#!/usr/bin/env python3
"""Export Segment Anything's prompt encoder and mask decoder to ONNX.

This is a self-contained adaptation of Segment Anything's export helper. It keeps
argument parsing safe when optional ONNX dependencies are missing, and reports
clear dependency errors for export validation and quantization.
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
import warnings
from pathlib import Path
from typing import Any

VALID_MODEL_TYPES = ("default", "vit_h", "vit_l", "vit_b")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Export the SAM prompt encoder and mask decoder to an ONNX model."
    )
    parser.add_argument("--checkpoint", required=True, help="Path to the SAM model checkpoint.")
    parser.add_argument("--output", required=True, help="Path to write the ONNX model.")
    parser.add_argument(
        "--model-type",
        required=True,
        choices=VALID_MODEL_TYPES,
        help="SAM registry key matching the checkpoint.",
    )
    parser.add_argument(
        "--return-single-mask",
        action="store_true",
        help="Return only the selected best mask instead of multiple masks.",
    )
    parser.add_argument(
        "--opset",
        type=int,
        default=17,
        help="ONNX opset version to use; must be >= 11.",
    )
    parser.add_argument(
        "--quantize-out",
        default=None,
        help="Optional path for a dynamically quantized ONNX model. Requires onnxruntime.",
    )
    parser.add_argument(
        "--gelu-approximate",
        action="store_true",
        help="Use tanh-approximate GELU for runtimes with slow or unsupported erf.",
    )
    parser.add_argument(
        "--use-stability-score",
        action="store_true",
        help="Return stability scores instead of predicted IoU scores.",
    )
    parser.add_argument(
        "--return-extra-metrics",
        action="store_true",
        help="Return masks, scores, stability scores, areas, and low-res logits.",
    )
    parser.add_argument(
        "--skip-onnxruntime-check",
        action="store_true",
        help="Do not run the exported model with ONNXRuntime after export.",
    )
    return parser


def require_segment_anything() -> tuple[Any, Any]:
    try:
        from segment_anything import sam_model_registry
        from segment_anything.utils.onnx import SamOnnxModel
    except ImportError as exc:
        raise SystemExit(
            "Could not import segment_anything. Install the Segment Anything package "
            "in this Python environment before exporting."
        ) from exc
    return sam_model_registry, SamOnnxModel


def has_module(module_name: str) -> bool:
    return importlib.util.find_spec(module_name) is not None


def to_numpy(tensor):
    return tensor.detach().cpu().numpy()


def require_torch():
    try:
        import torch
    except ImportError as exc:
        raise SystemExit(
            "Could not import torch. Install PyTorch in this Python environment before exporting."
        ) from exc
    return torch


def run_export(args: argparse.Namespace) -> None:
    if args.opset < 11:
        raise SystemExit("--opset must be >= 11 for the SAM ONNX export path.")
    if args.quantize_out and not has_module("onnxruntime"):
        raise SystemExit("--quantize-out requires onnxruntime. Install onnxruntime and retry.")
    if not has_module("onnx"):
        print(
            "Warning: Python package 'onnx' was not detected. PyTorch export may fail "
            "unless ONNX support is otherwise available.",
            file=sys.stderr,
        )

    torch = require_torch()
    sam_model_registry, SamOnnxModel = require_segment_anything()

    print("Loading SAM model...")
    sam = sam_model_registry[args.model_type](checkpoint=args.checkpoint)
    onnx_model = SamOnnxModel(
        model=sam,
        return_single_mask=args.return_single_mask,
        use_stability_score=args.use_stability_score,
        return_extra_metrics=args.return_extra_metrics,
    )

    if args.gelu_approximate:
        for module in onnx_model.modules():
            if isinstance(module, torch.nn.GELU):
                module.approximate = "tanh"

    dynamic_axes = {
        "point_coords": {1: "num_points"},
        "point_labels": {1: "num_points"},
    }
    embed_dim = sam.prompt_encoder.embed_dim
    embed_size = sam.prompt_encoder.image_embedding_size
    mask_input_size = [4 * size for size in embed_size]
    dummy_inputs = {
        "image_embeddings": torch.randn(1, embed_dim, *embed_size, dtype=torch.float),
        "point_coords": torch.randint(low=0, high=1024, size=(1, 5, 2), dtype=torch.float),
        "point_labels": torch.randint(low=0, high=4, size=(1, 5), dtype=torch.float),
        "mask_input": torch.randn(1, 1, *mask_input_size, dtype=torch.float),
        "has_mask_input": torch.tensor([1], dtype=torch.float),
        "orig_im_size": torch.tensor([1500, 2250], dtype=torch.float),
    }
    _ = onnx_model(**dummy_inputs)

    output_names = ["masks", "iou_predictions", "low_res_masks"]
    if args.return_extra_metrics:
        output_names = ["masks", "iou_predictions", "stability_scores", "areas", "low_res_masks"]

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=torch.jit.TracerWarning)
        warnings.filterwarnings("ignore", category=UserWarning)
        with output_path.open("wb") as output_file:
            print(f"Exporting ONNX model to {output_path}...")
            torch.onnx.export(
                onnx_model,
                tuple(dummy_inputs.values()),
                output_file,
                export_params=True,
                verbose=False,
                opset_version=args.opset,
                do_constant_folding=True,
                input_names=list(dummy_inputs.keys()),
                output_names=output_names,
                dynamic_axes=dynamic_axes,
            )

    if not args.skip_onnxruntime_check:
        if has_module("onnxruntime"):
            import onnxruntime

            providers = ["CPUExecutionProvider"]
            session = onnxruntime.InferenceSession(str(output_path), providers=providers)
            ort_inputs = {name: to_numpy(tensor) for name, tensor in dummy_inputs.items()}
            _ = session.run(None, ort_inputs)
            print("Exported model successfully ran with ONNXRuntime.")
        else:
            print("Skipping ONNXRuntime validation because onnxruntime is not installed.")

    if args.quantize_out:
        from onnxruntime.quantization import QuantType
        from onnxruntime.quantization.quantize import quantize_dynamic

        quantized_path = Path(args.quantize_out)
        quantized_path.parent.mkdir(parents=True, exist_ok=True)
        print(f"Quantizing model and writing to {quantized_path}...")
        quantize_dynamic(
            model_input=str(output_path),
            model_output=str(quantized_path),
            optimize_model=True,
            per_channel=False,
            reduce_range=False,
            weight_type=QuantType.QUInt8,
        )
        print("Done.")


def main() -> None:
    args = build_parser().parse_args()
    run_export(args)


if __name__ == "__main__":
    main()
