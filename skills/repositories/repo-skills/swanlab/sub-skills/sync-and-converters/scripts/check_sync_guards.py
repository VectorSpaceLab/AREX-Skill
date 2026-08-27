#!/usr/bin/env python3
"""No-network guard checks for SwanLab sync and converter guidance.

The checks deliberately avoid importing ``swanlab`` top-level or contacting any
service. They locate a SwanLab package/source tree, parse selected modules with
``ast``, and exercise local path-guard behavior on temporary files.
"""

from __future__ import annotations

import argparse
import ast
import importlib.util
import os
import sys
import tempfile
from pathlib import Path
from typing import Iterable


class CheckError(RuntimeError):
    """Raised for a failed guard assertion with a clear message."""


def _candidate_package_roots(user_root: str | None) -> Iterable[Path]:
    if user_root:
        p = Path(user_root).expanduser().resolve()
        yield p / "swanlab"
        yield p

    cwd = Path.cwd().resolve()
    yield cwd / "swanlab"
    yield cwd

    here = Path(__file__).resolve()
    for parent in here.parents:
        yield parent / "swanlab"

    spec = importlib.util.find_spec("swanlab")
    if spec and spec.submodule_search_locations:
        for loc in spec.submodule_search_locations:
            yield Path(loc).resolve()


def locate_swanlab_root(user_root: str | None) -> Path:
    seen: set[Path] = set()
    for candidate in _candidate_package_roots(user_root):
        candidate = candidate.resolve()
        if candidate in seen:
            continue
        seen.add(candidate)
        if candidate.name == "swanlab" and (candidate / "__init__.py").is_file():
            return candidate
    raise CheckError("Cannot locate a SwanLab package. Install swanlab or pass --package-root PATH.")


def read_source(pkg_root: Path, rel: str) -> str:
    path = pkg_root / rel
    if not path.is_file():
        raise CheckError(f"Expected SwanLab source module is missing: {rel}")
    return path.read_text(encoding="utf-8")


def parse_source(text: str, rel: str) -> ast.Module:
    try:
        return ast.parse(text)
    except SyntaxError as exc:
        raise CheckError(f"Cannot parse {rel}: {exc}") from exc


def find_function(tree: ast.Module, name: str, class_name: str | None = None) -> ast.FunctionDef:
    body: Iterable[ast.stmt]
    if class_name is None:
        body = tree.body
    else:
        cls = next((node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == class_name), None)
        if cls is None:
            raise CheckError(f"Missing class {class_name}")
        body = cls.body
    for node in body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    where = f"{class_name}." if class_name else ""
    raise CheckError(f"Missing function {where}{name}")


def arg_names(fn: ast.FunctionDef) -> list[str]:
    return [arg.arg for arg in [*fn.args.posonlyargs, *fn.args.args, *fn.args.kwonlyargs]]


def require_args(tree: ast.Module, name: str, required: list[str], class_name: str | None = None) -> None:
    fn = find_function(tree, name, class_name=class_name)
    names = arg_names(fn)
    missing = [arg for arg in required if arg not in names]
    if missing:
        where = f"{class_name}." if class_name else ""
        raise CheckError(f"{where}{name} is missing expected arguments: {missing}; saw {names}")


def require_snippets(rel: str, text: str, snippets: list[str]) -> None:
    missing = [snippet for snippet in snippets if snippet not in text]
    if missing:
        raise CheckError(f"{rel} is missing expected implementation guards: {missing}")


def validate_run_dir_like_sync(path: Path) -> Path:
    if not path.exists():
        raise CheckError(f"run directory does not exist: {path}")
    if not path.is_dir():
        raise CheckError(f"run path is not a directory: {path}")
    if not os.access(path, os.R_OK):
        raise CheckError(f"run directory is not readable: {path}")
    return path.resolve()


def guarded_join(base_dir: Path, file_path: str) -> Path | None:
    if not file_path:
        return None
    base = base_dir.resolve()
    joined = (base / file_path).resolve()
    try:
        joined.relative_to(base)
    except ValueError:
        return None
    return joined


def expect_failure(label: str, fn, fragment: str) -> None:
    try:
        fn()
    except CheckError as exc:
        if fragment not in str(exc):
            raise CheckError(f"{label} failed unclearly: {exc}") from exc
        print(f"OK: {label} failed clearly: {exc}")
    else:
        raise CheckError(f"{label} unexpectedly passed")


def run_path_guard_self_tests() -> None:
    with tempfile.TemporaryDirectory(prefix="swanlab-sync-guards-") as tmp:
        root = Path(tmp)
        missing = root / "missing-run"
        file_path = root / "run-file.swanlab"
        file_path.write_text("not a directory", encoding="utf-8")
        run_dir = root / "run-dir"
        run_dir.mkdir()

        expect_failure("missing temporary run directory", lambda: validate_run_dir_like_sync(missing), "does not exist")
        expect_failure("file passed as run directory", lambda: validate_run_dir_like_sync(file_path), "not a directory")
        validated = validate_run_dir_like_sync(run_dir)
        if validated != run_dir.resolve():
            raise CheckError("readable directory did not resolve as expected")
        print(f"OK: readable temporary run directory validates: {validated}")

        inside = guarded_join(run_dir, "files/media.png")
        outside = guarded_join(run_dir, "../secret.txt")
        absolute_outside = guarded_join(run_dir, str(root / "secret.txt"))
        if inside is None or outside is not None or absolute_outside is not None:
            raise CheckError("W&B-style media path traversal guard failed")
        print("OK: W&B-style media path guard accepts inside paths and rejects traversal")


def assert_source_guards(pkg_root: Path) -> None:
    modules = {
        "sdk/cmd/sync.py": read_source(pkg_root, "sdk/cmd/sync.py"),
        "cli/sync/__init__.py": read_source(pkg_root, "cli/sync/__init__.py"),
        "cli/converter/__init__.py": read_source(pkg_root, "cli/converter/__init__.py"),
        "converter/__init__.py": read_source(pkg_root, "converter/__init__.py"),
        "converter/base.py": read_source(pkg_root, "converter/base.py"),
        "converter/helper.py": read_source(pkg_root, "converter/helper.py"),
        "converter/wb/converter.py": read_source(pkg_root, "converter/wb/converter.py"),
        "converter/wb/local_converter.py": read_source(pkg_root, "converter/wb/local_converter.py"),
        "converter/wb/sync.py": read_source(pkg_root, "converter/wb/sync.py"),
        "converter/wb/utils.py": read_source(pkg_root, "converter/wb/utils.py"),
        "converter/tfb/converter.py": read_source(pkg_root, "converter/tfb/converter.py"),
        "converter/tfb/sync.py": read_source(pkg_root, "converter/tfb/sync.py"),
        "converter/tfb/utils.py": read_source(pkg_root, "converter/tfb/utils.py"),
        "converter/mlf/converter.py": read_source(pkg_root, "converter/mlf/converter.py"),
        "converter/mlf/sync.py": read_source(pkg_root, "converter/mlf/sync.py"),
    }

    trees = {rel: parse_source(text, rel) for rel, text in modules.items()}

    require_args(trees["sdk/cmd/sync.py"], "sync", ["run_dir", "settings"])
    require_args(trees["sdk/cmd/sync.py"], "ensure_run_dir", ["run_dir"])
    require_snippets(
        "sdk/cmd/sync.py",
        modules["sdk/cmd/sync.py"],
        [
            "TypeAdapter(DirectoryPath).validate_python",
            "os.access",
            "AuthenticationError",
            "client.exists",
            "login_raw",
            "run_with_progress",
            "confirm_sync_finish",
            "deliver_sync_start",
            "deliver_sync_flush",
        ],
    )

    require_args(trees["cli/sync/__init__.py"], "sync", ["path", "api_key", "workspace", "project", "host", "id"])
    require_snippets(
        "cli/sync/__init__.py",
        modules["cli/sync/__init__.py"],
        ["exists=True", "file_okay=False", "readable=True", "--api-key", "--host", "--workspace", "--project", "--id"],
    )

    require_args(
        trees["converter/base.py"],
        "__init__",
        ["project", "workspace", "mode", "log_dir", "logdir", "tags", "resume"],
        class_name="BaseConverter",
    )
    require_args(trees["converter/helper.py"], "extract_args", ["fn", "args", "kwargs", "param_names"])

    require_snippets(
        "converter/__init__.py",
        modules["converter/__init__.py"],
        ["WandbConverter", "WandbLocalConverter", "TFBConverter", "MLFlowConverter", "sync_wandb", "sync_tensorboardX", "sync_tensorboard_torch", "sync_mlflow"],
    )

    require_args(trees["converter/wb/converter.py"], "run", ["wb_project", "wb_entity", "wb_run_id"], class_name="WandbConverter")
    require_args(
        trees["converter/wb/local_converter.py"],
        "run",
        ["root_wandb_dir", "wandb_run_dir", "wb_run_id"],
        class_name="WandbLocalConverter",
    )
    require_snippets(
        "converter/wb/local_converter.py",
        modules["converter/wb/local_converter.py"],
        ["run-*", "offline-run-*", "*.wandb", "validate_path", "files"],
    )
    require_args(trees["converter/wb/sync.py"], "sync_wandb", ["mode", "wandb_run", "workspace", "log_dir"])
    require_snippets(
        "converter/wb/sync.py",
        modules["converter/wb/sync.py"],
        ["wandb.init", "Run.log", "Run.finish", "Config.update", "wandb_run is False"],
    )
    require_args(trees["converter/wb/utils.py"], "validate_path", ["base_dir", "file_path"])
    require_snippets("converter/wb/utils.py", modules["converter/wb/utils.py"], ["startswith(abs_base + os.sep)", "return None"])

    require_args(trees["converter/tfb/converter.py"], "__init__", ["types"], class_name="TFBConverter")
    require_args(trees["converter/tfb/converter.py"], "run", ["convert_dir", "depth"], class_name="TFBConverter")
    require_snippets(
        "converter/tfb/converter.py",
        modules["converter/tfb/converter.py"],
        ["SUPPORTED_TYPES", "scalar", "image", "audio", "text", "No TFEvent file found"],
    )
    require_args(trees["converter/tfb/sync.py"], "sync_tensorboardX", ["types"])
    require_args(trees["converter/tfb/sync.py"], "sync_tensorboard_torch", ["types"])
    require_snippets(
        "converter/tfb/sync.py",
        modules["converter/tfb/sync.py"],
        ["add_scalar", "add_scalars", "add_image", "add_text", "SummaryWriter.close", "swanlab.finish"],
    )
    require_args(trees["converter/tfb/utils.py"], "find_tfevents", ["logdir", "depth"])
    require_snippets("converter/tfb/utils.py", modules["converter/tfb/utils.py"], ["tfevents", "current_depth > depth"])

    require_args(trees["converter/mlf/converter.py"], "run", ["tracking_uri", "experiment", "run_id"], class_name="MLFlowConverter")
    require_args(trees["converter/mlf/sync.py"], "sync_mlflow", ["mode"])
    require_snippets(
        "converter/mlf/sync.py",
        modules["converter/mlf/sync.py"],
        ["set_experiment", "start_run", "end_run", "log_param", "log_params", "log_metric", "log_metrics"],
    )

    require_args(
        trees["cli/converter/__init__.py"],
        "convert",
        [
            "convert_type",
            "project",
            "mode",
            "workspace",
            "logdir",
            "tb_log_dir",
            "tb_types",
            "wb_project",
            "wb_entity",
            "wb_runid",
            "wb_dir",
            "wb_run_dir",
            "mlflow_url",
            "mlflow_exp",
            "mlflow_runid",
            "resume",
        ],
    )
    require_snippets(
        "cli/converter/__init__.py",
        modules["cli/converter/__init__.py"],
        [
            "tensorboard",
            "wandb-local",
            "mlflow",
            "--tb-log-dir",
            "--tb-logdir",
            "--wb-project",
            "--wb-entity",
            "--wb-dir",
            "--mlflow-exp",
            "--resume requires --wb-runid",
        ],
    )

    print("OK: source parser assertions found expected sync/converter surfaces")


def optional_dependency_report() -> None:
    optional = {
        "wandb": "W&B live sync/cloud/local converter",
        "tensorboard": "TensorBoard file converter",
        "tensorboardX": "tensorboardX live sync",
        "torch": "torch SummaryWriter live sync",
        "mlflow": "MLflow live sync/converter",
        "numpy": "W&B/TensorBoard image conversion",
        "PIL": "TensorBoard image conversion",
    }
    for module, purpose in optional.items():
        status = "available" if importlib.util.find_spec(module) else "missing"
        print(f"INFO: optional dependency {module}: {status} ({purpose})")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run no-network SwanLab sync/converter guard checks.")
    parser.add_argument(
        "--package-root",
        help="Path to a SwanLab package directory or a parent directory containing swanlab/.",
    )
    parser.add_argument(
        "--check-run-dir",
        help="Validate a candidate SwanLab run directory with clear local-only errors.",
    )
    parser.add_argument(
        "--skip-optional-probes",
        action="store_true",
        help="Skip importlib optional-dependency availability reporting.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.check_run_dir:
            validated = validate_run_dir_like_sync(Path(args.check_run_dir).expanduser())
            print(f"OK: run directory is present, readable, and resolves to: {validated}")
        else:
            run_path_guard_self_tests()

        pkg_root = locate_swanlab_root(args.package_root)
        print(f"INFO: parsing SwanLab package at: {pkg_root}")
        assert_source_guards(pkg_root)
        if not args.skip_optional_probes:
            optional_dependency_report()
        print("OK: all no-network sync/converter guard checks passed")
        return 0
    except CheckError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
