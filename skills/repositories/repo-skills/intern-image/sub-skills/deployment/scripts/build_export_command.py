#!/usr/bin/env python3
"""Print safe InternImage export/deployment command templates.

This helper performs no imports from InternImage, PyTorch, OpenMMLab,
mmdeploy, CUDA, or TensorRT. It never builds, downloads, or runs export; it
only prints prerequisite-aware shell templates.
"""

from __future__ import annotations

import argparse
import shlex
import sys
from typing import Iterable, List, Optional

MODES = (
    "classification-onnx",
    "classification-trt",
    "detection-trt",
    "segmentation-trt",
)

DEFAULTS = {
    "classification-onnx": {
        "task_dir": "classification",
        "model_name": "internimage_t_1k_224",
        "ckpt_dir": "<checkpoint-dir>",
    },
    "classification-trt": {
        "task_dir": "classification",
        "model_name": "internimage_t_1k_224",
        "ckpt_dir": "<checkpoint-dir>",
    },
    "detection-trt": {
        "task_dir": "detection",
        "model_name": "mask_rcnn_internimage_t_fpn_1x_coco",
        "deploy_cfg": "./deploy/configs/mmdet/instance-seg/instance-seg_tensorrt_dynamic-320x320-1344x1344.py",
        "model_cfg_template": "./configs/coco/{model_name}.py",
        "checkpoint": "<checkpoint.pth>",
        "image": "./deploy/demo.jpg",
        "work_dir_template": "./work_dirs/mmdet/instance-seg/{model_name}",
    },
    "segmentation-trt": {
        "task_dir": "segmentation",
        "model_name": "upernet_internimage_t_512_160k_ade20k",
        "deploy_cfg": "./deploy/configs/mmseg/segmentation_tensorrt_static-512x512.py",
        "model_cfg_template": "./configs/ade20k/{model_name}.py",
        "checkpoint": "<checkpoint.pth>",
        "image": "./deploy/demo.png",
        "work_dir_template": "./work_dirs/mmseg/{model_name}",
    },
}


def shell_quote(value: str) -> str:
    """Quote concrete shell values while preserving readable placeholders."""
    text = str(value)
    if "<" in text and ">" in text:
        return text
    if text.startswith("${") or text.startswith("$"):
        return f'"{text}"'
    return shlex.quote(text)


def join_path(root: str, *parts: str) -> str:
    root = root.rstrip("/")
    suffix = "/".join(part.strip("/") for part in parts if part)
    if not root:
        return suffix
    return f"{root}/{suffix}" if suffix else root


def emit(title: str, lines: Iterable[str]) -> List[str]:
    out = [title]
    out.extend(lines)
    return out


def numbered(items: Iterable[str]) -> List[str]:
    return [f"  {idx}. {item}" for idx, item in enumerate(items, 1)]


def bullet(items: Iterable[str]) -> List[str]:
    return [f"  - {item}" for item in items]


def linewrap_command(argv: List[str]) -> List[str]:
    if not argv:
        return []
    quoted = [shell_quote(part) for part in argv]
    if len(" ".join(quoted)) <= 96:
        return [" ".join(quoted)]
    lines = [quoted[0] + " \\"]
    for idx, part in enumerate(quoted[1:], 1):
        tail = " \\" if idx < len(quoted) - 1 else ""
        lines.append(f"  {part}{tail}")
    return lines


def safe_probe_lines() -> List[str]:
    return [
        "python -V",
        "python -c \"import torch; print('torch', torch.__version__, 'cuda_available', torch.cuda.is_available(), 'torch_cuda', torch.version.cuda)\"",
        "python -c \"from torch.utils.cpp_extension import CUDA_HOME; print('CUDA_HOME', CUDA_HOME)\"",
        "nvcc -V",
        "python -c \"import importlib.util as u; print('DCNv3', u.find_spec('DCNv3')); print('mmdeploy', u.find_spec('mmdeploy'))\"",
    ]


def mmdeploy_build_block(args: argparse.Namespace) -> List[str]:
    repo = args.repo_root
    mmdeploy_dir = args.mmdeploy_dir
    tensorrt_dir = args.tensorrt_dir
    cudnn_dir = args.cudnn_dir
    cxx = args.cxx_compiler
    return [
        "# Required only when mmdeploy has not already been built with InternImage's TensorRT DCNv3 op.",
        f"export INTERNIMAGE_REPO={shell_quote(repo)}",
        f"export MMDEPLOY_DIR={shell_quote(mmdeploy_dir)}",
        f"export TENSORRT_DIR={shell_quote(tensorrt_dir)}",
        f"export CUDNN_DIR={shell_quote(cudnn_dir)}",
        "mkdir -p \"${MMDEPLOY_DIR}/csrc/mmdeploy/backend_ops/tensorrt\"",
        "cp -r \"${INTERNIMAGE_REPO}/tensorrt/modulated_deform_conv_v3\" \\",
        "  \"${MMDEPLOY_DIR}/csrc/mmdeploy/backend_ops/tensorrt/\"",
        "cd \"${MMDEPLOY_DIR}\"",
        "mkdir -p build && cd build",
        f"cmake -DCMAKE_CXX_COMPILER={shell_quote(cxx)} \\",
        "  -DMMDEPLOY_TARGET_BACKENDS=trt \\",
        "  -DTENSORRT_DIR=\"${TENSORRT_DIR}\" \\",
        "  -DCUDNN_DIR=\"${CUDNN_DIR}\" \\",
        "  ..",
        "make -j\"$(nproc)\"",
        "make install",
        "cd \"${MMDEPLOY_DIR}\"",
        "python -m pip install -e .",
    ]


def common_prerequisites(mode: str) -> List[str]:
    reqs = [
        "CUDA runtime/driver and CUDA toolkit/nvcc are separate; DCNv3 source builds need both a CUDA-enabled PyTorch wheel and CUDA_HOME/nvcc.",
        "Use NumPy < 2.0 and the repo-era OpenMMLab pins unless you have already validated a newer stack.",
        "Command templates are dry-run plans; do not execute build/export commands without explicit resource approval.",
    ]
    if mode.endswith("trt"):
        reqs.extend([
            "TensorRT export needs mmdeploy with TensorRT backend support, TensorRT/CUDNN installation roots, and the InternImage mmdeploy::TRTDCNv3 custom op built into mmdeploy.",
            "The DCNv3 Python extension alone is not enough for TensorRT; ONNX export emits a custom mmdeploy op that TensorRT must parse through the plugin.",
        ])
    return reqs


def mode_prerequisites(mode: str) -> List[str]:
    if mode.startswith("classification"):
        return [
            "Classification environment imports torch, timm, yacs/config code, model code, and the selected checkpoint.",
            "The upstream export path calls CUDA tensors for ONNX export, so CPU-only environments can print templates but should not be treated as export-verified.",
            "Model name must map to a classification YAML config and checkpoint named <model_name>.pth under the checkpoint directory.",
        ]
    if mode == "detection-trt":
        return [
            "Detection deployment imports mmcv_custom and mmdet_custom before mmdeploy conversion.",
            "Default template uses the MMDetection instance-seg dynamic TensorRT deploy config and a COCO model config path.",
            "Use --device cuda for TensorRT conversion after CUDA readiness is confirmed.",
        ]
    if mode == "segmentation-trt":
        return [
            "Segmentation deployment imports mmcv_custom and mmseg_custom before mmdeploy conversion.",
            "Default template uses the MMSegmentation static 512x512 TensorRT deploy config and an ADE20K model config path.",
            "Use --device cuda for TensorRT conversion after CUDA readiness is confirmed.",
        ]
    raise ValueError(f"unsupported mode: {mode}")


def classification_command(args: argparse.Namespace) -> List[str]:
    defaults = DEFAULTS[args.mode]
    model_name = args.model_name or defaults["model_name"]
    ckpt_dir = args.ckpt_dir or defaults["ckpt_dir"]
    task_dir = join_path(args.repo_root, defaults["task_dir"])
    flag = "--onnx" if args.mode == "classification-onnx" else "--trt"
    cmd = [
        "python",
        "export.py",
        "--model_name",
        model_name,
        "--ckpt_dir",
        ckpt_dir,
        flag,
    ]
    lines = [f"cd {shell_quote(task_dir)}"]
    lines.extend(linewrap_command(cmd))
    return lines


def deploy_command(args: argparse.Namespace) -> List[str]:
    defaults = DEFAULTS[args.mode]
    model_name = args.model_name or defaults["model_name"]
    deploy_cfg = args.deploy_cfg or defaults["deploy_cfg"]
    model_cfg = args.model_cfg or defaults["model_cfg_template"].format(model_name=model_name)
    checkpoint = args.checkpoint or defaults["checkpoint"]
    image = args.image or defaults["image"]
    work_dir = args.work_dir or defaults["work_dir_template"].format(model_name=model_name)
    task_dir = join_path(args.repo_root, defaults["task_dir"])
    cmd = [
        "python",
        "deploy.py",
        deploy_cfg,
        model_cfg,
        checkpoint,
        image,
        "--work-dir",
        work_dir,
        "--device",
        args.device,
    ]
    if args.test_img:
        cmd.append("--test-img")
        cmd.extend(args.test_img)
    if args.calib_dataset_cfg:
        cmd.extend(["--calib-dataset-cfg", args.calib_dataset_cfg])
    if args.quant_image_dir:
        cmd.extend(["--quant-image-dir", args.quant_image_dir])
    if args.quant:
        cmd.append("--quant")
    if args.show:
        cmd.append("--show")
    if args.dump_info:
        cmd.append("--dump-info")
    lines = [f"cd {shell_quote(task_dir)}"]
    lines.extend(linewrap_command(cmd))
    return lines


def build_output(args: argparse.Namespace) -> str:
    lines: List[str] = []
    lines.append("InternImage deployment/export command template")
    lines.append(f"Mode: {args.mode}")
    lines.append("")
    lines.extend(emit("Prerequisites to confirm:", bullet(common_prerequisites(args.mode) + mode_prerequisites(args.mode))))
    lines.append("")
    if args.include_probes:
        lines.append("Safe probes to run before real execution:")
        lines.extend(f"  {line}" for line in safe_probe_lines())
        lines.append("")
    if args.include_mmdeploy_build and args.mode.endswith("trt"):
        lines.append("Optional mmdeploy custom-op build template:")
        lines.extend(f"  {line}" for line in mmdeploy_build_block(args))
        lines.append("")
    elif args.mode.endswith("trt"):
        lines.append("Custom-op note:")
        lines.extend(numbered([
            "If mmdeploy was not built with InternImage's TensorRT backend op, rerun this helper with --include-mmdeploy-build to print the required build template.",
            "The required op source directory in a checkout is tensorrt/modulated_deform_conv_v3, and the plugin registered for TensorRT is TRTDCNv3.",
        ]))
        lines.append("")
    lines.append("Export command template:")
    if args.mode.startswith("classification"):
        command = classification_command(args)
    else:
        command = deploy_command(args)
    lines.extend(f"  {line}" for line in command)
    lines.append("")
    lines.append("Execution guardrails:")
    lines.extend(bullet([
        "Replace all angle-bracket placeholders before execution.",
        "Run from the printed task directory so the task-local custom imports and config paths resolve.",
        "Confirm checkpoint/config/model-name compatibility before launching export.",
        "Stop rather than retrying blindly if a compiler, TensorRT, mmdeploy backend, or DCNv3 custom-op error appears.",
    ]))
    return "\n".join(lines) + "\n"


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Print safe InternImage ONNX/TensorRT export command templates.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("mode", choices=MODES, help="template type to print")
    parser.add_argument("--repo-root", default="<INTERNIMAGE_REPO>", help="InternImage checkout path placeholder or concrete path")
    parser.add_argument("--model-name", default=None, help="workflow model/config name; mode-specific default is used when omitted")
    parser.add_argument("--ckpt-dir", default=None, help="classification checkpoint directory containing <model_name>.pth")
    parser.add_argument("--checkpoint", default=None, help="detection/segmentation checkpoint path")
    parser.add_argument("--deploy-cfg", default=None, help="detection/segmentation mmdeploy config path")
    parser.add_argument("--model-cfg", default=None, help="detection/segmentation model config path")
    parser.add_argument("--image", default=None, help="sample image used by mmdeploy conversion")
    parser.add_argument("--test-img", action="append", help="optional test image for backend visualization; repeat for multiple images")
    parser.add_argument("--work-dir", default=None, help="directory for exported files/logs")
    parser.add_argument("--device", default="cuda", help="device for mmdeploy conversion templates")
    parser.add_argument("--calib-dataset-cfg", default=None, help="optional calibration dataset config for int8 flows")
    parser.add_argument("--quant-image-dir", default=None, help="optional image directory for quantization")
    parser.add_argument("--quant", action="store_true", help="include mmdeploy low-bit quantization flag")
    parser.add_argument("--show", action="store_true", help="include visualization display flag")
    parser.add_argument("--dump-info", dest="dump_info", action="store_true", default=True, help="include SDK info dump flag")
    parser.add_argument("--no-dump-info", dest="dump_info", action="store_false", help="omit SDK info dump flag")
    parser.add_argument("--include-mmdeploy-build", action="store_true", help="print the mmdeploy TensorRT custom-op build template for TensorRT modes")
    parser.add_argument("--mmdeploy-dir", default="<MMDEPLOY_DIR>", help="mmdeploy source tree placeholder for custom-op build template")
    parser.add_argument("--tensorrt-dir", default="<TENSORRT_DIR>", help="TensorRT installation root placeholder")
    parser.add_argument("--cudnn-dir", default="<CUDNN_DIR>", help="CUDNN installation root placeholder")
    parser.add_argument("--cxx-compiler", default="g++", help="C++ compiler name/path for mmdeploy CMake template")
    parser.add_argument("--no-probes", dest="include_probes", action="store_false", help="omit safe prerequisite probe commands")
    parser.set_defaults(include_probes=True)
    args = parser.parse_args(argv)
    if args.include_mmdeploy_build and not args.mode.endswith("trt"):
        parser.error("--include-mmdeploy-build only applies to TensorRT modes")
    return args


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    sys.stdout.write(build_output(args))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
