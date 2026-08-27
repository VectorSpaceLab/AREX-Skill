#!/usr/bin/env python3
"""Self-contained DAMO-YOLO ONNX export helper for generated skills.

This adapts the repository converter path for ONNX export only. It imports the
installed `damo` package and does not call repo-local converter scripts.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

import torch
from loguru import logger
from torch import nn

from damo.base_models.core.end2end import End2End
from damo.base_models.core.ops import RepConv, SiLU
from damo.config.base import parse_config
from damo.detectors.detector import build_local_model
from damo.utils.model_utils import get_model_info, replace_module


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        "DAMO-YOLO safe ONNX export",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("-f", "--config-file", required=True, help="DAMO-YOLO Python config file")
    parser.add_argument("-c", "--ckpt", required=True, help="PyTorch checkpoint file")
    parser.add_argument("--workdir", help="Directory used to resolve relative paths inside the config")
    parser.add_argument("--output", required=True, help="Output ONNX path")
    parser.add_argument("--benchmark", action="store_true", help="Export without postprocess for latency benchmarking")
    parser.add_argument("--batch-size", type=int, default=1, help="Batch dimension for dummy input and exported graph")
    parser.add_argument("--img-size", type=int, default=640, help="Square input size for dummy input")
    parser.add_argument("--input", default="images", help="ONNX input node name")
    parser.add_argument("--raw-output", default="output", help="Output node name for non-end2end export")
    parser.add_argument("--opset", type=int, default=11, help="ONNX opset")
    parser.add_argument("--end2end", action="store_true", help="Export with NMS wrapper outputs")
    parser.add_argument("--ort", action="store_true", help="Use ONNX Runtime NMS symbolic when --end2end is set")
    parser.add_argument("--trt-version", type=int, default=8, help="TRT NMS symbolic version when --end2end and not --ort")
    parser.add_argument("--with-preprocess", action="store_true", help="Include BGR->RGB and /255 preprocessing in end2end graph")
    parser.add_argument("--topk-all", type=int, default=100, help="Maximum detections for NMS wrapper")
    parser.add_argument("--iou-thres", type=float, default=0.65, help="NMS IoU threshold for end2end export")
    parser.add_argument("--conf-thres", type=float, default=0.05, help="NMS confidence threshold for end2end export")
    parser.add_argument("--device", default="cuda", help="cuda device id (0,1,...) or cpu")
    parser.add_argument("--no-simplify", action="store_true", help="Do not run onnxsim even if available")
    parser.add_argument(
        "opts",
        help="Top-level config overrides accepted by Config.merge(); prefer config-file edits for nested keys",
        nargs=argparse.REMAINDER,
    )
    return parser


def choose_device(text: str) -> torch.device:
    if text == "cpu" or not torch.cuda.is_available():
        return torch.device("cpu")
    if text == "cuda":
        return torch.device("cuda")
    if text.startswith("cuda:"):
        return torch.device(text)
    return torch.device(f"cuda:{text}")


def prepare_workdir(workdir: str | None) -> None:
    if not workdir:
        return
    path = Path(workdir).resolve()
    if not path.is_dir():
        raise SystemExit(f"ERROR: --workdir does not exist or is not a directory: {path}")
    os.chdir(path)


def main() -> int:
    args = make_parser().parse_args()
    prepare_workdir(args.workdir)

    try:
        import onnx
    except Exception as exc:  # pragma: no cover - user-facing diagnostic
        raise SystemExit(f"ERROR: ONNX export requires the 'onnx' package: {exc}")

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if args.batch_size < 1:
        raise SystemExit("ERROR: --batch-size must be >= 1")
    if args.img_size <= 0:
        raise SystemExit("ERROR: --img-size must be positive")

    device = choose_device(args.device)
    if args.device != "cpu" and device.type == "cpu":
        print("WARNING: CUDA was requested but torch.cuda.is_available() is false; exporting on CPU.")

    config = parse_config(args.config_file)
    config.merge(args.opts)
    if args.benchmark:
        config.model.head.export_with_post = False
    config.test.batch_size = args.batch_size

    model = build_local_model(config, device)
    ckpt = torch.load(args.ckpt, map_location=device)
    state_dict = ckpt.get("model", ckpt)
    model.eval()
    model.load_state_dict(state_dict, strict=True)
    logger.info("loaded checkpoint from {}", args.ckpt)

    model = replace_module(model, nn.SiLU, SiLU)
    for layer in model.modules():
        if isinstance(layer, RepConv):
            layer.switch_to_deploy()
    logger.info("{}", get_model_info(model, (args.img_size, args.img_size)))

    model.head.nms = False
    export_model = model
    output_names = [args.raw_output]
    if args.end2end:
        export_model = End2End(
            model,
            max_obj=args.topk_all,
            iou_thres=args.iou_thres,
            score_thres=args.conf_thres,
            device=device,
            ort=args.ort,
            trt_version=args.trt_version,
            with_preprocess=args.with_preprocess,
        )
        output_names = ["num_dets", "det_boxes", "det_scores", "det_classes"]

    dummy_input = torch.randn(args.batch_size, 3, args.img_size, args.img_size, device=device)
    with torch.no_grad():
        _ = export_model(dummy_input)
    torch.onnx.export(
        export_model,
        dummy_input,
        str(output_path),
        input_names=[args.input],
        output_names=output_names,
        opset_version=args.opset,
        dynamo=False,
    )

    onnx_model = onnx.load(str(output_path))
    if args.end2end and not args.ort:
        shapes = [
            args.batch_size,
            1,
            args.batch_size,
            args.topk_all,
            4,
            args.batch_size,
            args.topk_all,
            args.batch_size,
            args.topk_all,
        ]
        for output in onnx_model.graph.output:
            for dim in output.type.tensor_type.shape.dim:
                if shapes:
                    dim.dim_param = str(shapes.pop(0))

    if not args.no_simplify:
        try:
            import onnxsim

            logger.info("Starting ONNX simplification")
            simplified, check = onnxsim.simplify(onnx_model)
            if check:
                onnx_model = simplified
            else:
                print("WARNING: onnxsim.simplify returned check=False; saving unsimplified graph")
        except Exception as exc:
            print(f"WARNING: ONNX simplification skipped: {exc}")

    onnx.save(onnx_model, str(output_path))
    print(f"ONNX export written to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
