#!/usr/bin/env python3
"""Inspect OpenFold API signatures, config presets, and optional backends safely.

This helper imports OpenFold modules and builds config presets only. It does not
instantiate AlphaFold, load weights, run inference/training, download assets,
compile engines, or write output files unless the caller redirects stdout.

Model-level imports are allowed to fail. In some environments OpenFold's model
package requires compiled extensions such as attn_core_inplace_cuda; this script
reports those failures while still inspecting safe config/parser/protein modules.
"""

from __future__ import annotations

import argparse
import contextlib
import importlib
import importlib.metadata
import inspect
import io
import json
import sys
from pathlib import Path
from typing import Any

PRESETS = (
    "model_1",
    "model_1_ptm",
    "model_1_multimer_v3",
    "seq_model_esm1b_ptm",
    "initial_training",
    "finetuning",
)

SAFE_REQUIRED_IMPORTS = (
    "openfold",
    "openfold.config",
    "openfold.data.parsers",
    "openfold.data.mmcif_parsing",
    "openfold.np.protein",
)

MODEL_IMPORTS = (
    "openfold.model.model",
    "openfold.model.primitives",
    "openfold.utils.import_weights",
    "openfold.utils.validation_metrics",
    "openfold.utils.script_utils",
    "attn_core_inplace_cuda",
)

OPTIONAL_BACKENDS = (
    "deepspeed",
    "deepspeed.ops.deepspeed4science",
    "cuequivariance_torch",
    "flash_attn",
    "tensorrt",
)

SIGNATURE_OBJECTS = (
    ("openfold.config", "model_config"),
    ("openfold.config", "enforce_config_constraints"),
    ("openfold.model.model", "AlphaFold"),
    ("openfold.model.model", "AlphaFold.forward"),
    ("openfold.utils.import_weights", "import_jax_weights_"),
    ("openfold.utils.import_weights", "import_openfold_weights_"),
    ("openfold.np.protein", "from_prediction"),
    ("openfold.np.protein", "to_pdb"),
    ("openfold.np.protein", "to_modelcif"),
    ("openfold.utils.validation_metrics", "drmsd"),
    ("openfold.utils.validation_metrics", "drmsd_np"),
    ("openfold.utils.validation_metrics", "gdt"),
    ("openfold.utils.validation_metrics", "gdt_ts"),
    ("openfold.utils.validation_metrics", "gdt_ha"),
    ("openfold.utils.script_utils", "load_models_from_command_line"),
    ("openfold.utils.script_utils", "run_model"),
    ("openfold.utils.script_utils", "prep_output"),
    ("openfold.utils.script_utils", "relax_protein"),
)


def add_package_root(package_root: str | None) -> None:
    root = str(Path(package_root).expanduser().resolve()) if package_root else str(Path.cwd())
    if root not in sys.path:
        sys.path.insert(0, root)


def package_version() -> dict[str, Any]:
    for distribution_name in ("openfold", "openfold-wheel"):
        try:
            return {"ok": True, "distribution": distribution_name, "version": importlib.metadata.version(distribution_name)}
        except importlib.metadata.PackageNotFoundError:
            continue
    return {"ok": False, "error": "OpenFold distribution metadata not found"}


def import_status(module_name: str) -> dict[str, Any]:
    try:
        module = importlib.import_module(module_name)
    except Exception as exc:  # depends on local optional deps
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
    return {"ok": True, "module": getattr(module, "__name__", module_name)}


def resolve_attr(module: Any, dotted_name: str) -> Any:
    current = module
    for part in dotted_name.split("."):
        current = getattr(current, part)
    return current


def signature_report(module_name: str, dotted_name: str) -> dict[str, Any]:
    try:
        module = importlib.import_module(module_name)
        obj = resolve_attr(module, dotted_name)
        if inspect.isclass(obj):
            target = obj.__init__
            display_name = f"{module_name}.{dotted_name}.__init__"
        else:
            target = obj
            display_name = f"{module_name}.{dotted_name}"
        return {"ok": True, "name": display_name, "signature": str(inspect.signature(target))}
    except Exception as exc:  # depends on local install
        return {"ok": False, "name": f"{module_name}.{dotted_name}", "error": f"{type(exc).__name__}: {exc}"}


def get_path(config: Any, dotted_path: str, default: Any = None) -> Any:
    current = config
    for part in dotted_path.split("."):
        try:
            current = current[part]
        except Exception:
            try:
                current = getattr(current, part)
            except Exception:
                return default
    return current


def summarize_preset(name: str, train: bool | None = None) -> dict[str, Any]:
    try:
        from openfold.config import model_config

        kwargs: dict[str, Any] = {}
        if train is not None:
            kwargs["train"] = train
        config = model_config(name, **kwargs)
    except Exception as exc:  # depends on optional deps and preset validity
        return {"ok": False, "preset": name, "error": f"{type(exc).__name__}: {exc}"}

    return {
        "ok": True,
        "preset": name,
        "train_requested": train,
        "precision": get_path(config, "precision"),
        "is_multimer": bool(get_path(config, "globals.is_multimer", False)),
        "seqemb_mode_enabled": bool(get_path(config, "globals.seqemb_mode_enabled", False)),
        "template_enabled": bool(get_path(config, "model.template.enabled", False)),
        "tm_head_enabled": bool(get_path(config, "model.heads.tm.enabled", False)),
        "predict_fixed_size": bool(get_path(config, "data.predict.fixed_size", False)),
        "predict_max_msa_clusters": get_path(config, "data.predict.max_msa_clusters"),
        "predict_max_extra_msa": get_path(config, "data.predict.max_extra_msa"),
        "use_templates": bool(get_path(config, "data.common.use_templates", False)),
        "trt_mode": get_path(config, "trt.mode"),
        "trt_max_sequence_len": get_path(config, "trt.max_sequence_len"),
    }


def validation_metric_names() -> list[str]:
    try:
        from openfold.utils import validation_metrics
    except Exception:
        return []
    return [
        name
        for name in ("drmsd", "drmsd_np", "gdt", "gdt_ha", "gdt_ts")
        if callable(getattr(validation_metrics, name, None))
    ]


def collect_report(args: argparse.Namespace) -> dict[str, Any]:
    preset_summaries = []
    for preset in args.presets:
        train = True if preset in {"initial_training", "finetuning"} else None
        preset_summaries.append(summarize_preset(preset, train=train))

    safe_imports = {name: import_status(name) for name in SAFE_REQUIRED_IMPORTS}
    model_imports = {name: import_status(name) for name in MODEL_IMPORTS}
    return {
        "package_metadata": package_version(),
        "safe_imports": safe_imports,
        "model_and_extension_imports": model_imports,
        "optional_backends": {name: import_status(name) for name in OPTIONAL_BACKENDS},
        "signatures": [signature_report(module, attr) for module, attr in SIGNATURE_OBJECTS],
        "presets": preset_summaries,
        "validation_metrics": validation_metric_names(),
        "summary": {
            "safe_required_imports_ok": all(status["ok"] for status in safe_imports.values()),
            "model_imports_ok": all(status["ok"] for status in model_imports.values()),
        },
    }


def print_text(report: dict[str, Any]) -> None:
    metadata = report["package_metadata"]
    if metadata["ok"]:
        print(f"OpenFold API inspection: version {metadata['version']}")
    else:
        print("OpenFold API inspection: package metadata unavailable")

    print("\nSafe imports:")
    for name, status in report["safe_imports"].items():
        marker = "ok" if status["ok"] else "missing/error"
        print(f"  {name}: {marker}")
        if not status["ok"]:
            print(f"    {status['error']}")

    print("\nModel and extension imports:")
    for name, status in report["model_and_extension_imports"].items():
        marker = "ok" if status["ok"] else "missing/error"
        print(f"  {name}: {marker}")
        if not status["ok"]:
            print(f"    {status['error']}")

    print("\nOptional backends:")
    for name, status in report["optional_backends"].items():
        marker = "available" if status["ok"] else "unavailable"
        print(f"  {name}: {marker}")

    print("\nSignatures:")
    for item in report["signatures"]:
        if item["ok"]:
            print(f"  {item['name']}{item['signature']}")
        else:
            print(f"  {item['name']}: {item['error']}")

    print("\nPreset summaries:")
    for item in report["presets"]:
        if not item["ok"]:
            print(f"  {item['preset']}: {item['error']}")
            continue
        fields = ", ".join(
            f"{key}={item[key]!r}"
            for key in ("is_multimer", "seqemb_mode_enabled", "template_enabled", "tm_head_enabled", "precision")
        )
        print(f"  {item['preset']}: {fields}")

    metric_names = report["validation_metrics"]
    print("\nValidation metrics: " + (", ".join(metric_names) if metric_names else "unavailable"))


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    parser.add_argument(
        "--presets",
        nargs="+",
        default=list(PRESETS),
        help="preset names to summarize without model execution",
    )
    parser.add_argument(
        "--package-root",
        default=None,
        help="optional OpenFold checkout/package root to prepend to sys.path",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    add_package_root(args.package_root)
    if args.json:
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            report = collect_report(args)
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        report = collect_report(args)
        print_text(report)
    return 0 if report["summary"]["safe_required_imports_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
