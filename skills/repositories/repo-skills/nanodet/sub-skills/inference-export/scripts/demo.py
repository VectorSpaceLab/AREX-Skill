#!/usr/bin/env python3
"""Run NanoDet image, video, or webcam inference.

This wrapper keeps the original demo behavior but makes the device explicit.
"""

from __future__ import annotations

import argparse
import os
import time

import cv2
import torch

from nanodet.data.batch_process import stack_batch_img
from nanodet.data.collate import naive_collate
from nanodet.data.transform import Pipeline
from nanodet.model.arch import build_model
from nanodet.util import Logger, cfg, load_config, load_model_weight
from nanodet.util.path import mkdir

IMAGE_EXT = [".jpg", ".jpeg", ".webp", ".bmp", ".png"]

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run NanoDet demo inference.")
    parser.add_argument("demo", choices=("image", "video", "webcam"), help="Demo type.")
    parser.add_argument("--config", required=True, help="Model config file path.")
    parser.add_argument("--model", required=True, help="Checkpoint file path.")
    parser.add_argument("--path", default="./demo", help="Path to images or video.")
    parser.add_argument("--camid", type=int, default=0, help="Webcam / camera index.")
    parser.add_argument(
        "--save_result",
        action="store_true",
        help="Write inference results to the configured save_dir.",
    )
    parser.add_argument(
        "--show",
        action="store_true",
        help="Display an OpenCV window while visualizing detections.",
    )
    parser.add_argument(
        "--device",
        default="auto",
        help='Device to use: "auto", "cpu", or a CUDA device like "cuda:0".',
    )
    parser.add_argument(
        "--score_thres",
        type=float,
        default=0.35,
        help="Visualization score threshold.",
    )
    return parser.parse_args()


def resolve_device(device_arg: str) -> str:
    if device_arg == "auto":
        return "cuda:0" if torch.cuda.is_available() else "cpu"
    if device_arg.startswith("cuda") and not torch.cuda.is_available():
        raise RuntimeError("CUDA was requested, but torch.cuda.is_available() is False.")
    return device_arg


class Predictor:
    def __init__(self, cfg, model_path, logger, device="cuda:0"):
        self.cfg = cfg
        self.device = device
        model = build_model(cfg.model)
        ckpt = torch.load(model_path, map_location=lambda storage, loc: storage)
        load_model_weight(model, ckpt, logger)
        if cfg.model.arch.backbone.name == "RepVGG":
            deploy_config = cfg.model
            deploy_config.arch.backbone.update({"deploy": True})
            deploy_model = build_model(deploy_config)
            from nanodet.model.backbone.repvgg import repvgg_det_model_convert

            model = repvgg_det_model_convert(model, deploy_model)
        self.model = model.to(device).eval()
        self.pipeline = Pipeline(cfg.data.val.pipeline, cfg.data.val.keep_ratio)

    def inference(self, img):
        img_info = {"id": 0}
        if isinstance(img, str):
            img_info["file_name"] = os.path.basename(img)
            img = cv2.imread(img)
        else:
            img_info["file_name"] = None

        height, width = img.shape[:2]
        img_info["height"] = height
        img_info["width"] = width
        meta = dict(img_info=img_info, raw_img=img, img=img)
        meta = self.pipeline(None, meta, self.cfg.data.val.input_size)
        meta["img"] = torch.from_numpy(meta["img"].transpose(2, 0, 1)).to(self.device)
        meta = naive_collate([meta])
        meta["img"] = stack_batch_img(meta["img"], divisible=32)
        with torch.no_grad():
            results = self.model.inference(meta)
        return meta, results

    def visualize(self, dets, meta, class_names, score_thres, show=False):
        time1 = time.time()
        result_img = self.model.head.show_result(
            meta["raw_img"][0], dets, class_names, score_thres=score_thres, show=show
        )
        print(f"viz time: {time.time() - time1:.3f}s")
        return result_img


def get_image_list(path):
    image_names = []
    for maindir, _subdir, file_name_list in os.walk(path):
        for filename in file_name_list:
            apath = os.path.join(maindir, filename)
            ext = os.path.splitext(apath)[1]
            if ext in IMAGE_EXT:
                image_names.append(apath)
    return image_names


def main() -> None:
    args = parse_args()
    device = resolve_device(args.device)

    local_rank = 0
    torch.backends.cudnn.enabled = True
    torch.backends.cudnn.benchmark = True

    load_config(cfg, args.config)
    logger = Logger(local_rank, cfg.save_dir, use_tensorboard=False)
    predictor = Predictor(cfg, args.model, logger, device=device)
    logger.log('Press "Esc", "q" or "Q" to exit.')
    current_time = time.localtime()

    if args.demo == "image":
        if os.path.isdir(args.path):
            files = get_image_list(args.path)
        else:
            files = [args.path]
        files.sort()
        for image_name in files:
            meta, res = predictor.inference(image_name)
            result_image = predictor.visualize(
                res[0], meta, cfg.class_names, args.score_thres, show=args.show
            )
            if args.save_result:
                save_folder = os.path.join(
                    cfg.save_dir, time.strftime("%Y_%m_%d_%H_%M_%S", current_time)
                )
                mkdir(local_rank, save_folder)
                save_file_name = os.path.join(save_folder, os.path.basename(image_name))
                cv2.imwrite(save_file_name, result_image)
            if args.show:
                ch = cv2.waitKey(0)
                if ch == 27 or ch == ord("q") or ch == ord("Q"):
                    break
    elif args.demo in ("video", "webcam"):
        source = args.path if args.demo == "video" else args.camid
        cap = cv2.VideoCapture(source)
        width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        fps = cap.get(cv2.CAP_PROP_FPS)
        save_folder = os.path.join(
            cfg.save_dir, time.strftime("%Y_%m_%d_%H_%M_%S", current_time)
        )
        mkdir(local_rank, save_folder)
        save_path = (
            os.path.join(save_folder, args.path.replace("\\", "/").split("/")[-1])
            if args.demo == "video"
            else os.path.join(save_folder, "camera.mp4")
        )
        print(f"save_path is {save_path}")
        vid_writer = None
        if args.save_result:
            vid_writer = cv2.VideoWriter(
                save_path, cv2.VideoWriter_fourcc(*"mp4v"), fps, (int(width), int(height))
            )
        while True:
            ret_val, frame = cap.read()
            if not ret_val:
                break
            meta, res = predictor.inference(frame)
            result_frame = predictor.visualize(
                res[0], meta, cfg.class_names, args.score_thres, show=args.show
            )
            if vid_writer is not None:
                vid_writer.write(result_frame)
            if args.show:
                ch = cv2.waitKey(1)
                if ch == 27 or ch == ord("q") or ch == ord("Q"):
                    break


if __name__ == "__main__":
    main()
