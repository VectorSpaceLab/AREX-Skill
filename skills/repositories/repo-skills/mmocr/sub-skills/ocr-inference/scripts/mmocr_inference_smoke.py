#!/usr/bin/env python3
"""Safe MMOCR inference preflight and opt-in runner.

The default action is validation only. It imports MMOCR inferencers, prints
versions, validates model/config/checkpoint/input/output/device choices, and
exits without constructing models or downloading weights. Add --execute to run
inference; model-zoo downloads are still blocked unless --allow-download is set.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple
from urllib.parse import urlparse

KNOWN_MODELS: Dict[str, Set[str]] = {
    "det": {
        "DBNet",
        "DB_r18",
        "DBNetpp",
        "dbnetpp",
        "dbnet_resnet18_fpnc_1200e_icdar2015",
        "dbnet_resnet50_fpnc_1200e_icdar2015",
        "dbnetpp_resnet50_fpnc_1200e_icdar2015",
        "FCENet",
        "PSENet",
        "TextSnake",
        "DRRG",
        "PANet_CTW",
        "PANet_IC15",
        "MaskRCNN",
    },
    "rec": {
        "CRNN",
        "crnn_mini-vgg_5e_mj",
        "SAR",
        "sar_resnet31_parallel-decoder_5e_st-sub_mj-sub_sa_real",
        "svtr-small",
        "svtr-base",
        "svtr-small_20e_st_mj",
        "svtr-base_20e_st_mj",
        "SATRN",
        "SATRN_sm",
        "ABINet",
        "ABINet_Vision",
        "ASTER",
        "MASTER",
        "RobustScanner",
        "NRTR_1/16-1/8",
    },
    "kie": {
        "SDMGR",
        "sdmgr_unet16_60e_wildreceipt",
        "sdmgr_novisual_60e_wildreceipt",
        "sdmgr_novisual_60e_wildreceipt_openset",
    },
    "spot": set(),
}

KIND_LABELS = {
    "det": "text detection",
    "rec": "text recognition",
    "kie": "key information extraction",
    "spot": "text spotting",
}


def is_url(value: Optional[str]) -> bool:
    if not value:
        return False
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https", "s3", "gs"}


def looks_like_path(value: Optional[str]) -> bool:
    if not value or is_url(value):
        return False
    return (
        value.endswith((".py", ".pth", ".pt", ".ckpt", ".onnx"))
        or "/" in value
        or "\\" in value
        or value.startswith(".")
        or value.startswith("~")
    )


def path_exists(value: str) -> bool:
    return Path(value).expanduser().exists()


def import_runtime() -> Tuple[Dict[str, str], Dict[str, Any], Optional[Any]]:
    try:
        import mmcv  # type: ignore
        import mmdet  # type: ignore
        import mmengine  # type: ignore
        import mmocr  # type: ignore
        import torch  # type: ignore
        from mmocr.apis import (  # type: ignore
            KIEInferencer,
            MMOCRInferencer,
            TextDetInferencer,
            TextRecInferencer,
            TextSpotInferencer,
        )
    except Exception as exc:  # pragma: no cover - depends on host env
        print(
            "ERROR: failed to import MMOCR inference stack: "
            f"{type(exc).__name__}: {exc}",
            file=sys.stderr,
        )
        print(
            "Install/activate an environment with mmocr, mmcv, mmengine, "
            "mmdet, torch, and their compatible dependencies, then retry.",
            file=sys.stderr,
        )
        raise SystemExit(2)

    versions = {
        "mmocr": getattr(mmocr, "__version__", "unknown"),
        "torch": getattr(torch, "__version__", "unknown"),
        "mmcv": getattr(mmcv, "__version__", "unknown"),
        "mmengine": getattr(mmengine, "__version__", "unknown"),
        "mmdet": getattr(mmdet, "__version__", "unknown"),
    }
    classes = {
        "mmocr": MMOCRInferencer,
        "textdet": TextDetInferencer,
        "textrec": TextRecInferencer,
        "kie": KIEInferencer,
        "textspot": TextSpotInferencer,
    }
    return versions, classes, torch


def parse_scalar(raw: str) -> Optional[str]:
    value = raw.strip().strip("'\"")
    if not value or value in {"[]", "{}", "null", "None"}:
        return None
    # Ignore long inline lists; following list items will be parsed separately.
    if value.startswith("["):
        return None
    return value


def collect_alias_block(lines: Sequence[str], start: int) -> List[str]:
    aliases: List[str] = []
    for line in lines[start + 1 :]:
        if not line.startswith((" ", "\t")):
            break
        item = re.match(r"\s*-\s*(.+?)\s*$", line)
        if item:
            parsed = parse_scalar(item.group(1))
            if parsed:
                aliases.append(parsed)
        elif line.strip() and not line.startswith((" ", "\t")):
            break
    return aliases


def parse_metafile_names(path: Path) -> Set[str]:
    names: Set[str] = set()
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except Exception:
        return names
    for i, line in enumerate(lines):
        name_match = re.match(r"\s*-?\s*Name:\s*(.+?)\s*$", line)
        if name_match:
            parsed = parse_scalar(name_match.group(1))
            if parsed:
                names.add(parsed)
        alias_match = re.match(r"\s*Alias:\s*(.*?)\s*$", line)
        if alias_match:
            inline = parse_scalar(alias_match.group(1))
            if inline:
                names.add(inline)
            else:
                names.update(collect_alias_block(lines, i))
    return names


def kind_from_metafile(path_text: str) -> Optional[str]:
    normalized = path_text.replace("\\", "/")
    if "/textdet/" in normalized or normalized.startswith("configs/textdet/"):
        return "det"
    if "/textrecog/" in normalized or normalized.startswith("configs/textrecog/"):
        return "rec"
    if "/kie/" in normalized or normalized.startswith("configs/kie/"):
        return "kie"
    if "textspot" in normalized:
        return "spot"
    return None


def augment_known_models(mmocr_module: Optional[Any]) -> Dict[str, Set[str]]:
    known = {kind: set(values) for kind, values in KNOWN_MODELS.items()}
    if mmocr_module is None:
        return known

    try:
        pkg_dir = Path(mmocr_module.__file__).resolve().parent
    except Exception:
        return known

    candidates = [pkg_dir / "model-index.yml", pkg_dir.parent / "model-index.yml"]
    for model_index in candidates:
        if not model_index.is_file():
            continue
        try:
            text = model_index.read_text(encoding="utf-8")
        except Exception:
            continue
        for rel in re.findall(r"configs/[^\s'\"]+/metafile\.yml", text):
            kind = kind_from_metafile(rel)
            if not kind:
                continue
            metafile = model_index.parent / rel
            if metafile.is_file():
                known[kind].update(parse_metafile_names(metafile))
        break
    return known


def summarize_known(known: Dict[str, Set[str]], kind: str, limit: int = 12) -> str:
    items = sorted(known.get(kind, set()))
    if not items:
        return "no built-in aliases listed; use a local config path"
    shown = ", ".join(items[:limit])
    if len(items) > limit:
        shown += f", ... ({len(items)} total)"
    return shown


def validate_path_or_url(label: str, value: Optional[str], errors: List[str], warnings: List[str]) -> None:
    if not value:
        return
    if is_url(value):
        warnings.append(f"{label} is a URL; real execution may require network access.")
        return
    if not path_exists(value):
        errors.append(f"{label} does not exist: {value}")


def validate_model_spec(
    kind: str,
    model: Optional[str],
    weights: Optional[str],
    known: Dict[str, Set[str]],
    errors: List[str],
    warnings: List[str],
) -> None:
    label = KIND_LABELS[kind]
    if model:
        if is_url(model):
            warnings.append(f"{label} model config is a URL; execution may require network access.")
        elif looks_like_path(model):
            if not path_exists(model):
                errors.append(f"{label} config/model path does not exist: {model}")
            elif not model.endswith(".py"):
                warnings.append(f"{label} model path is not a .py config: {model}")
        elif model not in known.get(kind, set()):
            errors.append(
                f"Unknown {label} model name/alias: {model}. "
                f"Known examples: {summarize_known(known, kind)}. "
                "Use a local .py config path for custom models."
            )
    if weights:
        validate_path_or_url(f"{label} weights", weights, errors, warnings)
    if model and not weights and not looks_like_path(model) and not is_url(model):
        warnings.append(
            f"{label} model '{model}' has no local weights argument; real execution may "
            "resolve pretrained weights from the model zoo/cache."
        )
    if model and looks_like_path(model) and model.endswith(".py") and not weights:
        warnings.append(
            f"{label} config path has no weights argument; execution would use random "
            "initialization unless the runner obtains weights elsewhere."
        )


def selected_specs(args: argparse.Namespace) -> Iterable[Tuple[str, Optional[str], Optional[str]]]:
    if args.inferencer == "mmocr":
        yield "det", args.det, args.det_weights
        yield "rec", args.rec, args.rec_weights
        yield "kie", args.kie, args.kie_weights
    else:
        kind = {
            "textdet": "det",
            "textrec": "rec",
            "kie": "kie",
            "textspot": "spot",
        }[args.inferencer]
        yield kind, args.model, args.weights


def execution_would_need_download(model: Optional[str], weights: Optional[str]) -> bool:
    if is_url(model) or is_url(weights):
        return True
    if model and not weights and not looks_like_path(model):
        return True
    return False


def execution_would_be_random(model: Optional[str], weights: Optional[str]) -> bool:
    return bool(model and looks_like_path(model) and model.endswith(".py") and not weights)


def validate_args(
    args: argparse.Namespace,
    known: Dict[str, Set[str]],
    torch_module: Optional[Any],
) -> Tuple[List[str], List[str]]:
    errors: List[str] = []
    warnings: List[str] = []

    if args.input_opt and args.inputs and args.input_opt != args.inputs:
        errors.append("Provide input either positionally or with --input, not both.")
    input_value = args.input_opt or args.inputs
    args.input_value = input_value

    if input_value and not is_url(input_value) and not path_exists(input_value):
        errors.append(f"Input path does not exist: {input_value}")

    if args.save_pred or args.save_vis:
        if not args.out_dir:
            errors.append("--out-dir is required when --save-pred/--save_pred or --save-vis/--save_vis is used.")

    if args.inferencer == "mmocr":
        if not any([args.det, args.rec, args.kie]):
            errors.append("MMOCRInferencer requires at least one of --det, --rec, or --kie.")
        if args.kie and (not args.det or not args.rec):
            errors.append("--kie in MMOCRInferencer mode requires both --det and --rec.")
    else:
        if not args.model and not args.weights:
            errors.append(f"--inferencer {args.inferencer} requires --model or --weights.")
        if args.inferencer == "kie" and args.execute:
            errors.append(
                "This helper only preflights direct KIEInferencer. Execute direct KIE "
                "from Python with dict/list inputs containing img/img_shape and instances."
            )

    for kind, model, weights in selected_specs(args):
        if model or weights:
            validate_model_spec(kind, model, weights, known, errors, warnings)
            if args.execute and execution_would_need_download(model, weights) and not args.allow_download:
                errors.append(
                    f"Executing {KIND_LABELS[kind]} with model/weights that may require "
                    "download is blocked by default. Supply local weights or add --allow-download."
                )
            if args.execute and execution_would_be_random(model, weights) and not args.allow_random_init:
                errors.append(
                    f"Executing {KIND_LABELS[kind]} from a config path without weights is "
                    "blocked to avoid random-initialized predictions. Add weights or --allow-random-init."
                )

    if args.execute and not input_value:
        errors.append("--execute requires an input image or directory.")

    if args.show and os.name != "nt" and not os.environ.get("DISPLAY"):
        warnings.append("--show was requested but DISPLAY is not set; use --save-vis in headless sessions.")

    if args.device and args.device.startswith("cuda"):
        cuda_available = bool(torch_module is not None and torch_module.cuda.is_available())
        msg = f"CUDA device requested ({args.device}) but torch.cuda.is_available() is false."
        if not cuda_available and args.execute:
            errors.append(msg)
        elif not cuda_available:
            warnings.append(msg)

    if args.batch_size < 1:
        errors.append("--batch-size must be >= 1.")
    for name in ("det_batch_size", "rec_batch_size", "kie_batch_size"):
        value = getattr(args, name)
        if value is not None and value < 1:
            errors.append(f"--{name.replace('_', '-')} must be >= 1.")

    return errors, warnings


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Validate MMOCR inference inputs/models/devices without downloading weights by default; "
            "optionally execute when explicitly requested."
        )
    )
    parser.add_argument("inputs", nargs="?", help="Input image file, image URL, or image directory.")
    parser.add_argument("--input", dest="input_opt", help="Input image file, image URL, or image directory.")
    parser.add_argument(
        "--inferencer",
        choices=["mmocr", "textdet", "textrec", "kie", "textspot"],
        default="mmocr",
        help="Inferencer surface to validate or execute. Default: mmocr chain wrapper.",
    )

    # MMOCRInferencer chain arguments.
    parser.add_argument("--det", help="Text detection model name/alias or local config path.")
    parser.add_argument("--det-weights", help="Local/URL checkpoint for --det.")
    parser.add_argument("--rec", help="Text recognition model name/alias or local config path.")
    parser.add_argument("--rec-weights", help="Local/URL checkpoint for --rec.")
    parser.add_argument("--kie", help="KIE model name/alias or local config path; requires --det and --rec in mmocr mode.")
    parser.add_argument("--kie-weights", help="Local/URL checkpoint for --kie.")

    # Standard inferencer arguments.
    parser.add_argument("--model", help="Standard inferencer model name/alias or local config path.")
    parser.add_argument("--weights", help="Standard inferencer local/URL checkpoint path.")

    parser.add_argument("--device", help="Inference device, e.g. cpu, cuda:0. Default lets MMEngine decide.")
    parser.add_argument("--batch-size", type=int, default=1, help="Inference batch size. Default: 1.")
    parser.add_argument("--det-batch-size", type=int, help="Detection batch override for mmocr mode.")
    parser.add_argument("--rec-batch-size", type=int, help="Recognition batch override for mmocr mode.")
    parser.add_argument("--kie-batch-size", type=int, help="KIE batch override for mmocr mode.")
    parser.add_argument("--out-dir", help="Output directory for saved predictions/visualizations.")
    parser.add_argument("--save-pred", "--save_pred", action="store_true", dest="save_pred", help="Save predictions under out_dir/preds/.")
    parser.add_argument("--save-vis", "--save_vis", action="store_true", dest="save_vis", help="Save visualizations under out_dir/vis/.")
    parser.add_argument("--return-vis", action="store_true", help="Return visualization arrays from MMOCR.")
    parser.add_argument("--print-result", action="store_true", help="Print prediction dictionaries during execution.")
    parser.add_argument("--show", action="store_true", help="Display popup visualizations; unsafe in headless sessions.")
    parser.add_argument("--wait-time", type=float, default=0, help="Visualization wait time for show=True.")
    parser.add_argument("--pred-score-thr", type=float, default=0.3, help="Prediction score threshold for drawing visualizations.")
    parser.add_argument("--execute", action="store_true", help="Actually construct inferencers and run inference after validation.")
    parser.add_argument("--allow-download", action="store_true", help="Permit execution paths that may download or fetch model-zoo weights/URLs.")
    parser.add_argument("--allow-random-init", action="store_true", help="Permit execution from config paths without checkpoints.")
    parser.add_argument("--json", action="store_true", help="Print the final preflight summary as JSON.")
    return parser


def print_summary(summary: Dict[str, Any], as_json: bool) -> None:
    if as_json:
        print(json.dumps(summary, indent=2, sort_keys=True))
        return
    print("MMOCR inference smoke summary")
    print("versions:", ", ".join(f"{k}={v}" for k, v in summary["versions"].items()))
    print("inferencer:", summary["inferencer"])
    print("input:", summary.get("input") or "<not supplied>")
    print("execute:", summary["execute"])
    print("selected models:")
    for spec in summary["models"]:
        print(f"  - {spec['kind']}: model={spec.get('model') or '<none>'}, weights={spec.get('weights') or '<none>'}")
    for warning in summary.get("warnings", []):
        print(f"WARNING: {warning}")


def execute_inference(args: argparse.Namespace, classes: Dict[str, Any]) -> Dict[str, Any]:
    input_value = args.input_value
    call_kwargs = {
        "batch_size": args.batch_size,
        "out_dir": args.out_dir or "",
        "return_vis": args.return_vis,
        "save_vis": args.save_vis,
        "save_pred": args.save_pred,
        "print_result": args.print_result,
        "show": args.show,
        "wait_time": args.wait_time,
        "pred_score_thr": args.pred_score_thr,
    }
    if args.inferencer == "mmocr":
        init_kwargs = {
            "det": args.det,
            "det_weights": args.det_weights,
            "rec": args.rec,
            "rec_weights": args.rec_weights,
            "kie": args.kie,
            "kie_weights": args.kie_weights,
            "device": args.device,
        }
        inferencer = classes["mmocr"](**init_kwargs)
        if args.det_batch_size is not None:
            call_kwargs["det_batch_size"] = args.det_batch_size
        if args.rec_batch_size is not None:
            call_kwargs["rec_batch_size"] = args.rec_batch_size
        if args.kie_batch_size is not None:
            call_kwargs["kie_batch_size"] = args.kie_batch_size
        result = inferencer(input_value, **call_kwargs)
    else:
        class_key = args.inferencer
        inferencer = classes[class_key](model=args.model, weights=args.weights, device=args.device)
        result = inferencer(input_value, **call_kwargs)

    predictions = result.get("predictions", []) if isinstance(result, dict) else []
    first_keys = sorted(predictions[0].keys()) if predictions and isinstance(predictions[0], dict) else []
    return {
        "prediction_count": len(predictions),
        "first_prediction_keys": first_keys,
        "visualization_count": len(result.get("visualization", []) or []) if isinstance(result, dict) else 0,
    }


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    versions, classes, torch_module = import_runtime()
    import mmocr as mmocr_module  # type: ignore  # already imported by import_runtime

    known = augment_known_models(mmocr_module)
    errors, warnings = validate_args(args, known, torch_module)

    models = [
        {"kind": kind, "model": model, "weights": weights}
        for kind, model, weights in selected_specs(args)
        if model or weights
    ]
    summary: Dict[str, Any] = {
        "versions": versions,
        "inferencer": args.inferencer,
        "input": args.input_value,
        "execute": bool(args.execute),
        "models": models,
        "warnings": warnings,
    }

    if errors:
        summary["errors"] = errors
        print_summary(summary, args.json)
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 2

    if args.execute:
        run_info = execute_inference(args, classes)
        summary["execution"] = run_info
    else:
        summary["execution"] = "not requested; validation only"

    print_summary(summary, args.json)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
