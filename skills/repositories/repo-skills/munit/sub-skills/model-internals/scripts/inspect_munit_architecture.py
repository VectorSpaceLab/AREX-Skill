#!/usr/bin/env python3
"""
Safely inspect MUNIT architecture source text and config files.

This helper is intentionally static: it does not import trainer/network modules,
instantiate models, allocate CUDA tensors, run train/test entrypoints, or
download assets. It reads source text and simple YAML config files only.
"""
import argparse
import ast
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

EXPECTED_SIGNATURES = {
    "MUNIT_Trainer": ["hyperparameters"],
    "UNIT_Trainer": ["hyperparameters"],
    "AdaINGen": ["input_dim", "params"],
    "VAEGen": ["input_dim", "params"],
    "MsImageDis": ["input_dim", "params"],
    "StyleEncoder": ["n_downsample", "input_dim", "dim", "style_dim", "norm", "activ", "pad_type"],
    "ContentEncoder": ["n_downsample", "n_res", "input_dim", "dim", "norm", "activ", "pad_type"],
    "Decoder": ["n_upsample", "n_res", "dim", "output_dim", "res_norm", "activ", "pad_type"],
    "Conv2dBlock": ["input_dim", "output_dim", "kernel_size", "stride", "padding", "norm", "activation", "pad_type"],
    "LinearBlock": ["input_dim", "output_dim", "norm", "activation"],
    "AdaptiveInstanceNorm2d": ["num_features", "eps", "momentum"],
    "LayerNorm": ["num_features", "eps", "affine"],
}

EXPECTED_METHODS = {
    "MUNIT_Trainer": ["gen_update", "dis_update", "sample", "resume", "save"],
    "UNIT_Trainer": ["gen_update", "dis_update", "sample", "resume", "save"],
    "AdaINGen": ["encode", "decode", "assign_adain_params", "get_num_adain_params"],
    "VAEGen": ["encode", "decode"],
    "MsImageDis": ["calc_dis_loss", "calc_gen_loss"],
}

ALLOWED_PADDING = {"reflect", "replicate", "zero"}
ALLOWED_NORM = {"bn", "in", "ln", "adain", "none", "sn"}
ALLOWED_ACTIVATION = {"relu", "lrelu", "prelu", "selu", "tanh", "none"}
ALLOWED_GAN = {"lsgan", "nsgan"}
ALLOWED_INIT = {"gaussian", "xavier", "kaiming", "orthogonal", "default"}
ALLOWED_LR = {"constant", "step"}

COMMON_TOP_KEYS = {
    "lr", "beta1", "beta2", "weight_decay", "init", "gan_w", "recon_x_w",
    "recon_x_cyc_w", "vgg_w", "input_dim_a", "input_dim_b", "gen", "dis",
}
MUNIT_KEYS = {"recon_s_w", "recon_c_w"}
UNIT_KEYS = {"recon_kl_w", "recon_kl_cyc_w"}
GEN_MUNIT_KEYS = {"dim", "mlp_dim", "style_dim", "activ", "n_downsample", "n_res", "pad_type"}
GEN_UNIT_KEYS = {"dim", "activ", "n_downsample", "n_res", "pad_type"}
DIS_KEYS = {"dim", "norm", "activ", "n_layer", "gan_type", "num_scales", "pad_type"}

MARKERS = {
    "unconditional_cuda": r"\.cuda\(",
    "torch_cuda_seed_or_sync": r"torch\.cuda\.",
    "volatile_variable": r"volatile\s*=\s*True",
    "functional_sigmoid": r"F\.sigmoid\(",
    "yaml_load_no_loader": r"yaml\.load\(",
    "load_lua": r"load_lua",
    "wget_side_effect": r"os\.system\([^\n]*wget",
    "adain_assertion": r"Please assign weight and bias before calling AdaIN",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Static MUNIT architecture/config inspector; no imports, CUDA, downloads, training, or inference.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--repo-root", default=".", help="Path to a MUNIT checkout to inspect as text.")
    parser.add_argument("--config", help="Optional MUNIT YAML config to validate statically.")
    parser.add_argument("--trainer", choices=["MUNIT", "UNIT"], default="MUNIT", help="Trainer-specific config expectations.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of a human summary.")
    parser.add_argument("--strict", action="store_true", help="Exit nonzero when warnings are found, not only errors.")
    parser.add_argument("--no-source", action="store_true", help="Skip source-text class/marker inspection.")
    return parser.parse_args()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def class_info(source: str) -> Dict[str, Dict[str, Any]]:
    tree = ast.parse(source)
    out: Dict[str, Dict[str, Any]] = {}
    for node in tree.body:
        if not isinstance(node, ast.ClassDef):
            continue
        methods = {}
        init_args: List[str] = []
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                args = [arg.arg for arg in item.args.args]
                public_args = [arg for arg in args if arg != "self"]
                methods[item.name] = public_args
                if item.name == "__init__":
                    init_args = public_args
        out[node.name] = {"init_args": init_args, "methods": methods}
    return out


def inspect_source(repo_root: Path) -> Tuple[Dict[str, Any], List[str], List[str]]:
    errors: List[str] = []
    warnings: List[str] = []
    result: Dict[str, Any] = {"classes": {}, "markers": {}, "files_checked": []}
    source_files = ["trainer.py", "networks.py", "utils.py", "train.py", "test.py", "test_batch.py"]

    combined_classes: Dict[str, Dict[str, Any]] = {}
    for rel in source_files:
        path = repo_root / rel
        if not path.exists():
            if rel in {"trainer.py", "networks.py", "utils.py"}:
                errors.append(f"missing required source file: {rel}")
            continue
        text = read_text(path)
        result["files_checked"].append(rel)
        for marker, pattern in MARKERS.items():
            count = len(re.findall(pattern, text))
            if count:
                result["markers"].setdefault(marker, {})[rel] = count
        if rel in {"trainer.py", "networks.py"}:
            try:
                combined_classes.update(class_info(text))
            except SyntaxError as exc:
                errors.append(f"could not parse {rel}: {exc}")

    for cls, expected_args in EXPECTED_SIGNATURES.items():
        info = combined_classes.get(cls)
        if info is None:
            errors.append(f"missing expected class: {cls}")
            continue
        observed = info.get("init_args", [])
        result["classes"][cls] = {"init_args": observed, "methods": sorted(info.get("methods", {}).keys())}
        if observed != expected_args:
            errors.append(f"signature mismatch for {cls}: expected {expected_args}, observed {observed}")
        for method in EXPECTED_METHODS.get(cls, []):
            if method not in info.get("methods", {}):
                errors.append(f"missing expected method: {cls}.{method}")

    if result["markers"].get("wget_side_effect"):
        warnings.append("VGG helper contains a wget side effect; avoid trainer construction with vgg_w > 0 in static checks.")
    if result["markers"].get("unconditional_cuda"):
        warnings.append("source contains unconditional .cuda() calls; CPU-only static checks do not prove runtime execution.")
    if result["markers"].get("volatile_variable"):
        warnings.append("source contains legacy volatile=True inference code; port to torch.no_grad() for modern PyTorch.")
    if result["markers"].get("functional_sigmoid"):
        warnings.append("source contains F.sigmoid in nsgan losses; preserve semantics when modernizing.")
    if result["markers"].get("yaml_load_no_loader"):
        warnings.append("source contains yaml.load without explicit Loader; prefer safe_load for plain configs.")
    if result["markers"].get("load_lua"):
        warnings.append("source references load_lua; modern PyTorch removed this Torch7 loader.")

    return result, errors, warnings


def strip_comment(line: str) -> str:
    # Config files in this repository use simple comments and scalar values.
    return line.split("#", 1)[0].rstrip()


def parse_scalar(value: str) -> Any:
    value = value.strip()
    if value == "":
        return ""
    lower = value.lower()
    if lower in {"true", "false"}:
        return lower == "true"
    if lower in {"none", "null"}:
        return None
    try:
        if re.match(r"^[+-]?\d+$", value):
            return int(value)
        if re.match(r"^[+-]?(\d+\.\d*|\d*\.\d+|\d+)(e[+-]?\d+)?$", value, re.I):
            return float(value)
    except ValueError:
        pass
    return value.strip('"\'')


def parse_simple_yaml(path: Path) -> Dict[str, Any]:
    data: Dict[str, Any] = {}
    current_map: Optional[Dict[str, Any]] = None
    for raw_line in read_text(path).splitlines():
        line = strip_comment(raw_line)
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip(" "))
        if ":" not in line:
            continue
        key, value = line.strip().split(":", 1)
        key = key.strip()
        value = value.strip()
        if indent == 0:
            if value == "":
                data[key] = {}
                current_map = data[key]
            else:
                data[key] = parse_scalar(value)
                current_map = None
        elif current_map is not None:
            current_map[key] = parse_scalar(value)
    return data


def load_config(path: Path) -> Tuple[Dict[str, Any], str]:
    try:
        import yaml  # type: ignore
        with path.open("r", encoding="utf-8") as handle:
            loaded = yaml.safe_load(handle)
        if isinstance(loaded, dict):
            return loaded, "pyyaml.safe_load"
    except Exception:
        pass
    return parse_simple_yaml(path), "built-in simple parser"


def positive_int(value: Any) -> bool:
    return isinstance(value, int) and value > 0


def validate_config(path: Path, trainer: str) -> Tuple[Dict[str, Any], List[str], List[str]]:
    errors: List[str] = []
    warnings: List[str] = []
    conf, parser_name = load_config(path)
    result: Dict[str, Any] = {"path": str(path), "parser": parser_name, "top_keys": sorted(conf.keys())}

    expected_top = set(COMMON_TOP_KEYS)
    expected_top.update(MUNIT_KEYS if trainer == "MUNIT" else UNIT_KEYS)
    missing_top = sorted(k for k in expected_top if k not in conf)
    if missing_top:
        errors.append(f"config missing required {trainer} keys: {missing_top}")

    gen = conf.get("gen") if isinstance(conf.get("gen"), dict) else {}
    dis = conf.get("dis") if isinstance(conf.get("dis"), dict) else {}
    result["gen"] = gen
    result["dis"] = dis

    gen_expected = GEN_MUNIT_KEYS if trainer == "MUNIT" else GEN_UNIT_KEYS
    missing_gen = sorted(k for k in gen_expected if k not in gen)
    missing_dis = sorted(k for k in DIS_KEYS if k not in dis)
    if missing_gen:
        errors.append(f"config gen section missing keys for {trainer}: {missing_gen}")
    if missing_dis:
        errors.append(f"config dis section missing keys: {missing_dis}")

    if trainer == "UNIT" and "style_dim" in gen:
        warnings.append("UNIT does not use gen.style_dim for diversity, although shared demo configs may still include it.")
    if trainer == "MUNIT" and not positive_int(gen.get("style_dim")):
        errors.append("MUNIT requires positive integer gen.style_dim")

    if gen.get("activ") not in ALLOWED_ACTIVATION and "activ" in gen:
        errors.append(f"unsupported gen.activ: {gen.get('activ')}")
    if dis.get("activ") not in ALLOWED_ACTIVATION and "activ" in dis:
        errors.append(f"unsupported dis.activ: {dis.get('activ')}")
    if gen.get("pad_type") not in ALLOWED_PADDING and "pad_type" in gen:
        errors.append(f"unsupported gen.pad_type: {gen.get('pad_type')}")
    if dis.get("pad_type") not in ALLOWED_PADDING and "pad_type" in dis:
        errors.append(f"unsupported dis.pad_type: {dis.get('pad_type')}")
    if dis.get("norm") not in ALLOWED_NORM and "norm" in dis:
        errors.append(f"unsupported dis.norm: {dis.get('norm')}")
    if dis.get("gan_type") not in ALLOWED_GAN and "gan_type" in dis:
        errors.append(f"unsupported dis.gan_type: {dis.get('gan_type')}")
    if conf.get("init") not in ALLOWED_INIT and "init" in conf:
        errors.append(f"unsupported init: {conf.get('init')}")
    if conf.get("lr_policy", "constant") not in ALLOWED_LR:
        errors.append(f"unsupported lr_policy: {conf.get('lr_policy')}")

    for dim_key in ("input_dim_a", "input_dim_b"):
        if dim_key in conf and conf[dim_key] not in {1, 3}:
            warnings.append(f"{dim_key}={conf[dim_key]} is outside documented 1/3 channel convention.")

    if "new_size" not in conf and not {"new_size_a", "new_size_b"}.issubset(conf):
        warnings.append("config has neither new_size nor both new_size_a/new_size_b; data/inference transforms may fail.")
    if conf.get("vgg_w", 0):
        warnings.append("vgg_w is positive; trainer construction can trigger VGG file creation/download/conversion side effects.")
    if trainer == "UNIT" and missing_top:
        warnings.append("bundled MUNIT configs are not UNIT-ready unless recon_kl_w and recon_kl_cyc_w are added.")

    return result, errors, warnings


def human_report(report: Dict[str, Any]) -> str:
    lines: List[str] = []
    lines.append("MUNIT static architecture inspection")
    if report.get("source"):
        source = report["source"]
        lines.append("\nSource files checked: " + ", ".join(source.get("files_checked", [])))
        lines.append("Expected class signatures:")
        for cls in sorted(source.get("classes", {})):
            args = source["classes"][cls]["init_args"]
            lines.append(f"  - {cls}({', '.join(args)})")
        if source.get("markers"):
            lines.append("Legacy/porting markers:")
            for marker, files in sorted(source["markers"].items()):
                summary = ", ".join(f"{name}:{count}" for name, count in sorted(files.items()))
                lines.append(f"  - {marker}: {summary}")
    if report.get("config"):
        config = report["config"]
        lines.append("\nConfig inspection:")
        lines.append(f"  - parser: {config.get('parser')}")
        lines.append(f"  - top keys: {', '.join(config.get('top_keys', []))}")
        gen = config.get("gen") or {}
        dis = config.get("dis") or {}
        if gen:
            lines.append("  - gen: " + ", ".join(f"{k}={gen[k]}" for k in sorted(gen)))
        if dis:
            lines.append("  - dis: " + ", ".join(f"{k}={dis[k]}" for k in sorted(dis)))
    if report.get("warnings"):
        lines.append("\nWarnings:")
        lines.extend(f"  - {item}" for item in report["warnings"])
    if report.get("errors"):
        lines.append("\nErrors:")
        lines.extend(f"  - {item}" for item in report["errors"])
    if not report.get("errors"):
        lines.append("\nResult: no blocking static architecture errors found.")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root)
    warnings: List[str] = []
    errors: List[str] = []
    report: Dict[str, Any] = {"trainer": args.trainer, "warnings": warnings, "errors": errors}

    if not args.no_source:
        source, source_errors, source_warnings = inspect_source(repo_root)
        report["source"] = source
        errors.extend(source_errors)
        warnings.extend(source_warnings)

    if args.config:
        config_path = Path(args.config)
        if not config_path.is_absolute():
            config_path = repo_root / config_path
        if not config_path.exists():
            errors.append(f"config not found: {args.config}")
        else:
            config, config_errors, config_warnings = validate_config(config_path, args.trainer)
            config["path"] = args.config
            report["config"] = config
            errors.extend(config_errors)
            warnings.extend(config_warnings)

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(human_report(report))

    if errors:
        return 2
    if args.strict and warnings:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
