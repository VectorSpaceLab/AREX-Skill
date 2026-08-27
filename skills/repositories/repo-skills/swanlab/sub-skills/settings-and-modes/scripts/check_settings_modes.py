#!/usr/bin/env python3
"""Safe local assertions for SwanLab settings and modes.

This script intentionally avoids credentials and network access. It uses only
process-local environment changes and temporary directories.
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path
from typing import Callable, Type


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _assert_equal(actual, expected, message: str) -> None:
    if actual != expected:
        raise AssertionError(f"{message}: expected {expected!r}, got {actual!r}")


def _assert_raises(exc_type: Type[BaseException], fn: Callable[[], object], contains: str) -> None:
    try:
        fn()
    except exc_type as exc:
        if contains and contains not in str(exc):
            raise AssertionError(f"exception did not contain {contains!r}: {exc!r}") from exc
    else:
        raise AssertionError(f"expected {exc_type.__name__} to be raised")


def main() -> int:
    original_cwd = Path.cwd()
    original_env = os.environ.copy()

    with tempfile.TemporaryDirectory(prefix="swanlab-settings-modes-") as tmp_name:
        tmp = Path(tmp_name)
        workspace = tmp / "workspace"
        workspace.mkdir()
        config_dir = tmp / "system-config"
        config_dir.mkdir()
        secrets_dir = tmp / "secrets"
        secrets_dir.mkdir()
        user_root = tmp / "user-root"

        try:
            # Isolate this process from user credentials/config while still allowing
            # SwanLab to read controlled temporary config sources.
            for key in list(os.environ):
                if key.startswith("SWANLAB_"):
                    os.environ.pop(key)
            os.environ["SWANLAB_SAVE_DIR"] = str(user_root)
            os.environ["SWANLAB_CONFIG_DIR"] = str(config_dir)
            os.environ["SWANLAB_SECRETS_DIR"] = str(secrets_dir)
            os.chdir(workspace)

            try:
                import swanlab
                from swanlab import Settings
                from swanlab.sdk.internal.settings import resolve_hosts
            except Exception as exc:  # pragma: no cover - diagnostic path
                print(f"FAILED: could not import SwanLab: {type(exc).__name__}: {exc}", file=sys.stderr)
                return 1

            # Settings construction and validation should be side-effect-light.
            log_dir = tmp / "not-created-by-settings"
            settings = Settings(
                mode="disabled",
                log_dir=log_dir,
                probe=Settings.Probe(monitor=False, monitor_interval=5),
                terminal=Settings.Terminal(proxy_type="none", max_length=500),
            )
            _assert_equal(settings.mode, "disabled", "mode constructor value")
            _assert_equal(settings.probe.monitor, False, "probe nested constructor")
            _assert_equal(settings.terminal.proxy_type, "none", "terminal nested constructor")
            _assert(not log_dir.exists(), "Settings construction must not create log_dir")
            _assert_equal(Settings(mode="cloud").mode, "online", "legacy cloud mode maps to online")

            # Host normalization and blank-host failure.
            api, web, web_is_set = resolve_hosts(api_host="custom.example.com/api/v1/?x=1")
            _assert_equal(api, "https://custom.example.com", "api host is cleaned")
            _assert_equal(web, "https://custom.example.com", "web host is derived from custom api host")
            _assert_equal(web_is_set, True, "derived web host is marked explicit for custom api host")
            _assert_raises(ValueError, lambda: resolve_hosts(api_host="   "), "Host cannot be empty")

            # merge_settings deep-merge behavior and api_host -> web_host re-derivation.
            base = Settings(api_key="current-key", api_host="https://api-a.example", web_host="https://web-a.example")
            base.merge_settings({"probe": {"monitor": False}, "terminal": {"proxy_type": "none"}})
            _assert_equal(base.api_key, "current-key", "dict merge preserves unrelated api_key")
            _assert_equal(base.probe.monitor, False, "dict merge updates nested field")
            _assert_equal(base.probe.monitor_interval, 10, "dict merge preserves sibling nested defaults")
            _assert_equal(base.terminal.proxy_type, "none", "dict merge updates terminal")
            base.merge_settings({"api_host": "api-b.example/api/v2"})
            _assert_equal(base.api_host, "https://api-b.example", "merge cleans api host")
            _assert_equal(base.web_host, "https://api-b.example", "merge re-derives web host when omitted")
            base.merge_settings(Settings(log_dir=tmp / "new-log-dir"))
            _assert_equal(base.api_key, "current-key", "Settings-object merge must not overwrite with unset defaults")

            # require() accepts known Python-backend tokens and rejects unknown tokens.
            _assert_equal(swanlab.require("core_python", "probe_python"), ["core_python", "probe_python"], "require returns activated tokens")
            _assert_raises(ValueError, lambda: swanlab.require("not-a-real-requirement"), "Unknown requirement")

            # Disabled-mode smoke: no credentials, no network, no log directory creation.
            disabled_log_dir = tmp / "disabled-log"
            run = swanlab.init(
                mode="disabled",
                project="settings-modes-check",
                log_dir=disabled_log_dir,
                settings=Settings(
                    probe=Settings.Probe(hardware=False, requirements=False, git=False, monitor=False),
                    terminal=Settings.Terminal(proxy_type="none"),
                ),
            )
            _assert(swanlab.has_run(), "disabled init should create an active run object")
            _assert(run.mode == "disabled", "run mode should be disabled")
            swanlab.log({"settings_modes_check": 1}, step=0)
            swanlab.finish()
            _assert(not swanlab.has_run(), "finish should clear active run")
            _assert(getattr(swanlab, "run") is None, "swanlab.run should be None after finish")
            _assert(not disabled_log_dir.exists(), "disabled mode should not create the log directory")

            # Source precedence: env < secret < .env < swanlab.yaml.
            os.environ["SWANLAB_API_KEY"] = "env-key"
            _assert_equal(Settings().api_key, "env-key", "env api key baseline")

            (secrets_dir / "api_key").write_text("secret-key", encoding="utf-8")
            _assert_equal(Settings().api_key, "secret-key", "secret api_key overrides env")

            (workspace / ".env").write_text("SWANLAB_API_KEY=dotenv-key\n", encoding="utf-8")
            _assert_equal(Settings().api_key, "dotenv-key", ".env overrides secret")

            (workspace / "swanlab.yaml").write_text(
                "api_key: yaml-key\nmode: offline\nprobe:\n  monitor: true\n",
                encoding="utf-8",
            )
            os.environ["SWANLAB_PROBE_MONITOR"] = "false"
            yaml_settings = Settings()
            _assert_equal(yaml_settings.api_key, "yaml-key", "swanlab.yaml overrides .env/env")
            _assert_equal(yaml_settings.mode, "offline", "swanlab.yaml mode loads")
            _assert_equal(yaml_settings.probe.monitor, True, "swanlab.yaml nested value overrides env")

            # Lower-priority project/user config: env overrides per-directory config;
            # per-directory config overrides user-root config for overlapping keys.
            (workspace / "swanlab.yaml").unlink()
            (workspace / ".env").unlink()
            (secrets_dir / "api_key").unlink()
            os.environ.pop("SWANLAB_API_KEY", None)
            os.environ.pop("SWANLAB_PROBE_MONITOR", None)
            user_root.mkdir(parents=True, exist_ok=True)
            (user_root / "config.yaml").write_text("api_key: root-key\nmode: local\n", encoding="utf-8")
            pwd_config_dir = workspace / ".swanlab"
            pwd_config_dir.mkdir()
            (pwd_config_dir / "config.yaml").write_text("api_key: pwd-key\n", encoding="utf-8")
            pwd_settings = Settings()
            _assert_equal(pwd_settings.api_key, "pwd-key", "cwd .swanlab config overrides user config")
            _assert_equal(pwd_settings.mode, "local", "user config supplies missing mode")
            os.environ["SWANLAB_API_KEY"] = "env-over-pwd"
            _assert_equal(Settings().api_key, "env-over-pwd", "env overrides cwd .swanlab config")

            print("SwanLab settings-and-modes checks passed")
            return 0
        finally:
            try:
                if "swanlab" in sys.modules:
                    swanlab_mod = sys.modules["swanlab"]
                    if getattr(swanlab_mod, "has_run", lambda: False)():
                        swanlab_mod.finish()
            finally:
                os.chdir(original_cwd)
                os.environ.clear()
                os.environ.update(original_env)


if __name__ == "__main__":
    raise SystemExit(main())
