#!/usr/bin/env python3
"""Validate a MUNIT YAML config without importing MUNIT or running CUDA code.

The checker is intentionally static and safe: it parses a YAML file, verifies
required keys, checks supported option names from the original source, and can
optionally verify that dataset paths exist relative to a user-provided checkout.
"""
import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

ALLOWED_INIT = {"gaussian", "kaiming", "xavier", "orthogonal", "default"}
ALLOWED_LR = {"constant", "step"}
ALLOWED_ACTIVATION = {"relu", "lrelu", "prelu", "selu", "tanh", "none"}
ALLOWED_PADDING = {"reflect", "replicate", "zero"}
ALLOWED_NORM = {"bn", "in", "ln", "adain", "none", "sn"}
ALLOWED_GAN = {"lsgan", "nsgan"}
COMMON_REQUIRED = {
    "image_save_iter", "image_display_iter", "display_size", "snapshot_save_iter", "log_iter",
    "max_iter", "batch_size", "weight_decay", "beta1", "beta2", "init", "lr", "lr_policy",
    "gan_w", "recon_x_w", "recon_x_cyc_w", "vgg_w", "input_dim_a", "input_dim_b",
    "num_workers", "crop_image_height", "crop_image_width", "gen", "dis",
}
MUNIT_REQUIRED = {"recon_s_w", "recon_c_w"}
UNIT_REQUIRED = {"recon_kl_w", "recon_kl_cyc_w"}
GEN_MUNIT_REQUIRED = {"dim", "mlp_dim", "style_dim", "activ", "n_downsample", "n_res", "pad_type"}
GEN_UNIT_REQUIRED = {"dim", "activ", "n_downsample", "n_res", "pad_type"}
DIS_REQUIRED = {"dim", "norm", "activ", "n_layer", "gan_type", "num_scales", "pad_type"}
FOLDER_SPLITS = ["trainA", "trainB", "testA", "testB"]
LIST_KEYS = [
    "data_folder_train_a", "data_list_train_a", "data_folder_test_a", "data_list_test_a",
    "data_folder_train_b", "data_list_train_b", "data_folder_test_b", "data_list_test_b",
]


def parse_scalar(text: str) -> Any:
    value = text.strip()
    if not value:
        return ""
    lower = value.lower()
    if lower in {"true", "false"}:
        return lower == "true"
    if lower in {"none", "null", "~"}:
        return None
    if re.match(r"^[+-]?\d+$", value):
        try:
            return int(value)
        except ValueError:
            pass
    if re.match(r"^[+-]?(\d+\.\d*|\d*\.\d+|\d+)(e[+-]?\d+)?$", value, re.I):
        try:
            return float(value)
        except ValueError:
            pass
    return value.strip('"\'')


def parse_simple_yaml(path: Path) -> Dict[str, Any]:
    data: Dict[str, Any] = {}
    current: Dict[str, Any] = data
    current_indent = 0
    stack: List[Tuple[int, Dict[str, Any]]] = [(0, data)]
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].rstrip()
        if not line.strip() or ":" not in line:
            continue
        indent = len(line) - len(line.lstrip(" "))
        key, value = line.strip().split(":", 1)
        key = key.strip()
        value = value.strip()
        while stack and indent < stack[-1][0]:
            stack.pop()
        current = stack[-1][1]
        if value == "":
            current[key] = {}
            stack.append((indent + 2, current[key]))
        else:
            current[key] = parse_scalar(value)
    return data


def load_config(path: Path) -> Tuple[Dict[str, Any], str]:
    try:
        import yaml  # type: ignore
        with path.open("r", encoding="utf-8") as handle:
            loaded = yaml.safe_load(handle)
        if isinstance(loaded, dict):
            return loaded, "pyyaml.safe_load"
        return {}, "pyyaml.safe_load-empty"
    except Exception:
        return parse_simple_yaml(path), "built-in-simple-yaml"


def resolve_path(value: Any, repo_root: Path, config_dir: Path) -> Path:
    p = Path(str(value))
    if p.is_absolute():
        return p
    repo_candidate = repo_root / p
    config_candidate = config_dir / p
    if repo_candidate.exists() or not config_candidate.exists():
        return repo_candidate
    return config_candidate


def require_keys(container: Dict[str, Any], keys: set, label: str, errors: List[str]) -> None:
    missing = sorted(k for k in keys if k not in container)
    if missing:
        errors.append(f"{label} missing keys: {missing}")


def positive_int(conf: Dict[str, Any], key: str, errors: List[str], warnings: List[str], label: str = "") -> None:
    if key not in conf:
        return
    value = conf[key]
    where = f"{label}.{key}" if label else key
    if not isinstance(value, int) or value <= 0:
        errors.append(f"{where} should be a positive integer, observed {value!r}")


def validate(conf: Dict[str, Any], config_path: Path, repo_root: Path, trainer: str, check_paths: bool) -> Dict[str, Any]:
    errors: List[str] = []
    warnings: List[str] = []
    require_keys(conf, COMMON_REQUIRED | (MUNIT_REQUIRED if trainer == "MUNIT" else UNIT_REQUIRED), "top-level config", errors)

    gen = conf.get("gen") if isinstance(conf.get("gen"), dict) else {}
    dis = conf.get("dis") if isinstance(conf.get("dis"), dict) else {}
    if not gen:
        errors.append("gen section missing or not a mapping")
    if not dis:
        errors.append("dis section missing or not a mapping")
    require_keys(gen, GEN_MUNIT_REQUIRED if trainer == "MUNIT" else GEN_UNIT_REQUIRED, "gen section", errors)
    require_keys(dis, DIS_REQUIRED, "dis section", errors)

    for key in ["image_save_iter", "image_display_iter", "display_size", "snapshot_save_iter", "log_iter", "max_iter", "batch_size", "num_workers", "crop_image_height", "crop_image_width"]:
        positive_int(conf, key, errors, warnings)
    for key in ["dim", "n_downsample", "n_res"]:
        positive_int(gen, key, errors, warnings, "gen")
    if trainer == "MUNIT":
        positive_int(gen, "style_dim", errors, warnings, "gen")
        positive_int(gen, "mlp_dim", errors, warnings, "gen")
    for key in ["dim", "n_layer", "num_scales"]:
        positive_int(dis, key, errors, warnings, "dis")

    if conf.get("init") not in ALLOWED_INIT and "init" in conf:
        errors.append(f"unsupported init {conf.get('init')!r}; expected one of {sorted(ALLOWED_INIT)}")
    if conf.get("lr_policy") not in ALLOWED_LR and "lr_policy" in conf:
        errors.append(f"unsupported lr_policy {conf.get('lr_policy')!r}; expected one of {sorted(ALLOWED_LR)}")
    if gen.get("activ") not in ALLOWED_ACTIVATION and "activ" in gen:
        errors.append(f"unsupported gen.activ {gen.get('activ')!r}")
    if dis.get("activ") not in ALLOWED_ACTIVATION and "activ" in dis:
        errors.append(f"unsupported dis.activ {dis.get('activ')!r}")
    if gen.get("pad_type") not in ALLOWED_PADDING and "pad_type" in gen:
        errors.append(f"unsupported gen.pad_type {gen.get('pad_type')!r}")
    if dis.get("pad_type") not in ALLOWED_PADDING and "pad_type" in dis:
        errors.append(f"unsupported dis.pad_type {dis.get('pad_type')!r}")
    if dis.get("norm") not in ALLOWED_NORM and "norm" in dis:
        errors.append(f"unsupported dis.norm {dis.get('norm')!r}")
    if dis.get("gan_type") not in ALLOWED_GAN and "gan_type" in dis:
        errors.append(f"unsupported dis.gan_type {dis.get('gan_type')!r}")

    if conf.get("input_dim_a") not in {1, 3} and "input_dim_a" in conf:
        warnings.append(f"input_dim_a={conf.get('input_dim_a')!r}; common MUNIT usage is 1 or 3 channels")
    if conf.get("input_dim_b") not in {1, 3} and "input_dim_b" in conf:
        warnings.append(f"input_dim_b={conf.get('input_dim_b')!r}; common MUNIT usage is 1 or 3 channels")
    if "new_size" not in conf and not {"new_size_a", "new_size_b"}.issubset(conf):
        errors.append("config needs either new_size or both new_size_a/new_size_b")
    if "new_size" in conf:
        positive_int(conf, "new_size", errors, warnings)
    else:
        positive_int(conf, "new_size_a", errors, warnings)
        positive_int(conf, "new_size_b", errors, warnings)
    if conf.get("vgg_w", 0):
        warnings.append("vgg_w is positive; original load_vgg16 can create/download/convert VGG files under output_path/models")
    if trainer == "UNIT" and MUNIT_REQUIRED.issubset(conf) and not UNIT_REQUIRED.issubset(conf):
        warnings.append("this looks like a bundled MUNIT config; UNIT also needs recon_kl_w and recon_kl_cyc_w")

    data_mode = "folder" if "data_root" in conf else "list"
    path_results: Dict[str, Any] = {"mode": data_mode, "checked": check_paths, "paths": []}
    if data_mode == "list":
        missing_list_keys = [k for k in LIST_KEYS if k not in conf]
        if missing_list_keys:
            errors.append(f"list mode missing keys: {missing_list_keys}")
    if check_paths:
        if data_mode == "folder" and "data_root" in conf:
            root = resolve_path(conf["data_root"], repo_root, config_path.parent)
            path_results["data_root"] = str(root)
            for split in FOLDER_SPLITS:
                p = root / split
                exists = p.is_dir()
                path_results["paths"].append({"key": split, "path": str(p), "exists": exists})
                if not exists:
                    errors.append(f"folder mode missing split directory: {p}")
        elif data_mode == "list":
            for key in LIST_KEYS:
                if key not in conf:
                    continue
                p = resolve_path(conf[key], repo_root, config_path.parent)
                exists = p.exists()
                path_results["paths"].append({"key": key, "path": str(p), "exists": exists})
                if not exists:
                    errors.append(f"list mode path for {key} does not exist: {p}")
    else:
        warnings.append("dataset path existence checks skipped; pass --repo-root and do not use --no-path-check to enable them")

    return {
        "config": str(config_path),
        "trainer": trainer,
        "data_mode": data_mode,
        "errors": errors,
        "warnings": warnings,
        "path_results": path_results,
        "summary": {
            "top_key_count": len(conf),
            "gen_keys": sorted(gen.keys()),
            "dis_keys": sorted(dis.keys()),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Static MUNIT YAML config validator; no CUDA, downloads, or model construction.")
    parser.add_argument("--config", required=True, help="Path to the MUNIT YAML config to validate.")
    parser.add_argument("--repo-root", default=".", help="User's MUNIT checkout root for resolving repo-relative dataset paths.")
    parser.add_argument("--trainer", choices=["MUNIT", "UNIT"], default="MUNIT", help="Trainer-specific config expectations.")
    parser.add_argument("--no-path-check", action="store_true", help="Skip dataset path existence checks.")
    parser.add_argument("--json", action="store_true", help="Emit JSON report.")
    args = parser.parse_args()

    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = Path.cwd() / config_path
    repo_root = Path(args.repo_root)
    if not repo_root.is_absolute():
        repo_root = Path.cwd() / repo_root

    if not config_path.exists():
        print(f"FAIL config not found: {config_path}", file=sys.stderr)
        return 2
    conf, parser_name = load_config(config_path)
    report = validate(conf, config_path, repo_root, args.trainer, not args.no_path_check)
    report["parser"] = parser_name

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"MUNIT config validation: {config_path}")
        print(f"parser: {parser_name}")
        print(f"trainer: {args.trainer}")
        print(f"data mode: {report['data_mode']}")
        for item in report["warnings"]:
            print(f"WARN {item}")
        for item in report["errors"]:
            print(f"FAIL {item}")
        if not report["errors"]:
            print("OK no blocking config errors found")
    return 2 if report["errors"] else 0


if __name__ == "__main__":
    sys.exit(main())
