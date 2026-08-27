#!/usr/bin/env python3
"""Safe diagnostic checks for SwanLab integrations and plugins.

The script never installs packages and never makes network calls.
It bootstraps a minimal local runtime, exercises the callback manager,
CSV writer, and notification plugins, and probes missing optional
framework imports from the adapter modules themselves.
"""

from __future__ import annotations

import contextlib
import csv
import enum
import importlib.util
import json
import os
import sys
import tempfile
import threading
import types
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Iterable, Union
from unittest.mock import patch


class MinimalCallback:
    @property
    def name(self) -> str:
        return self.__class__.__name__


class CoreEnum(str, enum.Enum):
    CORE_PYTHON = "CorePython"
    CORE = "Core"


class ProbeEnum(str, enum.Enum):
    PROBE_PYTHON = "ProbePython"
    PROBE = "Probe"


def _noop(*args: Any, **kwargs: Any) -> None:
    return None


def find_repo_root() -> Path:
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "README.md").is_file() and (parent / "swanlab").is_dir():
            return parent
    raise RuntimeError("Could not locate the repository root from the script path.")


def ensure_package(name: str, path: Path) -> types.ModuleType:
    module = sys.modules.get(name)
    if module is None:
        module = types.ModuleType(name)
        module.__path__ = [str(path)]
        sys.modules[name] = module
    return module


def ensure_module(name: str, **attrs: Any) -> types.ModuleType:
    module = sys.modules.get(name)
    if module is None:
        module = types.ModuleType(name)
        sys.modules[name] = module
    for key, value in attrs.items():
        setattr(module, key, value)
    return module


def load_source_module(name: str, path: Path) -> types.ModuleType:
    existing = sys.modules.get(name)
    if existing is not None and getattr(existing, "__file__", None):
        return existing  # type: ignore[return-value]

    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load module spec for {name} from {path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def fmt_run_path(run_path: str) -> str:
    parts = Path(run_path).parts
    if parts and parts[0] == os.sep:
        parts = parts[1:]
    if len(parts) < 3:
        raise ValueError(f"Invalid run path: {run_path!r}")
    username, project_name, run_id = parts[:3]
    if not username.startswith("@"):
        username = f"@{username}"
    return Path("/", username, project_name, "runs", run_id).as_posix()


def bootstrap_runtime(repo_root: Path) -> None:
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    swanlab = ensure_package("swanlab", repo_root / "swanlab")
    ensure_package("swanlab.sdk", repo_root / "swanlab" / "sdk")
    ensure_package("swanlab.sdk.internal", repo_root / "swanlab" / "sdk" / "internal")
    ensure_package("swanlab.sdk.internal.context", repo_root / "swanlab" / "sdk" / "internal" / "context")
    ensure_package(
        "swanlab.sdk.internal.context.components", repo_root / "swanlab" / "sdk" / "internal" / "context" / "components"
    )
    pkg = ensure_package("swanlab.sdk.internal.pkg", repo_root / "swanlab" / "sdk" / "internal" / "pkg")
    ensure_package("swanlab.sdk.protocol", repo_root / "swanlab" / "sdk" / "protocol")
    ensure_package("swanlab.sdk.typings", repo_root / "swanlab" / "sdk" / "typings")
    ensure_package("swanlab.plugin", repo_root / "swanlab" / "plugin")
    ensure_package("swanlab.plugin.notification", repo_root / "swanlab" / "plugin" / "notification")
    ensure_package("swanlab.plugin.writer", repo_root / "swanlab" / "plugin" / "writer")
    ensure_package("swanlab.integration", repo_root / "swanlab" / "integration")

    protocol = sys.modules["swanlab.sdk.protocol"]
    protocol.Callback = MinimalCallback
    protocol.CoreEnum = CoreEnum
    protocol.ProbeEnum = ProbeEnum
    protocol.CoreProtocol = type("CoreProtocol", (), {})
    protocol.ProbeProtocol = type("ProbeProtocol", (), {})

    ensure_module(
        "swanlab.sdk.typings.context",
        CallbacksType=Union[Iterable[MinimalCallback], MinimalCallback],
    )

    console = ensure_module(
        "swanlab.sdk.internal.pkg.console",
        info=_noop,
        warning=_noop,
        trace=_noop,
        debug=_noop,
        error=_noop,
    )
    helper = ensure_module("swanlab.sdk.internal.pkg.helper", fmt_run_path=fmt_run_path)
    pkg.console = console
    pkg.helper = helper

    safe = load_source_module("swanlab.sdk.internal.pkg.safe", repo_root / "swanlab" / "sdk" / "internal" / "pkg" / "safe" / "__init__.py")
    executor = load_source_module(
        "swanlab.sdk.internal.pkg.executor", repo_root / "swanlab" / "sdk" / "internal" / "pkg" / "executor" / "__init__.py"
    )
    pkg.safe = safe
    pkg.executor = executor

    swanlab.Callback = MinimalCallback
    swanlab.config = {}
    swanlab.get_run = lambda: None
    swanlab.init = lambda *args, **kwargs: None
    swanlab.log = lambda *args, **kwargs: None
    swanlab.finish = lambda *args, **kwargs: None
    swanlab.vendor = load_source_module("swanlab.vendor", repo_root / "swanlab" / "vendor" / "__init__.py")


class FakeResponse:
    def __init__(self, payload: dict[str, Any] | None = None):
        self._payload = payload or {"code": 0}
        self.status_code = 200
        self.text = "ok"

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict[str, Any]:
        return self._payload


def make_settings() -> SimpleNamespace:
    return SimpleNamespace(
        mode="online",
        web_host="https://swanlab.example",
        run=SimpleNamespace(id="run-123"),
        experiment=SimpleNamespace(name="demo-exp", description="demo-desc"),
        project=SimpleNamespace(name="demo-project", workspace="demo-workspace"),
    )


def probe_callback_manager() -> dict[str, Any]:
    from swanlab.sdk.internal.context.components.callbacker import CallbackManager, create_callback_manager, global_callbacker

    class Alpha(MinimalCallback):
        @property
        def name(self) -> str:
            return "alpha"

    class AlphaDup(MinimalCallback):
        @property
        def name(self) -> str:
            return "alpha"

    class Beta(MinimalCallback):
        @property
        def name(self) -> str:
            return "beta"

    mgr = CallbackManager()
    mgr.merge_callbacks(Alpha())
    mgr.merge_callbacks([AlphaDup()])
    single_supported = len(mgr.registered_callbacks) == 1 and isinstance(mgr.registered_callbacks[0], AlphaDup)

    global_callbacker.merge_callbacks([Alpha()])
    try:
        merged = create_callback_manager([Beta()])
        merged_names = sorted(cb.name for cb in merged.registered_callbacks)
        global_names = sorted(cb.name for cb in global_callbacker.registered_callbacks)
    finally:
        global_callbacker.remove_callback("alpha")

    return {
        "single_callback_supported": single_supported,
        "duplicate_overwrite": isinstance(mgr.registered_callbacks[0], AlphaDup),
        "merged_names": merged_names,
        "global_isolated": global_names == ["alpha"],
    }


def probe_csv_writer() -> dict[str, Any]:
    from swanlab.plugin.writer.csv_writer import CSVWriter

    old_cwd = Path.cwd()
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        os.chdir(tmp)
        try:
            writer = CSVWriter(dir="csv-out")
            run_dir = tmp / "run"
            run_dir.mkdir()
            writer.on_run_initialized(run_dir, "/demo-workspace/demo-project/run-123", make_settings())
            writer.on_scalar_flush([SimpleNamespace(key="loss", value=SimpleNamespace(number=1.23))])
            writer.on_run_finished("finished")

            save_path = tmp / "csv-out" / "swanlab_runs.csv"
            if not save_path.is_file():
                raise RuntimeError(f"CSVWriter did not create {save_path}")

            with save_path.open(newline="", encoding="utf-8") as handle:
                rows = list(csv.reader(handle))

            return {
                "save_path": str(save_path.relative_to(tmp)),
                "header": rows[0],
                "row_count": len(rows) - 1,
                "loss_value": rows[1][rows[0].index("loss")],
                "url_value": rows[1][rows[0].index("url")],
            }
        finally:
            os.chdir(old_cwd)


def probe_notifications() -> dict[str, Any]:
    from swanlab.plugin.notification import base as notification_base
    from swanlab.plugin.notification.dingtalk import DingTalkCallback
    from swanlab.plugin.notification.lark import LarkCallback

    settings = make_settings()
    lark = LarkCallback(webhook_url="https://lark.example/webhook", secret="lark-secret")
    lark.on_run_initialized(Path("/tmp/run"), "/demo-workspace/demo-project/run-123", settings)

    captured: dict[str, Any] = {}
    lark_module = sys.modules["swanlab.plugin.notification.lark"]

    def fake_run(fn, *args, **kwargs):
        captured["scheduled"] = True
        captured["callable"] = getattr(fn, "__name__", type(fn).__name__)
        return fn(*args, **kwargs)

    def fake_post(url, json=None, timeout=None):
        captured["url"] = url
        captured["payload"] = json
        captured["timeout"] = timeout
        return FakeResponse()

    with patch.object(notification_base.NotificationCallback._executor, "run", side_effect=fake_run):
        with patch.object(lark_module.requests, "post", side_effect=fake_post):
            lark.on_run_finished("finished")

    dingtalk = DingTalkCallback(webhook_url="https://dingtalk.example/webhook", secret="SECdemo-secret")
    signed_url = dingtalk._bot.webhook_url

    return {
        "executor_class": notification_base.NotificationCallback._executor.__class__.__name__,
        "scheduled": bool(captured.get("scheduled")),
        "callable": captured.get("callable"),
        "lark_payload_has_sign": "sign" in captured.get("payload", {}),
        "lark_payload_text_mentions_project": "demo-project" in captured.get("payload", {}).get("content", {}).get("text", ""),
        "dingtalk_url_has_sign": "sign=" in signed_url and "timestamp=" in signed_url,
    }


def probe_background_executor() -> dict[str, Any]:
    from swanlab.sdk.internal.pkg.executor import SafeThreadPoolExecutor

    ran = threading.Event()

    def explode() -> None:
        ran.set()
        raise RuntimeError("boom")

    executor = SafeThreadPoolExecutor(max_workers=1)
    executor.run(explode)
    executor.shutdown(wait=True)

    return {
        "task_ran": ran.is_set(),
        "caller_raised": False,
        "executor_class": executor.__class__.__name__,
    }


def probe_optional_framework_imports(repo_root: Path) -> dict[str, Any]:
    targets = {
        "accelerate": ("accelerate", repo_root / "swanlab" / "integration" / "accelerate.py"),
        "catboost": ("catboost", repo_root / "swanlab" / "integration" / "catboost.py"),
        "fastai": ("fastai", repo_root / "swanlab" / "integration" / "fastai.py"),
        "keras": ("keras", repo_root / "swanlab" / "integration" / "keras.py"),
        "lightgbm": ("lightgbm", repo_root / "swanlab" / "integration" / "lightgbm.py"),
        "mmengine": ("mmengine", repo_root / "swanlab" / "integration" / "mmengine.py"),
        "paddlenlp": ("paddlenlp", repo_root / "swanlab" / "integration" / "paddlenlp.py"),
        "pytorch_lightning": ("lightning", repo_root / "swanlab" / "integration" / "pytorch_lightning.py"),
        "ray": ("ray", repo_root / "swanlab" / "integration" / "ray.py"),
        "stable_baselines3": ("stable_baselines3", repo_root / "swanlab" / "integration" / "sb3.py"),
        "torchtune": ("torchtune", repo_root / "swanlab" / "integration" / "torchtune.py"),
        "transformers": ("transformers", repo_root / "swanlab" / "integration" / "transformers.py"),
        "ultralytics": ("ultralytics", repo_root / "swanlab" / "integration" / "ultralytics.py"),
        "xgboost": ("xgboost", repo_root / "swanlab" / "integration" / "xgboost.py"),
    }
    results: dict[str, Any] = {}
    for label, (package_hint, path) in targets.items():
        package_available = importlib.util.find_spec(package_hint) is not None
        if package_available:
            results[label] = {
                "status": "framework_package_available_not_loaded",
                "package": package_hint,
                "note": "framework package is importable; skipped adapter import to avoid training-framework side effects",
            }
            continue

        probe_name = f"probe_integration_{label}"
        try:
            load_source_module(probe_name, path)
        except Exception as exc:  # noqa: BLE001
            message = str(exc)
            results[label] = {
                "status": "error",
                "type": type(exc).__name__,
                "message": message,
                "message_has_install_hint": "pip install" in message and package_hint in message,
            }
        else:
            results[label] = {
                "status": "adapter_loaded_without_framework_package",
                "package": package_hint,
                "note": "adapter module did not import the third-party framework at module import time",
            }
    return results


def scan_distributed_guards(repo_root: Path) -> dict[str, list[str]]:
    specs = {
        "transformers": repo_root / "swanlab" / "integration" / "transformers.py",
        "pytorch_lightning": repo_root / "swanlab" / "integration" / "pytorch_lightning.py",
        "accelerate": repo_root / "swanlab" / "integration" / "accelerate.py",
        "paddlenlp": repo_root / "swanlab" / "integration" / "paddlenlp.py",
        "torchtune": repo_root / "swanlab" / "integration" / "torchtune.py",
        "ultralytics": repo_root / "swanlab" / "integration" / "ultralytics.py",
        "ray": repo_root / "swanlab" / "integration" / "ray.py",
    }
    terms = [
        "rank_zero_only",
        "rank_zero_experiment",
        "main_process_only",
        "is_world_process_zero",
        "self.rank == 0",
        "_processed_plots",
        "_step_counter",
        "_trial_logging_actors",
        "Queue",
    ]
    matches: dict[str, list[str]] = {}
    for label, path in specs.items():
        text = path.read_text(encoding="utf-8")
        found = [term for term in terms if term in text]
        if found:
            matches[label] = found
    return matches


def main() -> dict[str, Any]:
    repo_root = find_repo_root()
    bootstrap_runtime(repo_root)

    from swanlab.plugin.notification import base as notification_base

    callback_manager = probe_callback_manager()
    csv_writer = probe_csv_writer()
    notifications = probe_notifications()
    background_executor = probe_background_executor()

    # Tidy the shared notification executor once the scheduling probe is complete.
    notification_base.NotificationCallback._executor.shutdown(wait=True)

    return {
        "repository_source_resolved": True,
        "callback_manager": callback_manager,
        "csv_writer": csv_writer,
        "notifications": notifications,
        "background_executor": background_executor,
        "optional_framework_imports": probe_optional_framework_imports(repo_root),
        "distributed_guard_scan": scan_distributed_guards(repo_root),
    }


if __name__ == "__main__":
    print(json.dumps(main(), indent=2, ensure_ascii=False, sort_keys=True))
