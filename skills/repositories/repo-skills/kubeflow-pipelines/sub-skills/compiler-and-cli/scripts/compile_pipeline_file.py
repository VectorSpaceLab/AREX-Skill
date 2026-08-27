#!/usr/bin/env python3
"""Compile a KFP pipeline/component file with an installed KFP package.

This helper intentionally avoids importing from a Kubeflow Pipelines source
checkout. The default backend shells out safely to the installed public ``kfp``
CLI. The optional API backend imports the target file and calls
``kfp.compiler.Compiler`` from the installed package.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import shlex
import shutil
import subprocess
import sys
from pathlib import Path
from types import ModuleType
from typing import Any, Dict, Iterable, Optional


class UserFacingError(RuntimeError):
    """Error whose message is safe to print without a traceback."""


def _existing_file(value: str) -> Path:
    path = Path(value).expanduser()
    if not path.is_file():
        raise argparse.ArgumentTypeError(f"file does not exist: {value}")
    return path.resolve()


def _output_path(value: str) -> Path:
    path = Path(value).expanduser()
    if path.suffix not in {".yaml", ".yml"}:
        raise argparse.ArgumentTypeError(
            "output must end with .yaml or .yml for supported KFP compilation")
    return path.resolve()


def _parse_args(argv: Optional[Iterable[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Compile a KFP Python pipeline/component file to PipelineSpec YAML "
            "or Kubernetes manifest YAML using the installed kfp package."))
    parser.add_argument("--py", required=True, type=_existing_file,
                        help="Python file containing a decorated pipeline/component.")
    parser.add_argument("--output", required=True, type=_output_path,
                        help="YAML file to write.")
    parser.add_argument("--function", dest="function_name", default=None,
                        help="Pipeline/component object name when the file has multiple candidates.")
    parser.add_argument("--pipeline-parameters", default=None,
                        help="JSON object of input default overrides.")
    parser.add_argument("--disable-type-check", action="store_true",
                        help="Disable KFP compile-time interface type checking.")
    parser.add_argument("--disable-execution-caching-by-default",
                        action="store_true",
                        help="Disable default execution caching for compiled tasks.")
    parser.add_argument("--kubernetes-manifest-format", action="store_true",
                        help="Write Kubernetes PipelineVersion/Pipeline manifest YAML.")
    parser.add_argument("--pipeline-name", default=None,
                        help="Manifest Pipeline resource name; used only with manifest format.")
    parser.add_argument("--pipeline-display-name", default=None,
                        help="Manifest Pipeline display name; used only with manifest format.")
    parser.add_argument("--pipeline-version-name", default=None,
                        help="Manifest PipelineVersion resource name; used only with manifest format.")
    parser.add_argument("--pipeline-version-display-name", default=None,
                        help="Manifest PipelineVersion display name; used only with manifest format.")
    parser.add_argument("--namespace", default=None,
                        help="Kubernetes namespace for manifest resources.")
    parser.add_argument("--include-pipeline-manifest", action="store_true",
                        help="Include Pipeline manifest with PipelineVersion manifest.")
    parser.add_argument("--backend", choices=("cli", "api"), default="cli",
                        help="Use installed public kfp console CLI or Compiler API. Default: cli.")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print the CLI command without compiling; only valid with --backend cli.")
    args = parser.parse_args(argv)
    if args.dry_run and args.backend != "cli":
        parser.error("--dry-run is only supported with --backend cli")
    return args


def _parse_pipeline_parameters(raw: Optional[str]) -> Optional[Dict[str, Any]]:
    if raw is None:
        return None
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise UserFacingError(
            f"failed to parse --pipeline-parameters as JSON: {exc.msg} "
            f"at line {exc.lineno} column {exc.colno}") from exc
    if not isinstance(parsed, dict):
        raise UserFacingError(
            "--pipeline-parameters must parse to a JSON object/dict")
    return parsed


def _manifest_options_provided(args: argparse.Namespace) -> bool:
    return any([
        args.pipeline_name,
        args.pipeline_display_name,
        args.pipeline_version_name,
        args.pipeline_version_display_name,
        args.namespace,
        args.include_pipeline_manifest,
    ])


def _kfp_console_command() -> list[str]:
    sibling = Path(sys.executable).with_name("kfp")
    if sibling.is_file():
        return [str(sibling)]
    on_path = shutil.which("kfp")
    if on_path:
        return [on_path]
    return [sys.executable, "-c", "from kfp.cli.__main__ import main; main()"]


def _build_cli_command(args: argparse.Namespace,
                       parameters: Optional[Dict[str, Any]]) -> list[str]:
    cmd = _kfp_console_command() + [
        "dsl",
        "compile",
        "--py",
        str(args.py),
        "--output",
        str(args.output),
    ]
    if args.function_name:
        cmd.extend(["--function", args.function_name])
    if parameters is not None:
        cmd.extend([
            "--pipeline-parameters",
            json.dumps(parameters, separators=(",", ":"), sort_keys=True),
        ])
    if args.disable_type_check:
        cmd.append("--disable-type-check")
    if args.disable_execution_caching_by_default:
        cmd.append("--disable-execution-caching-by-default")
    if args.kubernetes_manifest_format:
        cmd.append("--kubernetes-manifest-format")
    for flag, value in [
        ("--pipeline-name", args.pipeline_name),
        ("--pipeline-display-name", args.pipeline_display_name),
        ("--pipeline-version-name", args.pipeline_version_name),
        ("--pipeline-version-display-name", args.pipeline_version_display_name),
        ("--namespace", args.namespace),
    ]:
        if value:
            cmd.extend([flag, value])
    if args.include_pipeline_manifest:
        cmd.append("--include-pipeline-manifest")
    return cmd


def _run_cli(args: argparse.Namespace, parameters: Optional[Dict[str, Any]]) -> int:
    cmd = _build_cli_command(args, parameters)
    if args.dry_run:
        print(" ".join(shlex.quote(part) for part in cmd))
        return 0
    args.output.parent.mkdir(parents=True, exist_ok=True)
    completed = subprocess.run(cmd, check=False)
    return completed.returncode


def _load_module_from_file(path: Path) -> ModuleType:
    module_name = f"_kfp_compile_target_{abs(hash(str(path)))}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise UserFacingError(f"could not import Python file: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(path.parent))
    try:
        spec.loader.exec_module(module)
    finally:
        del sys.path[0]
    return module


def _is_compilable_kfp_object(obj: Any) -> bool:
    return hasattr(obj, "pipeline_spec") and hasattr(obj, "name")


def _select_pipeline_or_component(module: ModuleType,
                                  function_name: Optional[str]) -> Any:
    if function_name:
        if not hasattr(module, function_name):
            raise UserFacingError(
                f'pipeline function or component "{function_name}" not found in {module.__name__}')
        selected = getattr(module, function_name)
        if not _is_compilable_kfp_object(selected):
            raise UserFacingError(
                f'object "{function_name}" does not look like a decorated KFP pipeline/component')
        return selected

    candidates = []
    for attr_name in dir(module):
        if attr_name.startswith("_"):
            continue
        obj = getattr(module, attr_name)
        if _is_compilable_kfp_object(obj):
            candidates.append((attr_name, getattr(obj, "name", attr_name)))

    if len(candidates) != 1:
        pretty = ", ".join(f"{attr}({name})" for attr, name in candidates) or "none"
        raise UserFacingError(
            "expected exactly one decorated KFP pipeline/component in the file; "
            f"found {len(candidates)}: {pretty}. Pass --function.")
    return getattr(module, candidates[0][0])


def _run_api(args: argparse.Namespace, parameters: Optional[Dict[str, Any]]) -> int:
    from kfp import compiler
    from kfp.compiler.compiler_utils import KubernetesManifestOptions

    module = _load_module_from_file(args.py)
    pipeline_func = _select_pipeline_or_component(module, args.function_name)

    kubernetes_manifest_options = None
    if args.kubernetes_manifest_format:
        kubernetes_manifest_options = KubernetesManifestOptions(
            pipeline_name=args.pipeline_name,
            pipeline_display_name=args.pipeline_display_name,
            pipeline_version_name=args.pipeline_version_name,
            pipeline_version_display_name=args.pipeline_version_display_name,
            namespace=args.namespace,
            include_pipeline_manifest=args.include_pipeline_manifest,
        )
    elif _manifest_options_provided(args):
        print(
            "Warning: Kubernetes manifest options were provided but "
            "--kubernetes-manifest-format was not set. These options will be ignored.",
            file=sys.stderr,
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    compiler.Compiler().compile(
        pipeline_func=pipeline_func,
        package_path=str(args.output),
        pipeline_parameters=parameters or {},
        type_check=not args.disable_type_check,
        kubernetes_manifest_options=kubernetes_manifest_options,
        kubernetes_manifest_format=args.kubernetes_manifest_format,
    )
    print(f"Pipeline code was successfully compiled with the output saved to {args.output}")
    return 0


def main(argv: Optional[Iterable[str]] = None) -> int:
    args = _parse_args(argv)
    try:
        parameters = _parse_pipeline_parameters(args.pipeline_parameters)
        if args.backend == "cli":
            return _run_cli(args, parameters)
        return _run_api(args, parameters)
    except UserFacingError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
