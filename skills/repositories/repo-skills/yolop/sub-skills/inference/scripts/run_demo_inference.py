#!/usr/bin/env python3
"""Run YOLOP PyTorch demo inference with explicit paths and safer defaults.

Example:
  python run_demo_inference.py --repo-root /path/to/YOLOP \
    --weights /path/to/YOLOP/weights/End-to-end.pth \
    --source /path/to/YOLOP/test.jpg --save-dir /tmp/yolop-demo --device cpu
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="YOLOP PyTorch demo inference helper")
    parser.add_argument("--repo-root", required=True, help="Path to a YOLOP checkout")
    parser.add_argument("--weights", help="Path to a YOLOP checkpoint with a state_dict key")
    parser.add_argument("--source", required=True, help="Image file, folder, glob, or video path")
    parser.add_argument("--save-dir", required=True, help="Directory for output images/video")
    parser.add_argument("--img-size", type=int, default=640, help="Inference size in pixels")
    parser.add_argument("--conf-thres", type=float, default=0.25, help="Object confidence threshold")
    parser.add_argument("--iou-thres", type=float, default=0.45, help="NMS IoU threshold")
    parser.add_argument("--device", default="cpu", help="cpu, cuda, cuda:0, ...")
    parser.add_argument("--max-items", type=int, default=0, help="Maximum images/frames to process; 0 means all")
    parser.add_argument("--allow-video", action="store_true", help="Allow video inputs and write mp4 outputs")
    parser.add_argument("--allow-camera", action="store_true", help="Allow numeric camera source; not recommended for headless runs")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).expanduser().resolve()
    if not (repo_root / "lib" / "dataset" / "DemoDataset.py").is_file():
        print(f"ERROR: not a YOLOP checkout: {repo_root}", file=sys.stderr)
        return 2
    source_text = str(args.source)
    if source_text.isnumeric() and not args.allow_camera:
        print("ERROR: numeric camera sources are disabled by default; pass --allow-camera only on an interactive camera host", file=sys.stderr)
        return 3
    if args.img_size <= 0 or args.img_size % 32 != 0:
        print("ERROR: --img-size must be a positive multiple of 32", file=sys.stderr)
        return 4

    sys.path.insert(0, str(repo_root))

    import cv2
    import numpy as np
    import torch
    import torchvision.transforms as transforms
    from tqdm import tqdm

    from lib.config import cfg
    from lib.core.function import AverageMeter
    from lib.core.general import non_max_suppression, scale_coords
    from lib.dataset import LoadImages, LoadStreams
    from lib.models import get_net
    from lib.utils import plot_one_box, show_seg_result

    if args.device != "cpu" and args.device.startswith("cuda") and not torch.cuda.is_available():
        print("ERROR: CUDA requested but torch.cuda.is_available() is false", file=sys.stderr)
        return 5
    device = torch.device(args.device)
    weights = Path(args.weights).expanduser().resolve() if args.weights else repo_root / "weights" / "End-to-end.pth"
    if not weights.is_file():
        print(f"ERROR: checkpoint not found: {weights}", file=sys.stderr)
        return 6

    save_dir = Path(args.save_dir).expanduser().resolve()
    save_dir.mkdir(parents=True, exist_ok=True)

    model = get_net(cfg)
    checkpoint = torch.load(str(weights), map_location=device)
    state_dict = checkpoint.get("state_dict", checkpoint) if isinstance(checkpoint, dict) else checkpoint
    model.load_state_dict(state_dict)
    model = model.to(device).eval()
    half = device.type != "cpu"
    if half:
        model.half()

    if source_text.isnumeric():
        dataset = LoadStreams(source_text, img_size=args.img_size)
    else:
        dataset = LoadImages(source_text, img_size=args.img_size)

    normalize = transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    transform = transforms.Compose([transforms.ToTensor(), normalize])
    names = model.module.names if hasattr(model, "module") else model.names
    colors = [[int(x) for x in np.random.randint(0, 255, size=3)] for _ in range(len(names))]
    inf_time = AverageMeter()
    nms_time = AverageMeter()
    vid_path = None
    vid_writer = None
    processed = 0
    t0 = time.time()

    with torch.no_grad():
        dummy = torch.zeros((1, 3, args.img_size, args.img_size), device=device)
        _ = model(dummy.half() if half else dummy) if device.type != "cpu" else None
        for path, img, img_det, vid_cap, shapes in tqdm(dataset, total=len(dataset)):
            if getattr(dataset, "mode", "images") == "video" and not args.allow_video:
                print("ERROR: video input encountered; pass --allow-video to write mp4 output", file=sys.stderr)
                return 7
            tensor = transform(img).to(device)
            tensor = tensor.half() if half else tensor.float()
            if tensor.ndimension() == 3:
                tensor = tensor.unsqueeze(0)

            t1 = time.time()
            det_out, da_seg_out, ll_seg_out = model(tensor)
            t2 = time.time()
            inf_out, _ = det_out
            inf_time.update(t2 - t1, tensor.size(0))

            t3 = time.time()
            det_pred = non_max_suppression(inf_out, conf_thres=args.conf_thres, iou_thres=args.iou_thres, classes=None, agnostic=False)
            t4 = time.time()
            nms_time.update(t4 - t3, tensor.size(0))
            det = det_pred[0]

            _, _, height, width = tensor.shape
            pad_w, pad_h = shapes[1][1]
            pad_w, pad_h = int(pad_w), int(pad_h)
            ratio = shapes[1][0][1]
            da_predict = da_seg_out[:, :, pad_h:(height - pad_h), pad_w:(width - pad_w)]
            da_seg_mask = torch.nn.functional.interpolate(da_predict, scale_factor=int(1 / ratio), mode="bilinear")
            _, da_seg_mask = torch.max(da_seg_mask, 1)
            da_seg_mask = da_seg_mask.int().squeeze().cpu().numpy()

            ll_predict = ll_seg_out[:, :, pad_h:(height - pad_h), pad_w:(width - pad_w)]
            ll_seg_mask = torch.nn.functional.interpolate(ll_predict, scale_factor=int(1 / ratio), mode="bilinear")
            _, ll_seg_mask = torch.max(ll_seg_mask, 1)
            ll_seg_mask = ll_seg_mask.int().squeeze().cpu().numpy()

            img_out = show_seg_result(img_det, (da_seg_mask, ll_seg_mask), 0, 0, is_demo=True)
            if len(det):
                det[:, :4] = scale_coords(tensor.shape[2:], det[:, :4], img_out.shape).round()
                for *xyxy, conf, cls in reversed(det):
                    label = f"{names[int(cls)]} {float(conf):.2f}"
                    plot_one_box(xyxy, img_out, label=label, color=colors[int(cls)], line_thickness=2)

            if getattr(dataset, "mode", "images") == "video":
                out_path = str(save_dir / (Path(path).stem + ".mp4"))
                if vid_path != out_path:
                    vid_path = out_path
                    if isinstance(vid_writer, cv2.VideoWriter):
                        vid_writer.release()
                    fps = vid_cap.get(cv2.CAP_PROP_FPS) if vid_cap is not None else 30.0
                    h, w = img_out.shape[:2]
                    vid_writer = cv2.VideoWriter(out_path, cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))
                vid_writer.write(img_out)
            else:
                out_name = "web.jpg" if isinstance(path, list) else Path(str(path)).name
                cv2.imwrite(str(save_dir / out_name), img_out)

            processed += 1
            if args.max_items and processed >= args.max_items:
                break

    if isinstance(vid_writer, cv2.VideoWriter):
        vid_writer.release()
    print(f"processed={processed} save_dir={save_dir}")
    print(f"elapsed={time.time() - t0:.3f}s inf_avg={inf_time.avg:.4f}s nms_avg={nms_time.avg:.4f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
