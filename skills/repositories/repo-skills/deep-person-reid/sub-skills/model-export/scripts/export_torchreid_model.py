#!/usr/bin/env python3
"""Export a Torchreid checkpoint to ONNX, OpenVINO, or TFLite-style artifacts.

Safe defaults:
- ``--help`` and ``--dry-run`` stay side-effect free.
- ONNX export runs on CPU.
- OpenVINO and TFLite-style conversion are attempted only when their optional
  tools are installed.
"""

from __future__ import annotations

import argparse
import difflib
import importlib.util
import shlex
import shutil
import subprocess
import sys
from collections import OrderedDict
from pathlib import Path
from typing import Iterable, Sequence

SUPPORTED_MODEL_NAMES = (
    "resnet18",
    "resnet34",
    "resnet50",
    "resnet101",
    "resnet152",
    "resnext50_32x4d",
    "resnext101_32x8d",
    "resnet50_fc512",
    "resnet50mid",
    "resnet50_ibn_a",
    "resnet50_ibn_b",
    "se_resnet50",
    "se_resnet50_fc512",
    "se_resnet101",
    "se_resnext50_32x4d",
    "se_resnext101_32x4d",
    "densenet121",
    "densenet169",
    "densenet201",
    "densenet161",
    "densenet121_fc512",
    "inceptionresnetv2",
    "inceptionv4",
    "xception",
    "nasnsetmobile",
    "mobilenetv2_x1_0",
    "mobilenetv2_x1_4",
    "shufflenet",
    "shufflenet_v2_x0_5",
    "shufflenet_v2_x1_0",
    "shufflenet_v2_x1_5",
    "shufflenet_v2_x2_0",
    "squeezenet1_0",
    "squeezenet1_0_fc512",
    "squeezenet1_1",
    "mudeep",
    "hacnn",
    "pcb_p6",
    "pcb_p4",
    "mlfn",
    "osnet_x1_0",
    "osnet_x0_75",
    "osnet_x0_5",
    "osnet_x0_25",
    "osnet_ibn_x1_0",
    "osnet_ain_x1_0",
    "osnet_ain_x0_75",
    "osnet_ain_x0_5",
    "osnet_ain_x0_25",
)
SUPPORTED_INCLUDE_VALUES = ("onnx", "openvino", "tflite")
DEFAULT_IMGSZ = (256, 128)
CHECKPOINT_SUFFIXES = (".pth.tar", ".pt.tar", ".ckpt", ".pth", ".pt")


class ExportError(RuntimeError):
    """Raised when export cannot proceed."""


class DependencyMissingError(ExportError):
    """Raised when an optional backend package is missing."""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="export_torchreid_model.py",
        description=(
            "Export a Torchreid checkpoint to ONNX, OpenVINO, or TFLite-style "
            "artifacts."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python scripts/export_torchreid_model.py --weights model-best.pth.tar "
            "--model-name osnet_x0_25 --include onnx\n"
            "  python scripts/export_torchreid_model.py --weights model-best.pth.tar "
            "--model-name osnet_x0_25 --include openvino tflite --dry-run\n"
        ),
    )
    parser.add_argument(
        "--weights",
        type=Path,
        required=True,
        help="Path to a Torchreid checkpoint file.",
    )
    parser.add_argument(
        "--model-name",
        default=None,
        help=(
            "Core Torchreid model key. Required when the checkpoint filename "
            "cannot be inferred safely."
        ),
    )
    parser.add_argument(
        "--imgsz",
        "--img",
        "--img-size",
        nargs="+",
        type=int,
        default=list(DEFAULT_IMGSZ),
        metavar="SIZE",
        help=(
            "Input height and width for the export dummy tensor. One value makes "
            "a square input."
        ),
    )
    parser.add_argument(
        "--include",
        nargs="+",
        default=["onnx", "openvino", "tflite"],
        metavar="FORMAT",
        help=(
            "Requested export targets. Supported values are onnx, openvino, and "
            "tflite. Upstream stages are inserted automatically."
        ),
    )
    parser.add_argument(
        "--dynamic",
        action="store_true",
        help="Export ONNX with a dynamic batch axis.",
    )
    parser.add_argument(
        "--opset",
        type=int,
        default=12,
        help="ONNX opset version for the export stage.",
    )
    parser.add_argument(
        "--half-precision",
        "--half_precision",
        dest="half_precision",
        action="store_true",
        help=(
            "Request FP16 when the optional OpenVINO converter supports it. "
            "ONNX remains CPU-safe and float32."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help=(
            "Resolve the plan and print the commands without importing torchreid "
            "or writing files."
        ),
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing output artifacts if they already exist.",
    )
    return parser


def normalize_imgsz(values: Sequence[int]) -> tuple[int, int]:
    if not values:
        raise ExportError("--imgsz needs at least one integer")
    if len(values) == 1:
        size = int(values[0])
        if size <= 0:
            raise ExportError("--imgsz values must be positive")
        return size, size
    if len(values) == 2:
        h, w = int(values[0]), int(values[1])
        if h <= 0 or w <= 0:
            raise ExportError("--imgsz values must be positive")
        return h, w
    raise ExportError("--imgsz accepts either one value or two values")


def normalize_include(values: Sequence[str]) -> list[str]:
    tokens: list[str] = []
    for raw in values:
        for token in str(raw).split(","):
            token = token.strip().lower()
            if token:
                tokens.append(token)
    if not tokens:
        raise ExportError("--include must contain at least one export target")

    deduped: list[str] = []
    for token in tokens:
        if token not in SUPPORTED_INCLUDE_VALUES:
            valid = ", ".join(SUPPORTED_INCLUDE_VALUES)
            raise ExportError(
                f"Unsupported --include value '{token}'. Valid values: {valid}."
            )
        if token not in deduped:
            deduped.append(token)
    return deduped


def strip_checkpoint_suffix(path: Path) -> str:
    name = path.name
    lower = name.lower()
    for suffix in CHECKPOINT_SUFFIXES:
        if lower.endswith(suffix):
            return name[: -len(suffix)]
    return path.stem


def infer_model_name(weights: Path) -> str | None:
    base = strip_checkpoint_suffix(weights).lower()
    ranked = sorted(SUPPORTED_MODEL_NAMES, key=len, reverse=True)
    matches = [name for name in ranked if name in base]
    if not matches:
        return None
    best_len = len(matches[0])
    best = [name for name in matches if len(name) == best_len]
    if len(best) > 1:
        raise ExportError(
            f"Ambiguous model-name inference from '{weights.name}'. Pass --model-name explicitly."
        )
    return best[0]


def resolve_model_name(weights: Path, explicit: str | None) -> str:
    if explicit:
        model_name = explicit.strip().lower()
        if model_name not in SUPPORTED_MODEL_NAMES:
            suggestion = difflib.get_close_matches(model_name, SUPPORTED_MODEL_NAMES, n=3)
            extra = f" Did you mean: {', '.join(suggestion)}?" if suggestion else ""
            raise ExportError(
                f"Model '{model_name}' is not part of the core Torchreid build_model registry.{extra} "
                "Project-specific models are outside this bundled core Torchreid export helper."
            )
        return model_name

    inferred = infer_model_name(weights)
    if inferred is None:
        raise ExportError(
            f"Could not infer a safe model name from '{weights.name}'. Pass --model-name explicitly."
        )
    return inferred


def build_pipeline(requested_targets: Sequence[str]) -> list[str]:
    pipeline: list[str] = []
    if any(target in requested_targets for target in ("onnx", "openvino", "tflite")):
        pipeline.append("onnx")
    if any(target in requested_targets for target in ("openvino", "tflite")):
        pipeline.append("openvino")
    if "tflite" in requested_targets:
        pipeline.append("tflite")
    return pipeline


def ensure_repo_root_on_path() -> Path:
    try:
        import torchreid  # noqa: F401
        return Path(torchreid.__file__).resolve().parent.parent
    except ModuleNotFoundError:
        for parent in Path(__file__).resolve().parents:
            if (parent / "torchreid").is_dir():
                sys.path.insert(0, str(parent))
                return parent
        raise ModuleNotFoundError(
            "Could not import torchreid. Install the Torchreid package in the active Python environment before running this helper."
        )


def require_module_or_cli(module_name: str, cli_name: str, install_hint: str) -> list[str]:
    if shutil.which(cli_name):
        return [cli_name]
    if importlib.util.find_spec(module_name) is not None:
        return [sys.executable, "-m", module_name]
    raise DependencyMissingError(install_hint)


def ensure_not_exists(path: Path, force: bool) -> None:
    if not path.exists():
        return
    if not force:
        raise ExportError(
            f"Output path already exists: {path}. Re-run with --force to overwrite it."
        )
    if path.is_dir():
        shutil.rmtree(path)
    else:
        path.unlink()


def format_size(path: Path) -> float:
    if path.is_file():
        return path.stat().st_size / 1e6
    if path.is_dir():
        total = 0
        for child in path.rglob("*"):
            if child.is_file():
                total += child.stat().st_size
        return total / 1e6
    return 0.0


def print_dry_run(
    weights: Path,
    weights_exists: bool,
    model_name: str,
    imgsz: tuple[int, int],
    requested_targets: Sequence[str],
    pipeline: Sequence[str],
    artifact_base: str,
    dynamic: bool,
    opset: int,
    half_precision: bool,
) -> None:
    onnx_path = weights.with_name(f"{artifact_base}.onnx")
    openvino_dir = weights.with_name(f"{artifact_base}_openvino_model")
    tflite_dir = weights.with_name(f"{artifact_base}_tflite_model")
    print("Torchreid export dry-run")
    print(f"- weights: {weights}")
    print(f"- checkpoint exists: {'yes' if weights_exists else 'no'}")
    print(f"- model-name: {model_name}")
    print(f"- input-size: {imgsz[0]}x{imgsz[1]}")
    print(f"- requested targets: {', '.join(requested_targets)}")
    print(f"- execution pipeline: {' -> '.join(pipeline)}")
    print(f"- onnx output: {onnx_path}")
    print(f"- openvino output: {openvino_dir}")
    print(f"- tflite output: {tflite_dir}")
    print(f"- dynamic axes: {dynamic}")
    print(f"- opset: {opset}")
    print(f"- half precision: {half_precision}")
    print("- required backends:")
    print("  * onnx for the ONNX stage")
    if "openvino" in pipeline:
        print("  * openvino-dev or the Model Optimizer entry point")
    if "tflite" in pipeline:
        print("  * openvino2tensorflow, tensorflow, and related TensorFlow extras")
    if not weights_exists:
        print("- note: actual export will fail until the checkpoint file exists")
    print("No files will be written in dry-run mode.")


def load_checkpoint_into_model(model, weights: Path) -> tuple[list[str], list[str]]:
    import torch

    try:
        checkpoint = torch.load(weights, map_location="cpu")
    except Exception as exc:  # pragma: no cover - surfaced to caller
        raise ExportError(f"Failed to load checkpoint '{weights}': {exc}") from exc

    if isinstance(checkpoint, dict) and "state_dict" in checkpoint:
        state_dict = checkpoint["state_dict"]
    elif isinstance(checkpoint, dict):
        state_dict = checkpoint
    else:
        raise ExportError(
            f"Checkpoint '{weights}' is not a Torchreid-style dictionary checkpoint."
        )

    model_state = model.state_dict()
    new_state = OrderedDict()
    matched_layers: list[str] = []
    discarded_layers: list[str] = []

    for key, value in state_dict.items():
        clean_key = key[7:] if key.startswith("module.") else key
        if clean_key in model_state and model_state[clean_key].shape == value.shape:
            new_state[clean_key] = value
            matched_layers.append(clean_key)
        else:
            discarded_layers.append(clean_key)

    if not matched_layers:
        raise ExportError(
            f"No checkpoint parameters matched model '{model.__class__.__name__}'. "
            "Check the model name and checkpoint file."
        )

    model_state.update(new_state)
    model.load_state_dict(model_state)
    return matched_layers, discarded_layers


def export_onnx(
    model,
    dummy_input,
    onnx_path: Path,
    *,
    opset: int,
    dynamic: bool,
    force: bool,
) -> Path:
    import torch

    ensure_not_exists(onnx_path, force)

    try:
        import onnx
    except ModuleNotFoundError as exc:
        raise DependencyMissingError(
            "ONNX export requires the 'onnx' package. Install the export extra before retrying."
        ) from exc

    print(f"[onnx] exporting to {onnx_path}")
    torch.onnx.export(
        model.cpu(),
        dummy_input.cpu(),
        onnx_path,
        verbose=False,
        opset_version=opset,
        training=torch.onnx.TrainingMode.EVAL,
        do_constant_folding=True,
        input_names=["images"],
        output_names=["output"],
        dynamic_axes={
            "images": {0: "batch"},
            "output": {0: "batch"},
        }
        if dynamic
        else None,
    )

    model_onnx = onnx.load(onnx_path)
    onnx.checker.check_model(model_onnx)

    try:
        import onnxsim
    except ModuleNotFoundError:
        print("[onnx] simplifier not installed; keeping the raw graph")
    else:
        try:
            print(f"[onnx] simplifying with onnxsim {onnxsim.__version__}")
            simplified, ok = onnxsim.simplify(
                model_onnx,
                dynamic_input_shape=dynamic,
                input_shapes={"images": list(dummy_input.shape)} if dynamic else None,
            )
            if ok:
                onnx.save(simplified, onnx_path)
            else:
                print("[onnx] simplifier check failed; keeping the raw graph")
        except Exception as exc:
            print(f"[onnx] simplifier skipped: {exc}")

    print(f"[onnx] saved {onnx_path} ({format_size(onnx_path):.1f} MB)")
    return onnx_path


def export_openvino(
    onnx_path: Path,
    openvino_dir: Path,
    *,
    half_precision: bool,
    force: bool,
) -> Path:
    ensure_not_exists(openvino_dir, force)
    cmd = require_module_or_cli(
        "openvino.tools.mo",
        "mo",
        "OpenVINO conversion requires 'openvino-dev' or the Model Optimizer entry point.",
    )
    cmd.extend(
        [
            "--input_model",
            str(onnx_path),
            "--output_dir",
            str(openvino_dir),
            "--data_type",
            "FP16" if half_precision else "FP32",
        ]
    )
    print(f"[openvino] {' '.join(shlex.quote(part) for part in cmd)}")
    subprocess.run(cmd, check=True)
    print(f"[openvino] saved {openvino_dir} ({format_size(openvino_dir):.1f} MB)")
    return openvino_dir


def find_openvino_xml(openvino_dir: Path) -> Path:
    xml_files = sorted(openvino_dir.glob("*.xml"))
    if not xml_files:
        raise ExportError(
            f"No OpenVINO XML file was produced under {openvino_dir}."
        )
    return xml_files[0]


def export_tflite(
    openvino_dir: Path,
    tflite_dir: Path,
    *,
    force: bool,
) -> Path:
    ensure_not_exists(tflite_dir, force)
    xml_path = find_openvino_xml(openvino_dir)
    cmd = require_module_or_cli(
        "openvino2tensorflow",
        "openvino2tensorflow",
        "TFLite-style export requires 'openvino2tensorflow' plus TensorFlow support.",
    )
    cmd.extend(
        [
            "--model_path",
            str(xml_path),
            "--model_output_path",
            str(tflite_dir),
            "--output_pb",
            "--output_saved_model",
            "--output_no_quant_float32_tflite",
            "--output_dynamic_range_quant_tflite",
        ]
    )
    print(f"[tflite] {' '.join(shlex.quote(part) for part in cmd)}")
    subprocess.run(cmd, check=True)
    print(f"[tflite] saved {tflite_dir} ({format_size(tflite_dir):.1f} MB)")
    return tflite_dir


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    weights = args.weights.expanduser().resolve() if args.weights else None
    if weights is None:
        raise ExportError("--weights is required")

    imgsz = normalize_imgsz(args.imgsz)
    requested_targets = normalize_include(args.include)
    pipeline = build_pipeline(requested_targets)
    model_name = resolve_model_name(weights, args.model_name)
    artifact_base = strip_checkpoint_suffix(weights)

    if args.dry_run:
        print_dry_run(
            weights=weights,
            weights_exists=weights.is_file(),
            model_name=model_name,
            imgsz=imgsz,
            requested_targets=requested_targets,
            pipeline=pipeline,
            artifact_base=artifact_base,
            dynamic=args.dynamic,
            opset=args.opset,
            half_precision=args.half_precision,
        )
        return 0

    if not weights.is_file():
        raise ExportError(f"Checkpoint file does not exist: {weights}")

    if args.half_precision:
        print(
            "[note] ONNX stays float32 on CPU; half precision only affects the optional OpenVINO stage."
        )
    if args.dynamic and args.half_precision:
        print(
            "[note] dynamic ONNX export is kept in float32; FP16 is not applied to the CPU-safe ONNX stage."
        )

    ensure_repo_root_on_path()
    import torch
    from torchreid.models import build_model

    model = build_model(model_name, num_classes=1, pretrained=False, use_gpu=False)
    print(f"[model] using {model_name}")
    matched_layers, discarded_layers = load_checkpoint_into_model(model, weights)
    print(
        f"[weights] loaded {len(matched_layers)} matched layers from {weights.name}"
    )
    if discarded_layers:
        print(
            f"[weights] ignored {len(discarded_layers)} unmatched layers"
        )

    dummy = torch.zeros(1, 3, imgsz[0], imgsz[1], dtype=torch.float32)
    model.eval()

    onnx_path = weights.with_name(f"{artifact_base}.onnx")
    openvino_dir = weights.with_name(f"{artifact_base}_openvino_model")
    tflite_dir = weights.with_name(f"{artifact_base}_tflite_model")

    if "onnx" in pipeline:
        export_onnx(
            model,
            dummy,
            onnx_path,
            opset=args.opset,
            dynamic=args.dynamic,
            force=args.force,
        )

    if "openvino" in pipeline:
        export_openvino(
            onnx_path,
            openvino_dir,
            half_precision=args.half_precision,
            force=args.force,
        )

    if "tflite" in pipeline:
        export_tflite(
            openvino_dir,
            tflite_dir,
            force=args.force,
        )

    print("[done] export pipeline finished")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except DependencyMissingError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2)
    except ExportError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
