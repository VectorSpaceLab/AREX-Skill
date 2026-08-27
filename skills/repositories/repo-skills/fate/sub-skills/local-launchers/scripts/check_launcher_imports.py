#!/usr/bin/env python3
"""Safe import/signature helper for FATE local launcher authoring.

This helper is intentionally cheap by default: it imports modules/classes,
prints package and backend summaries, and inspects signatures. It does not call
`launch()` or run training unless the user supplies both `--run-callable` and
`--yes-run-training`.

Examples:
  python check_launcher_imports.py --check-standard
  python check_launcher_imports.py --module fate.ml.glm.hetero.sshe --object SSHELogisticRegression
  python check_launcher_imports.py --module-path ./my_launcher.py --object run --expect-callable
  python check_launcher_imports.py --proc some.module:SomeMPCClass --expect-subclass-mpc
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
import importlib.util
import inspect
import json
import os
import sys
from pathlib import Path
from types import ModuleType
from typing import Any, Iterable


STANDARD_OBJECTS = [
    ("fate.arch.context", "create_context"),
    ("fate.arch", "Context"),
    ("fate.arch", "CipherKit"),
    ("fate.arch.dataframe", "CSVReader"),
    ("fate.arch.dataframe", "PandasReader"),
    ("fate.arch.dataframe", "TableReader"),
    ("fate.arch.launchers.argparser", "HfArgumentParser"),
    ("fate.arch.launchers.multiprocess_launcher", "LauncherArguments"),
    ("fate.arch.launchers.multiprocess_launcher", "MultiProcessLauncher"),
    ("fate.arch.launchers.multiprocess_launcher", "launch"),
    ("fate.ml.glm.hetero.sshe", "SSHELogisticRegression"),
    ("fate.ml.glm.hetero.sshe", "SSHELinearRegression"),
    ("fate.ml.ensemble.algo.secureboost.hetero.guest", "HeteroSecureBoostGuest"),
    ("fate.ml.ensemble.algo.secureboost.hetero.host", "HeteroSecureBoostHost"),
    ("fate.ml.nn.hetero.hetero_nn", "HeteroNNTrainerGuest"),
    ("fate.ml.nn.hetero.hetero_nn", "HeteroNNTrainerHost"),
    ("fate.ml.nn.hetero.hetero_nn", "TrainingArguments"),
    ("fate.ml.nn.homo.fedavg", "FedAVGArguments"),
    ("fate.ml.nn.homo.fedavg", "FedAVGClient"),
    ("fate.ml.nn.homo.fedavg", "FedAVGServer"),
    ("fate.ml.nn.model_zoo.hetero_nn_model", "HeteroNNModelGuest"),
    ("fate.ml.nn.model_zoo.hetero_nn_model", "HeteroNNModelHost"),
    ("fate.ml.nn.model_zoo.hetero_nn_model", "SSHEArgument"),
    ("fate.ml.nn.model_zoo.hetero_nn_model", "FedPassArgument"),
    ("fate.ml.preprocessing.feature_scale", "FeatureScale"),
    ("fate.ml.preprocessing.union", "Union"),
    ("fate.ml.statistics.pearson_correlation", "PearsonCorrelation"),
]

OPTIONAL_OBJECTS = [
    ("fate.ml.mpc", "MPCModule"),
]


def _json_default(value: Any) -> str:
    return repr(value)


def package_summary() -> dict[str, Any]:
    summary: dict[str, Any] = {"python": sys.version.split()[0], "packages": {}, "torch": {}}
    for dist in ["pyfate", "fate_utils", "fate_client", "fate_flow", "setuptools"]:
        try:
            summary["packages"][dist] = metadata.version(dist)
        except metadata.PackageNotFoundError:
            summary["packages"][dist] = None
    try:
        import fate  # type: ignore

        summary["fate_import"] = "ok"
        summary["fate_version_attr"] = getattr(fate, "__version__", None)
    except Exception as exc:  # pragma: no cover - diagnostic path
        summary["fate_import"] = f"{type(exc).__name__}: {exc}"
    try:
        import fate_utils  # type: ignore  # noqa: F401

        summary["fate_utils_import"] = "ok"
    except Exception as exc:  # pragma: no cover - diagnostic path
        summary["fate_utils_import"] = f"{type(exc).__name__}: {exc}"
    try:
        import pkg_resources  # type: ignore  # noqa: F401

        summary["pkg_resources_import"] = "ok"
    except Exception as exc:  # pragma: no cover - diagnostic path
        summary["pkg_resources_import"] = f"{type(exc).__name__}: {exc}"
    try:
        import torch  # type: ignore

        summary["torch"] = {
            "version": getattr(torch, "__version__", None),
            "cuda_available": bool(torch.cuda.is_available()),
        }
    except Exception as exc:  # pragma: no cover - diagnostic path
        summary["torch"] = {"import_error": f"{type(exc).__name__}: {exc}"}
    return summary


def import_module_by_path(path: str) -> ModuleType:
    module_path = Path(path).expanduser().resolve()
    if not module_path.exists():
        raise FileNotFoundError(f"module path does not exist: {module_path}")
    if module_path.suffix != ".py":
        raise ValueError(f"module path must be a .py file: {module_path}")
    module_name = f"_fate_launcher_check_{module_path.stem}_{abs(hash(str(module_path))) & 0xFFFF:x}"
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot create import spec for {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def import_module(module_name: str | None, module_path: str | None) -> ModuleType | None:
    if module_path:
        return import_module_by_path(module_path)
    if module_name:
        return importlib.import_module(module_name)
    return None


def split_proc(proc: str) -> tuple[str, str]:
    if ":" not in proc:
        raise ValueError("--proc must use module:Class form")
    module_name, object_name = proc.split(":", 1)
    if not module_name or not object_name:
        raise ValueError("--proc must contain both module and class names")
    return module_name, object_name


def signature_of(obj: Any) -> str | None:
    try:
        return str(inspect.signature(obj))
    except (TypeError, ValueError):
        return None


def object_report(module_name: str, object_name: str, *, optional: bool = False) -> dict[str, Any]:
    report: dict[str, Any] = {"module": module_name, "object": object_name, "optional": optional}
    try:
        module = importlib.import_module(module_name)
        report["module_import"] = "ok"
        obj = getattr(module, object_name)
        report["object_found"] = True
        report["type"] = type(obj).__name__
        sig = signature_of(obj)
        if sig is not None:
            report["signature"] = sig
    except Exception as exc:
        report["error"] = f"{type(exc).__name__}: {exc}"
    return report


def resolve_object(module: ModuleType | None, object_name: str | None, proc: str | None) -> tuple[Any | None, str | None]:
    if proc:
        module_name, cls_name = split_proc(proc)
        mod = importlib.import_module(module_name)
        return getattr(mod, cls_name), f"{module_name}:{cls_name}"
    if module is not None and object_name:
        return getattr(module, object_name), f"{module.__name__}.{object_name}"
    return None, None


def check_subclass_mpc(obj: Any) -> dict[str, Any]:
    report: dict[str, Any] = {"expect_subclass_mpc": True}
    try:
        mpc_module = importlib.import_module("fate.ml.mpc")
        mpc_base = getattr(mpc_module, "MPCModule")
    except Exception as exc:
        report["mpc_base_import"] = f"{type(exc).__name__}: {exc}"
        report["is_subclass"] = None
        return report
    try:
        report["mpc_base_import"] = "ok"
        report["is_subclass"] = bool(inspect.isclass(obj) and issubclass(obj, mpc_base))
    except Exception as exc:  # pragma: no cover - defensive diagnostic path
        report["is_subclass_error"] = f"{type(exc).__name__}: {exc}"
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Safely import/check FATE local launcher modules and signatures without training by default.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--check-standard", action="store_true", help="Import the standard local launcher API set.")
    parser.add_argument("--module", help="Import a Python module by dotted name, e.g. fate.ml.glm.hetero.sshe.")
    parser.add_argument("--module-path", help="Import a user launcher .py file by path for syntax/import checks.")
    parser.add_argument("--object", help="Object name to resolve inside --module or --module-path.")
    parser.add_argument("--proc", help="SMPC-style target in module:Class form.")
    parser.add_argument("--expect-callable", action="store_true", help="Fail if the resolved object is not callable.")
    parser.add_argument("--expect-subclass-mpc", action="store_true", help="Check whether --proc/--object is an MPCModule subclass when MPCModule is available.")
    parser.add_argument("--prepend-path", action="append", default=[], help="Prepend an extra import path. Use for a user's own launcher directory, not as a hidden dependency.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON instead of text.")
    parser.add_argument("--run-callable", help="HEAVY: name of callable to execute with fate.arch.launchers.launch. Requires --yes-run-training.")
    parser.add_argument("--yes-run-training", action="store_true", help="Required confirmation for --run-callable. This may spawn processes and train models.")
    parser.add_argument("--party", action="append", dest="parties", default=[], help="Party for heavy run, e.g. guest:9999. Repeat for each party.")
    parser.add_argument("--log-level", default="INFO", help="Log level passed to launch() for heavy runs.")
    parser.add_argument("--data-dir", help="Data directory passed to launch() for heavy runs.")
    return parser


def print_text(report: dict[str, Any]) -> None:
    print("FATE local launcher import check")
    print("=" * 34)
    print("Environment summary:")
    print(json.dumps(report["environment"], indent=2, sort_keys=True, default=_json_default))
    if report.get("standard_checks"):
        print("\nStandard API checks:")
        for item in report["standard_checks"]:
            status = "ok" if item.get("object_found") else item.get("error", "missing")
            sig = f" {item['signature']}" if item.get("signature") else ""
            optional = " (optional)" if item.get("optional") else ""
            print(f"- {item['module']}:{item['object']}{optional}: {status}{sig}")
    if report.get("target"):
        print("\nTarget:")
        print(json.dumps(report["target"], indent=2, sort_keys=True, default=_json_default))
    if report.get("heavy_run"):
        print("\nHeavy run:")
        print(json.dumps(report["heavy_run"], indent=2, sort_keys=True, default=_json_default))


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args, unknown = parser.parse_known_args(argv)

    for p in reversed(args.prepend_path):
        sys.path.insert(0, str(Path(p).expanduser().resolve()))

    report: dict[str, Any] = {"environment": package_summary()}
    exit_code = 0

    if args.check_standard:
        standard = [object_report(module, obj) for module, obj in STANDARD_OBJECTS]
        optional = [object_report(module, obj, optional=True) for module, obj in OPTIONAL_OBJECTS]
        report["standard_checks"] = standard + optional
        for item in standard:
            if item.get("error"):
                exit_code = 1

    module = None
    try:
        module = import_module(args.module, args.module_path)
        if module is not None:
            report.setdefault("target", {})["module_import"] = "ok"
            report["target"]["module_name"] = module.__name__
    except Exception as exc:
        report.setdefault("target", {})["module_import"] = f"{type(exc).__name__}: {exc}"
        exit_code = 1

    obj = None
    obj_label = None
    if args.object or args.proc:
        try:
            obj, obj_label = resolve_object(module, args.object, args.proc)
            target = report.setdefault("target", {})
            target["object"] = obj_label
            target["object_type"] = type(obj).__name__
            sig = signature_of(obj)
            if sig is not None:
                target["signature"] = sig
            if args.expect_callable:
                target["callable"] = callable(obj)
                if not callable(obj):
                    exit_code = 1
            if args.expect_subclass_mpc:
                target.update(check_subclass_mpc(obj))
                if target.get("is_subclass") is False:
                    exit_code = 1
        except Exception as exc:
            report.setdefault("target", {})["object_error"] = f"{type(exc).__name__}: {exc}"
            exit_code = 1

    if args.run_callable:
        heavy = report.setdefault("heavy_run", {})
        heavy["requested"] = True
        heavy["warning"] = "This path calls fate.arch.launchers.launch and may spawn parties and train models."
        if not args.yes_run_training:
            heavy["status"] = "refused: pass --yes-run-training to confirm heavy execution"
            exit_code = 2
        else:
            if module is None and not args.module and not args.module_path:
                heavy["status"] = "refused: --run-callable requires --module or --module-path"
                exit_code = 2
            else:
                try:
                    run_obj = getattr(module, args.run_callable) if module is not None else None
                    if not callable(run_obj):
                        raise TypeError(f"{args.run_callable} is not callable")
                    parties = args.parties or ["guest:9999", "host:10000"]
                    heavy["status"] = "starting"
                    heavy["callable"] = f"{module.__name__}.{args.run_callable}"
                    heavy["parties"] = parties
                    if not args.json:
                        print_text(report)
                        print("\n*** ENTERING EXPLICIT HEAVY TRAINING MODE ***", flush=True)
                    # Preserve only user-supplied unknown args for the launched callable's own parser.
                    sys.argv = [sys.argv[0], *unknown]
                    from fate.arch.launchers.multiprocess_launcher import launch

                    launch(run_obj, parties=parties, log_level=args.log_level, data_dir=args.data_dir)
                    return 0  # launch normally exits; this is for unusual non-exit behavior.
                except SystemExit as exc:
                    raise exc
                except Exception as exc:
                    heavy["status"] = f"failed before launch: {type(exc).__name__}: {exc}"
                    exit_code = 1

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True, default=_json_default))
    else:
        print_text(report)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
