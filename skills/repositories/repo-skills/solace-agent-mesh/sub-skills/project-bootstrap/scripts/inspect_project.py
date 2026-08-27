#!/usr/bin/env python3
"""Dry inspector for generated Solace Agent Mesh project trees.

The helper is deterministic and safe by default: it reads files, parses YAML when
PyYAML is available, and reports scaffold issues. It never imports project code,
starts SAM, contacts brokers/clouds/LLMs, opens browsers, or writes to the target
project.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

try:  # PyYAML is expected in SAM environments, but keep text checks usable without it.
    import yaml  # type: ignore
except Exception:  # pragma: no cover - exercised only when PyYAML is absent.
    yaml = None  # type: ignore


PLACEHOLDER_RE = re.compile(r"__[A-Z0-9_]+__")
ENV_REF_RE = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)(?:,([^}]*))?\}")
ALIAS_VALUE_RE = re.compile(r":\s*(\*[A-Za-z_][A-Za-z0-9_]*)(\s*(?:#.*)?)$")
MERGE_ALIAS_RE = re.compile(r"^\s*<<:\s*\*[A-Za-z_][A-Za-z0-9_]*\s*(?:#.*)?$")
DB_ENV_NAMES = {
    "ORCHESTRATOR_DATABASE_URL",
    "WEB_UI_GATEWAY_DATABASE_URL",
    "PLATFORM_DATABASE_URL",
}
OPTIONAL_NO_DEFAULT_ENV = {
    "AZURE_SPEECH_KEY",
    "AZURE_SPEECH_REGION",
    "EXTERNAL_AUTH_PROVIDER",
    "EXTERNAL_AUTH_SERVICE_URL",
    "FRONTEND_USE_AUTHORIZATION",
    "GEMINI_API_KEY",
    "GOOGLE_APPLICATION_CREDENTIALS",
    "IMAGE_MODEL_NAME",
    "IMAGE_SERVICE_API_KEY",
    "IMAGE_SERVICE_ENDPOINT",
    "LLM_REPORT_MODEL_NAME",
    "OPENAI_API_KEY",
    "SECURE_AGENT_TOKEN",
    "TTS_PROVIDER",
    "WEBUI_FRONTEND_LOGO_URL",
}


@dataclass
class Finding:
    severity: str
    path: str
    message: str
    hint: str = ""


@dataclass
class AppSummary:
    file: str
    name: str
    module: str


class UnknownTagLoader(yaml.SafeLoader if yaml is not None else object):  # type: ignore[misc]
    """SafeLoader variant that materializes unknown custom tags as plain data."""


if yaml is not None:

    def _construct_unknown(loader: UnknownTagLoader, tag_suffix: str, node: Any) -> Any:
        if isinstance(node, yaml.ScalarNode):
            return loader.construct_scalar(node)
        if isinstance(node, yaml.SequenceNode):
            return loader.construct_sequence(node)
        if isinstance(node, yaml.MappingNode):
            return loader.construct_mapping(node)
        return None

    UnknownTagLoader.add_multi_constructor("", _construct_unknown)  # type: ignore[attr-defined]


class Inspector:
    def __init__(self, root: Path, strict: bool = False) -> None:
        self.root = root.resolve()
        self.strict = strict
        self.findings: list[Finding] = []
        self.apps: list[AppSummary] = []
        self.env: dict[str, str] = {}

    def rel(self, path: Path) -> str:
        try:
            return str(path.resolve().relative_to(self.root))
        except Exception:
            return str(path)

    def add(self, severity: str, path: str | Path, message: str, hint: str = "") -> None:
        path_str = self.rel(path) if isinstance(path, Path) else path
        self.findings.append(Finding(severity, path_str, message, hint))

    def run(self) -> dict[str, Any]:
        if not self.root.exists():
            self.add("error", str(self.root), "Project path does not exist.")
            return self.result()
        if not self.root.is_dir():
            self.add("error", str(self.root), "Project path is not a directory.")
            return self.result()

        self.env = self.parse_env(self.root / ".env")
        self.check_layout()
        self.check_env_values()
        self.check_yaml_files()
        self.check_webui_platform_consistency()
        return self.result()

    def result(self) -> dict[str, Any]:
        counts = {"error": 0, "warning": 0, "info": 0}
        for finding in self.findings:
            counts[finding.severity] = counts.get(finding.severity, 0) + 1
        ok = counts.get("error", 0) == 0 and (not self.strict or counts.get("warning", 0) == 0)
        return {
            "ok": ok,
            "root": str(self.root),
            "counts": counts,
            "apps": [asdict(app) for app in self.apps],
            "findings": [asdict(f) for f in self.findings],
        }

    def parse_env(self, env_path: Path) -> dict[str, str]:
        values: dict[str, str] = {}
        if not env_path.exists():
            return values
        for raw_line in env_path.read_text(encoding="utf-8", errors="replace").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip()
            if (value.startswith('"') and value.endswith('"')) or (
                value.startswith("'") and value.endswith("'")
            ):
                value = value[1:-1]
            if key:
                values[key] = value
        return values

    def check_layout(self) -> None:
        required_dirs = ["configs", "configs/agents", "src"]
        expected_dirs = ["configs/gateways", "configs/services"]
        for rel in required_dirs:
            path = self.root / rel
            if not path.is_dir():
                self.add("error", path, f"Required directory `{rel}` is missing.", "Run `sam init` from the intended project root.")
        for rel in expected_dirs:
            path = self.root / rel
            if not path.is_dir():
                self.add("warning", path, f"Expected directory `{rel}` is missing.", "This is unusual for `sam init`; verify Web UI/service choices or partial initialization.")

        required_files = [
            "requirements.txt",
            ".env",
            "configs/shared_config.yaml",
            "configs/logging_config.yaml",
            "configs/agents/main_orchestrator.yaml",
        ]
        for rel in required_files:
            path = self.root / rel
            if not path.is_file():
                severity = "warning" if rel == ".env" else "error"
                self.add(severity, path, f"Expected file `{rel}` is missing.")

        webui = self.root / "configs/gateways/webui.yaml"
        platform = self.root / "configs/services/platform.yaml"
        if not webui.exists():
            self.add("info", webui, "Web UI gateway config is not present.", "This is acceptable only if Web UI was intentionally disabled.")
        if webui.exists() and not platform.exists():
            self.add("warning", platform, "Web UI gateway exists but platform service config is missing.", "Regenerate or restore `configs/services/platform.yaml`.")

    def check_env_values(self) -> None:
        env_path = self.root / ".env"
        if not env_path.exists():
            return
        required = ["NAMESPACE", "SOLACE_DEV_MODE", "LOGGING_CONFIG_PATH"]
        for key in required:
            if key not in self.env:
                self.add("warning", env_path, f"`.env` does not define `{key}`.")

        namespace = self.env.get("NAMESPACE")
        if namespace and not namespace.endswith("/"):
            self.add("warning", env_path, "`NAMESPACE` does not end with `/`.", "SAM topic namespaces conventionally include a trailing slash.")

        for key in ("FASTAPI_PORT", "FASTAPI_HTTPS_PORT", "PLATFORM_API_PORT"):
            value = self.env.get(key)
            if value and not str(value).isdigit():
                self.add("error", env_path, f"`{key}` must be an integer port, got `{value}`.")

        dev_mode = self.env.get("SOLACE_DEV_MODE")
        if dev_mode and dev_mode.lower() not in {"true", "false", "1", "0", "yes", "no"}:
            self.add("warning", env_path, f"`SOLACE_DEV_MODE` has unusual boolean value `{dev_mode}`.")

        for key, value in sorted(self.env.items()):
            if "YOUR_" in value and value.endswith("_HERE"):
                self.add("warning", env_path, f"`{key}` still has placeholder value `{value}`.", "Replace it before live runtime use or remove the unused provider config.")
            if key == "SESSION_SECRET_KEY" and value == "please_change_me_in":
                self.add("warning", env_path, "`SESSION_SECRET_KEY` is still the scaffold default.", "Change it before any shared or production run.")

        for db_key in DB_ENV_NAMES:
            if db_key in self.env:
                self.check_database_url(env_path, db_key, self.env[db_key])

    def yaml_files(self) -> Iterable[Path]:
        configs_dir = self.root / "configs"
        if not configs_dir.is_dir():
            return []
        return sorted([*configs_dir.rglob("*.yaml"), *configs_dir.rglob("*.yml")])

    def check_yaml_files(self) -> None:
        if yaml is None:
            self.add("warning", "python", "PyYAML is unavailable; YAML schema checks were skipped.", "Install PyYAML to enable full dry inspection.")
            for path in self.yaml_files():
                self.scan_text_file(path)
            return

        for path in self.yaml_files():
            text = path.read_text(encoding="utf-8", errors="replace")
            self.scan_text_file(path, text)
            self.check_include_lines(path, text)
            data = self.load_yaml(path, text)
            if data is None:
                continue
            self.check_app_file(path, data)
            self.check_service_blocks(path, data)

    def scan_text_file(self, path: Path, text: str | None = None) -> None:
        if text is None:
            text = path.read_text(encoding="utf-8", errors="replace")
        placeholders = sorted(set(PLACEHOLDER_RE.findall(text)))
        for token in placeholders:
            self.add("error", path, f"Unresolved template token `{token}` remains in generated file.")

        for match in ENV_REF_RE.finditer(text):
            env_name, default = match.group(1), match.group(2)
            if default is None and env_name not in self.env and env_name not in OPTIONAL_NO_DEFAULT_ENV:
                severity = "warning" if env_name not in DB_ENV_NAMES else "error"
                self.add(severity, path, f"Environment reference `${{{env_name}}}` has no default and is not present in `.env`.")
            if default is not None and env_name in DB_ENV_NAMES:
                self.check_database_url(path, env_name, default.strip())

        if "YOUR_" in text:
            for line_no, line in enumerate(text.splitlines(), start=1):
                if "YOUR_" in line and "_HERE" in line:
                    self.add("warning", path, f"Placeholder-looking value remains near line {line_no}.", line.strip())

    def check_include_lines(self, path: Path, text: str) -> None:
        for line_no, raw in enumerate(text.splitlines(), start=1):
            stripped = raw.strip()
            if not stripped.startswith("!include "):
                continue
            target_text = stripped.split(None, 1)[1].strip().strip('"\'')
            target = (path.parent / target_text).resolve()
            if not target.exists():
                self.add("error", path, f"Include target on line {line_no} does not exist: `{target_text}`.", "Keep generated config files under their expected `configs/*/` directory or adjust include paths deliberately.")

    def sanitize_yaml(self, text: str) -> str:
        clean_lines: list[str] = []
        for raw in text.splitlines():
            stripped = raw.strip()
            if stripped.startswith("!include "):
                continue
            if MERGE_ALIAS_RE.match(raw):
                continue
            clean_lines.append(ALIAS_VALUE_RE.sub(r': "\1"\2', raw))
        return "\n".join(clean_lines) + "\n"

    def load_yaml(self, path: Path, text: str) -> Any | None:
        try:
            return yaml.load(self.sanitize_yaml(text), Loader=UnknownTagLoader)  # type: ignore[arg-type]
        except Exception as exc:
            self.add("error", path, f"YAML parse failed after safe preprocessing: {exc}")
            return None

    def check_app_file(self, path: Path, data: Any) -> None:
        if not isinstance(data, dict):
            return
        apps = data.get("apps")
        if apps is None:
            return
        if not isinstance(apps, list):
            self.add("error", path, "`apps` must be a list.")
            return
        for idx, app in enumerate(apps):
            if not isinstance(app, dict):
                self.add("error", path, f"`apps[{idx}]` is not a mapping.")
                continue
            name = str(app.get("name") or "")
            module = str(app.get("app_module") or "")
            if not name:
                self.add("error", path, f"`apps[{idx}].name` is missing.")
            if not module:
                self.add("error", path, f"`apps[{idx}].app_module` is missing.")
            else:
                self.apps.append(AppSummary(file=self.rel(path), name=name or f"apps[{idx}]", module=module))
            app_config = app.get("app_config")
            if app_config is None:
                self.add("warning", path, f"`apps[{idx}].app_config` is missing.")
                continue
            if not isinstance(app_config, dict):
                self.add("error", path, f"`apps[{idx}].app_config` must be a mapping.")
                continue
            self.check_known_app_config(path, module, app_config)

    def check_known_app_config(self, path: Path, module: str, app_config: dict[str, Any]) -> None:
        if module == "solace_agent_mesh.agent.sac.app":
            for key in ("namespace", "agent_name", "model_provider"):
                if key not in app_config:
                    self.add("warning", path, f"Agent app config is missing `{key}`.")
            if "session_service" not in app_config:
                self.add("warning", path, "Agent app config is missing `session_service`.")
            if "artifact_service" not in app_config:
                self.add("warning", path, "Agent app config is missing `artifact_service`.")
        elif module == "solace_agent_mesh.gateway.http_sse.app":
            for key in ("namespace", "gateway_id", "fastapi_host", "fastapi_port", "session_service", "artifact_service"):
                if key not in app_config:
                    self.add("warning", path, f"Web UI gateway app config is missing `{key}`.")
        elif module == "solace_agent_mesh.services.platform.app":
            for key in ("namespace", "database_url", "fastapi_host", "fastapi_port"):
                if key not in app_config:
                    self.add("warning", path, f"Platform service app config is missing `{key}`.")
        elif module == "solace_agent_mesh.agent.proxies.a2a.app":
            if "proxied_agents" not in app_config:
                self.add("warning", path, "Proxy app config has no `proxied_agents` list.")
        elif module.startswith("src.") and module.endswith(".app"):
            for key in ("namespace", "gateway_id"):
                if key not in app_config:
                    self.add("warning", path, f"Custom gateway app config is missing `{key}`.")

    def check_service_blocks(self, path: Path, data: Any) -> None:
        for service_path, service in self.walk_key(data, "session_service"):
            if isinstance(service, dict):
                service_type = service.get("type")
                if service_type not in {"memory", "sql", "vertex_rag"}:
                    self.add("warning", path, f"Session service at `{service_path}` has unusual type `{service_type}`.")
                if service_type == "sql":
                    database_url = service.get("database_url")
                    if not database_url:
                        self.add("error", path, f"SQL session service at `{service_path}` is missing `database_url`.")
                    else:
                        self.check_database_url(path, "database_url", str(database_url))

        for service_path, service in self.walk_key(data, "artifact_service"):
            if isinstance(service, str):
                continue
            if not isinstance(service, dict):
                self.add("warning", path, f"Artifact service at `{service_path}` is not a mapping or shared alias.")
                continue
            service_type = service.get("type")
            if service_type not in {"memory", "filesystem", "gcs", "s3"}:
                self.add("warning", path, f"Artifact service at `{service_path}` has unusual type `{service_type}`.")
            if service_type == "filesystem" and not service.get("base_path"):
                self.add("error", path, f"Filesystem artifact service at `{service_path}` is missing `base_path`.")
            if service_type in {"gcs", "s3"} and not (service.get("bucket_name") or self.env.get("S3_BUCKET_NAME")):
                self.add("warning", path, f"{service_type.upper()} artifact service at `{service_path}` has no bucket value visible to the inspector.")
            scope = service.get("artifact_scope")
            if scope and scope not in {"namespace", "app", "custom"}:
                self.add("warning", path, f"Artifact service at `{service_path}` has unusual `artifact_scope` `{scope}`.")

    def walk_key(self, data: Any, key: str, prefix: str = "$") -> Iterable[tuple[str, Any]]:
        if isinstance(data, dict):
            for k, v in data.items():
                next_path = f"{prefix}.{k}"
                if k == key:
                    yield next_path, v
                yield from self.walk_key(v, key, next_path)
        elif isinstance(data, list):
            for idx, item in enumerate(data):
                yield from self.walk_key(item, key, f"{prefix}[{idx}]")

    def check_database_url(self, path: Path, label: str, value: str) -> None:
        candidate = self.resolve_env_default(value)
        if "${" in candidate:
            return
        if not candidate:
            return
        if candidate.startswith("sqlite:///"):
            db_path = candidate.removeprefix("sqlite:///")
            if not db_path:
                self.add("error", path, f"Database URL `{label}` has empty SQLite path.")
            return
        if candidate.startswith("sqlite://") and not candidate.startswith("sqlite:///"):
            self.add("error", path, f"Database URL `{label}` should use `sqlite:///path.db` for file-backed SQLite.")
            return
        if candidate.startswith("postgres://"):
            self.add("warning", path, f"Database URL `{label}` uses `postgres://`; prefer `postgresql://`.")
            return
        if candidate.startswith("postgresql://"):
            return
        if candidate in {"memory", "none"}:
            return
        self.add("warning", path, f"Database URL `{label}` has unrecognized scheme/value `{candidate}`.")

    def resolve_env_default(self, value: str) -> str:
        match = ENV_REF_RE.fullmatch(value.strip().strip('"\''))
        if not match:
            return value.strip().strip('"\'')
        env_name, default = match.group(1), match.group(2)
        if env_name in self.env:
            return self.env[env_name]
        return (default or "").strip()

    def check_webui_platform_consistency(self) -> None:
        webui = self.root / "configs/gateways/webui.yaml"
        platform = self.root / "configs/services/platform.yaml"
        if not webui.exists():
            return
        if not platform.exists():
            return
        platform_url = self.env.get("PLATFORM_SERVICE_URL", "")
        platform_host = self.env.get("PLATFORM_API_HOST", "")
        platform_port = self.env.get("PLATFORM_API_PORT", "")
        if platform_url and platform_host and platform_host not in platform_url:
            self.add("warning", self.root / ".env", "`PLATFORM_SERVICE_URL` host does not match `PLATFORM_API_HOST`.")
        if platform_url and platform_port and f":{platform_port}" not in platform_url:
            self.add("warning", self.root / ".env", "`PLATFORM_SERVICE_URL` port does not match `PLATFORM_API_PORT`.")

        fastapi_host = self.env.get("FASTAPI_HOST")
        if fastapi_host == "127.0.0.1":
            self.add("info", self.root / ".env", "`FASTAPI_HOST` is loopback-only.", "For containerized runtime access, plan to set it to `0.0.0.0` before handing off to runtime operations.")


def write_human(result: dict[str, Any]) -> None:
    status = "PASS" if result["ok"] else "FAIL"
    print(f"SAM project inspection: {status}")
    print(f"Root: {result['root']}")
    counts = result["counts"]
    print(f"Findings: {counts.get('error', 0)} error(s), {counts.get('warning', 0)} warning(s), {counts.get('info', 0)} info")
    if result["apps"]:
        print("\nApps:")
        for app in result["apps"]:
            print(f"  - {app['file']}: {app['name']} [{app['module']}]")
    if result["findings"]:
        print("\nFindings:")
        for finding in result["findings"]:
            hint = f" Hint: {finding['hint']}" if finding.get("hint") else ""
            print(f"  [{finding['severity'].upper()}] {finding['path']}: {finding['message']}{hint}")


def create_self_test_project(base: Path) -> Path:
    root = base / "tiny-sam-project"
    (root / "configs/agents").mkdir(parents=True)
    (root / "configs/gateways").mkdir(parents=True)
    (root / "configs/services").mkdir(parents=True)
    (root / "src").mkdir(parents=True)
    (root / "src/__init__.py").write_text("# Source directory\n", encoding="utf-8")
    (root / "requirements.txt").write_text("solace-agent-mesh~=1.28.7\n", encoding="utf-8")
    (root / ".env").write_text(
        "\n".join(
            [
                'NAMESPACE="tiny/"',
                'SOLACE_DEV_MODE="true"',
                'LOGGING_CONFIG_PATH="configs/logging_config.yaml"',
                'SESSION_SECRET_KEY="not_the_default"',
                'FASTAPI_HOST="127.0.0.1"',
                'FASTAPI_PORT="8000"',
                'FASTAPI_HTTPS_PORT="8443"',
                'PLATFORM_API_HOST="127.0.0.1"',
                'PLATFORM_API_PORT="8001"',
                'PLATFORM_SERVICE_URL="http://127.0.0.1:8001"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (root / "configs/shared_config.yaml").write_text(
        """shared_config:
  - broker_connection: &broker_connection
      dev_mode: ${SOLACE_DEV_MODE, false}
      broker_url: ${SOLACE_BROKER_URL, ws://localhost:8008}
  - models:
      planning: &planning_model
        model: ${LLM_SERVICE_PLANNING_MODEL_NAME, openai/example}
      general: &general_model
        model: ${LLM_SERVICE_GENERAL_MODEL_NAME, openai/example}
  - services:
      session_service: &default_session_service
        type: "memory"
        default_behavior: "PERSISTENT"
      artifact_service: &default_artifact_service
        type: "filesystem"
        base_path: "./artifacts"
        artifact_scope: namespace
      data_tools_config: &default_data_tools_config
        sqlite_memory_threshold_mb: 100
""",
        encoding="utf-8",
    )
    (root / "configs/logging_config.yaml").write_text("version: 1\nhandlers: {}\n", encoding="utf-8")
    (root / "configs/agents/main_orchestrator.yaml").write_text(
        """!include ../shared_config.yaml
apps:
  - name: tiny_orchestrator_app
    app_module: solace_agent_mesh.agent.sac.app
    broker:
      <<: *broker_connection
    app_config:
      namespace: ${NAMESPACE}
      agent_name: "OrchestratorAgent"
      model: *planning_model
      model_provider: ["planning"]
      session_service:
        type: "sql"
        database_url: "${ORCHESTRATOR_DATABASE_URL, sqlite:///orchestrator.db}"
        default_behavior: "PERSISTENT"
      artifact_service: *default_artifact_service
""",
        encoding="utf-8",
    )
    (root / "configs/gateways/webui.yaml").write_text(
        """!include ../shared_config.yaml
apps:
  - name: a2a_webui_app
    app_module: solace_agent_mesh.gateway.http_sse.app
    app_config:
      namespace: ${NAMESPACE}
      gateway_id: ${WEBUI_GATEWAY_ID, webui-gw-01}
      fastapi_host: ${FASTAPI_HOST}
      fastapi_port: ${FASTAPI_PORT, 8000}
      session_service:
        type: "sql"
        database_url: "${WEB_UI_GATEWAY_DATABASE_URL, sqlite:///webui_gateway.db}"
        default_behavior: "PERSISTENT"
      artifact_service: *default_artifact_service
      platform_service:
        url: "${PLATFORM_SERVICE_URL, http://localhost:8001}"
""",
        encoding="utf-8",
    )
    (root / "configs/services/platform.yaml").write_text(
        """!include ../shared_config.yaml
apps:
  - name: platform_service_app
    app_module: solace_agent_mesh.services.platform.app
    app_config:
      namespace: ${NAMESPACE}
      database_url: "${PLATFORM_DATABASE_URL, sqlite:///platform.db}"
      fastapi_host: ${PLATFORM_API_HOST, localhost}
      fastapi_port: ${PLATFORM_API_PORT, 8001}
""",
        encoding="utf-8",
    )
    return root


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Dry-inspect a generated Solace Agent Mesh project tree without starting services."
    )
    parser.add_argument(
        "project",
        nargs="?",
        default=".",
        help="Path to the SAM project root to inspect (default: current directory).",
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as failures in the process exit status.",
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Inspect an embedded tiny fixture instead of the provided project path.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    if args.self_test:
        with tempfile.TemporaryDirectory(prefix="sam-inspect-") as tmp:
            root = create_self_test_project(Path(tmp))
            result = Inspector(root, strict=args.strict).run()
            if args.json:
                print(json.dumps(result, indent=2, sort_keys=True))
            else:
                write_human(result)
            return 0 if result["ok"] else 1
    result = Inspector(Path(args.project), strict=args.strict).run()
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        write_human(result)
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
