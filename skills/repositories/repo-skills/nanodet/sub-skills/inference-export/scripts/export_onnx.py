#!/usr/bin/env python3
"""Export a NanoDet checkpoint to ONNX and simplify it when possible."""

from __future__ import annotations

import argparse
import os

import onnx
import onnxsim
import torch

from nanodet.model.arch import build_model
from nanodet.util import Logger, cfg, load_config, load_model_weight


def generate_output_names(head_cfg):
    cls_names, dis_names = [], []
    for stride in head_cfg.strides:
        cls_names.append(f"cls_pred_stride_{stride}")
        dis_names.append(f"dis_pred_stride_{stride}")
    return cls_names + dis_names


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description="Convert a NanoDet checkpoint to ONNX.",
    )
    parser.add_argument("--cfg_path", type=str, required=True, help="Path to a YAML config file.")
    parser.add_argument("--model_path", type=str, default=None, help="Path to a .ckpt model.")
    parser.add_argument("--out_path", type=str, default="nanodet.onnx", help="ONNX output path.")
    parser.add_argument("--input_shape", type=str, default=None, help="Model input shape as width,height.")
    return parser.parse_args()


def main(config, model_path, output_path, input_shape=(320, 320)):
    logger = Logger(-1, config.save_dir, False)
    model = build_model(config.model)
    checkpoint = torch.load(model_path, map_location=lambda storage, loc: storage)
    load_model_weight(model, checkpoint, logger)
    if config.model.arch.backbone.name == "RepVGG":
        deploy_config = config.model
        deploy_config.arch.backbone.update({"deploy": True})
        deploy_model = build_model(deploy_config)
        from nanodet.model.backbone.repvgg import repvgg_det_model_convert

        model = repvgg_det_model_convert(model, deploy_model)
    dummy_input = torch.autograd.Variable(torch.randn(1, 3, input_shape[0], input_shape[1]))

    torch.onnx.export(
        model,
        dummy_input,
        output_path,
        verbose=True,
        keep_initializers_as_inputs=True,
        opset_version=11,
        input_names=["data"],
        output_names=["output"],
    )
    logger.log("finished exporting onnx")

    logger.log("start simplifying onnx")
    input_data = {"data": dummy_input.detach().cpu().numpy()}
    model_sim, flag = onnxsim.simplify(output_path, input_data=input_data)
    if flag:
        onnx.save(model_sim, output_path)
        logger.log("simplify onnx successfully")
    else:
        logger.log("simplify onnx failed")


def entrypoint() -> None:
    args = parse_args()
    load_config(cfg, args.cfg_path)
    if args.input_shape is None:
        input_shape = cfg.data.train.input_size
    else:
        input_shape = tuple(map(int, args.input_shape.split(",")))
        assert len(input_shape) == 2
    if args.model_path is None:
        args.model_path = os.path.join(cfg.save_dir, "model_best/model_best.ckpt")
    main(cfg, args.model_path, args.out_path, input_shape)
    print("Model saved to:", args.out_path)


if __name__ == "__main__":
    entrypoint()
