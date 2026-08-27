#!/usr/bin/env python3
"""Static gptme config/provider checker.

This helper parses gptme TOML configuration files, computes key config/env
precedence, and reports common provider/model mistakes. It performs no network
calls, does not import gptme, and never prints secret values.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import re
import stat
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

try:  # Python 3.11+
    import tomllib  # type: ignore[import-not-found]
except ModuleNotFoundError:  # pragma: no cover - Python 3.10 fallback
    try:
        import tomli as tomllib  # type: ignore[import-not-found,no-redef]
    except ModuleNotFoundError:  # pragma: no cover
        tomllib = None  # type: ignore[assignment]

SECRET_KEY_RE = re.compile(r"(KEY|TOKEN|SECRET|PASSWORD|CREDENTIAL|AUTH)", re.I)

PROVIDER_API_KEYS: dict[str, str] = {
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "openrouter": "OPENROUTER_API_KEY",
    "requesty": "REQUESTY_API_KEY",
    "gemini": "GEMINI_API_KEY",
    "groq": "GROQ_API_KEY",
    "xai": "XAI_API_KEY",
    "deepseek": "DEEPSEEK_API_KEY",
    "moonshot": "MOONSHOT_API_KEY",
    "azure": "AZURE_OPENAI_API_KEY",
    "nvidia": "NVIDIA_API_KEY",
}

AUTO_DETECT_ORDER = [
    "openai",
    "anthropic",
    "openrouter",
    "requesty",
    "gemini",
    "groq",
    "xai",
    "deepseek",
    "moonshot",
    "azure",
]

BUILTIN_PROVIDERS = set(PROVIDER_API_KEYS) | {
    "local",
    "gptme",
    "openai-subscription",
    "grok-subscription",
    "mock",
}

VALID_OPENROUTER_QUANTIZATIONS = {"fp16", "bf16", "fp8", "int8", "int4", "unknown"}

GLOBAL_KNOWN_TOP_LEVEL = {
    "user",
    "prompt",
    "env",
    "mcp",
    "providers",
    "lessons",
    "models",
    "plugins",
    "settings",
    "hooks",
    "plugin",
}
PROJECT_KNOWN_TOP_LEVEL = {
    "base_prompt",
    "prompt",
    "files",
    "exclude",
    "context_cmd",
    "hooks",
    "rag",
    "agent",
    "lessons",
    "context",
    "context_selector",
    "plugins",
    "architect",
    "subagent",
    "settings",
    "plugin",
    "env",
    "mcp",
}
CHAT_KNOWN_TOP_LEVEL = {"chat", "env", "mcp"}
CHAT_KNOWN_FIELDS = {
    "name",
    "model",
    "tools",
    "tool_format",
    "gear",
    "stream",
    "interactive",
    "no_confirm",
    "max_tokens",
    "temperature",
    "top_p",
    "workspace",
    "agent",
    "system_prompt",
}


@dataclass
class Finding:
    severity: str
    code: str
    message: str


@dataclass
class LoadedConfig:
    label: str
    path: str
    exists: bool
    data: dict[str, Any]


class Report:
    def __init__(self) -> None:
        self.findings: list[Finding] = []
        self.loaded: list[LoadedConfig] = []
        self.summary: dict[str, Any] = {}

    def add(self, severity: str, code: str, message: str) -> None:
        self.findings.append(Finding(severity, code, message))

    def has_errors(self) -> bool:
        return any(f.severity == "error" for f in self.findings)

    def has_warnings(self) -> bool:
        return any(f.severity == "warning" for f in self.findings)


def default_config_dir() -> Path:
    return Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "gptme"


def is_secret_key(key: str) -> bool:
    return bool(SECRET_KEY_RE.search(key))


def parse_env_assignment(raw: str) -> tuple[str, str]:
    if "=" not in raw:
        raise argparse.ArgumentTypeError("expected KEY=VALUE")
    key, value = raw.split("=", 1)
    key = key.strip()
    if not key:
        raise argparse.ArgumentTypeError("environment key must not be empty")
    return key, value


def load_toml_file(path: Path | None, label: str, report: Report) -> dict[str, Any]:
    if path is None:
        return {}
    resolved = Path(path).expanduser()
    if not resolved.exists():
        report.loaded.append(LoadedConfig(label, str(resolved), False, {}))
        return {}
    if tomllib is None:
        report.add(
            "error",
            "toml-parser-missing",
            "No TOML parser available; use Python 3.11+ or install tomli.",
        )
        report.loaded.append(LoadedConfig(label, str(resolved), True, {}))
        return {}
    try:
        data = tomllib.loads(resolved.read_text(encoding="utf-8"))
    except UnicodeDecodeError as exc:
        report.add("error", "toml-encoding", f"{label} is not valid UTF-8: {exc}")
        data = {}
    except Exception as exc:  # TOMLDecodeError class differs by parser
        report.add("error", "toml-parse", f"{label} failed to parse: {exc}")
        data = {}
    if not isinstance(data, dict):
        report.add("error", "toml-root", f"{label} did not parse to a TOML table")
        data = {}
    report.loaded.append(LoadedConfig(label, str(resolved), True, data))
    return data


def merge_config_data(main_config: dict[str, Any], local_config: dict[str, Any]) -> dict[str, Any]:
    """Mirror gptme's important local-override merge behavior."""
    merged = copy.deepcopy(main_config)
    for key, value in local_config.items():
        if key == "mcp" and isinstance(value, dict) and "servers" in value:
            merged.setdefault("mcp", {})
            merged["mcp"].setdefault("servers", [])
            main_servers = merged["mcp"]["servers"]
            main_by_name = {
                s.get("name"): s for s in main_servers if isinstance(s, dict) and "name" in s
            }
            for local_server in value.get("servers", []):
                if not isinstance(local_server, dict):
                    main_servers.append(local_server)
                    continue
                name = local_server.get("name")
                if name in main_by_name:
                    target = main_by_name[name]
                    if "env" in local_server:
                        target.setdefault("env", {})
                        if isinstance(target["env"], dict) and isinstance(local_server["env"], dict):
                            target["env"].update(local_server["env"])
                    for server_key, server_value in local_server.items():
                        if server_key not in {"name", "env"}:
                            target[server_key] = server_value
                else:
                    main_servers.append(local_server)
            for mcp_key, mcp_value in value.items():
                if mcp_key != "servers":
                    merged["mcp"][mcp_key] = mcp_value
        elif key == "providers" and isinstance(value, list):
            merged.setdefault("providers", [])
            main_providers = merged["providers"]
            main_by_name = {
                p.get("name"): p for p in main_providers if isinstance(p, dict) and "name" in p
            }
            for local_provider in value:
                if not isinstance(local_provider, dict):
                    main_providers.append(local_provider)
                    continue
                name = local_provider.get("name")
                if name in main_by_name:
                    main_by_name[name].update(local_provider)
                else:
                    main_providers.append(local_provider)
        elif isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = merge_config_data(merged[key], value)
        else:
            merged[key] = copy.deepcopy(value)
    return merged


def get_section(data: dict[str, Any], key: str) -> dict[str, Any]:
    value = data.get(key, {})
    return value if isinstance(value, dict) else {}


def get_nested(data: dict[str, Any], *keys: str) -> Any | None:
    cur: Any = data
    for key in keys:
        if not isinstance(cur, dict) or key not in cur:
            return None
        cur = cur[key]
    return cur


def scan_secret_keys(data: Any, path: str, report: Report, *, local_ok: bool) -> None:
    if isinstance(data, dict):
        for key, value in data.items():
            child = f"{path}.{key}" if path else str(key)
            if is_secret_key(str(key)) and value not in (None, ""):
                if local_ok:
                    report.add("info", "secret-local", f"{child} is present in a local/private config file (value hidden).")
                else:
                    report.add("warning", "secret-in-shared-config", f"{child} looks secret-like in a shared config file; move it to a local override or credential store.")
            scan_secret_keys(value, child, report, local_ok=local_ok)
    elif isinstance(data, list):
        for idx, item in enumerate(data):
            scan_secret_keys(item, f"{path}[{idx}]", report, local_ok=local_ok)


def check_unknown_keys(data: dict[str, Any], known: set[str], label: str, report: Report) -> None:
    unknown = sorted(set(data) - known)
    if unknown:
        report.add("warning", "unknown-config-keys", f"{label} contains unknown top-level key(s): {', '.join(unknown)}")


def build_env_lookup(
    *,
    supplied_env: dict[str, str],
    include_process_env: bool,
    chat: dict[str, Any],
    project: dict[str, Any],
    user: dict[str, Any],
) -> Any:
    process_env = dict(os.environ) if include_process_env else {}

    def lookup(key: str) -> tuple[str | None, str | None]:
        prefixed = key if key.startswith("GPTME_") else f"GPTME_{key}"
        bare = key.removeprefix("GPTME_") if key.startswith("GPTME_") else key

        for env_map, source_prefix in (
            (supplied_env, "supplied env"),
            (process_env, "process env"),
        ):
            if prefixed in env_map:
                return env_map[prefixed], f"{source_prefix}:{prefixed}"
            if bare in env_map:
                return env_map[bare], f"{source_prefix}:{bare}"

        for cfg, source in (
            (get_section(chat, "env"), "chat [env]"),
            (get_section(project, "env"), "project [env]"),
            (get_section(user, "env"), "global [env]"),
        ):
            value = cfg.get(bare)
            if value is not None:
                return str(value), source
        return None, None

    return lookup


def load_credentials(path: Path | None, report: Report) -> set[str]:
    if path is None:
        return set()
    data = load_toml_file(path, "credentials", report)
    if not data:
        return set()
    resolved = Path(path).expanduser()
    try:
        mode = stat.S_IMODE(resolved.stat().st_mode)
        if mode & 0o077:
            report.add(
                "warning",
                "credentials-permissions",
                "credential store is readable by group/others; tighten permissions to owner-only.",
            )
    except OSError:
        pass
    providers = get_section(data, "providers")
    result = {str(provider) for provider, value in providers.items() if isinstance(value, str) and value}
    if result:
        report.add("info", "credentials-present", f"credential store has provider key(s): {', '.join(sorted(result))} (values hidden).")
    return result


def check_providers(user_config: dict[str, Any], report: Report) -> set[str]:
    providers = user_config.get("providers", [])
    if providers in (None, []):
        return set()
    if not isinstance(providers, list):
        report.add("error", "providers-type", "global [[providers]] must be a list of tables.")
        return set()
    names: set[str] = set()
    for idx, provider in enumerate(providers):
        prefix = f"providers[{idx}]"
        if not isinstance(provider, dict):
            report.add("error", "provider-entry-type", f"{prefix} must be a table.")
            continue
        name = provider.get("name")
        base_url = provider.get("base_url")
        if not isinstance(name, str) or not name.strip():
            report.add("error", "provider-name", f"{prefix}.name must be a non-empty string.")
            continue
        if name in names:
            report.add("warning", "provider-duplicate", f"duplicate custom provider name {name!r}; entries merge by exact name in local overrides.")
        names.add(name)
        if name in BUILTIN_PROVIDERS:
            report.add("warning", "provider-name-collides", f"custom provider {name!r} collides with a built-in provider prefix.")
        if not isinstance(base_url, str) or not base_url.startswith(("http://", "https://")):
            report.add("error", "provider-base-url", f"custom provider {name!r} needs an http(s) base_url.")
        if provider.get("api_key"):
            report.add("warning", "provider-inline-key", f"custom provider {name!r} has inline api_key; ensure this is only in a local/private config (value hidden).")
        if not provider.get("default_model"):
            report.add("info", "provider-no-default-model", f"custom provider {name!r} has no default_model; use {name}/<model> explicitly.")
    return names


def selected_provider(model: str | None, custom_names: set[str]) -> str | None:
    if not model:
        return None
    if "/" in model:
        return model.split("/", 1)[0]
    if model in BUILTIN_PROVIDERS or model in custom_names:
        return model
    return None


def check_numeric_env(env_lookup: Any, report: Report) -> None:
    for key in ("LLM_API_TIMEOUT",):
        value, source = env_lookup(key)
        if value is not None:
            try:
                if float(value) <= 0:
                    raise ValueError
            except ValueError:
                report.add("warning", "env-numeric", f"{key} from {source} must be a positive number.")
    for key in ("GPTME_MAX_TOKENS", "GPTME_CONTEXT_LENGTH"):
        value, source = env_lookup(key)
        if value is not None:
            try:
                if int(value) <= 0:
                    raise ValueError
            except ValueError:
                report.add("warning", "env-integer", f"{key} from {source} must be a positive integer.")


def run_checks(args: argparse.Namespace) -> Report:
    report = Report()

    global_config_path = Path(args.global_config).expanduser() if args.global_config else None
    global_local_path = (
        Path(args.global_local).expanduser()
        if args.global_local
        else (global_config_path.parent / "config.local.toml" if global_config_path else None)
    )
    project_config_path = Path(args.project_config).expanduser() if args.project_config else None
    project_local_path = (
        Path(args.project_local).expanduser()
        if args.project_local
        else (project_config_path.parent / "gptme.local.toml" if project_config_path else None)
    )
    chat_config_path = Path(args.chat_config).expanduser() if args.chat_config else None
    credentials_path = None if args.no_credentials else Path(args.credentials).expanduser()

    global_main = load_toml_file(global_config_path, "global config", report)
    global_local = load_toml_file(global_local_path, "global local config", report)
    project_main = load_toml_file(project_config_path, "project config", report)
    project_local = load_toml_file(project_local_path, "project local config", report)
    chat_config = load_toml_file(chat_config_path, "chat config", report)

    user_config = merge_config_data(global_main, global_local)
    project_config = merge_config_data(project_main, project_local)

    if global_main:
        check_unknown_keys(global_main, GLOBAL_KNOWN_TOP_LEVEL, "global config", report)
        scan_secret_keys(global_main, "global", report, local_ok=False)
    if global_local:
        scan_secret_keys(global_local, "global-local", report, local_ok=True)
    if project_main:
        check_unknown_keys(project_main, PROJECT_KNOWN_TOP_LEVEL, "project config", report)
        scan_secret_keys(project_main, "project", report, local_ok=False)
        if "providers" in project_main:
            report.add("warning", "providers-in-project", "custom [[providers]] are user/global config entries; project config may ignore this top-level key.")
    if project_local:
        scan_secret_keys(project_local, "project-local", report, local_ok=True)
    if chat_config:
        check_unknown_keys(chat_config, CHAT_KNOWN_TOP_LEVEL, "chat config", report)
        chat_section = get_section(chat_config, "chat")
        unknown_chat = sorted(set(chat_section) - CHAT_KNOWN_FIELDS)
        if unknown_chat:
            report.add("error", "unknown-chat-keys", f"chat config [chat] contains unknown key(s): {', '.join(unknown_chat)}")

    custom_provider_names = check_providers(user_config, report)
    credential_providers = load_credentials(credentials_path, report)

    supplied_env = dict(parse_env_assignment(item) for item in args.env)
    env_lookup = build_env_lookup(
        supplied_env=supplied_env,
        include_process_env=args.include_process_env,
        chat=chat_config,
        project=project_config,
        user=user_config,
    )

    chat_model = get_nested(chat_config, "chat", "model")
    models_default = get_nested(user_config, "models", "default")
    env_model, env_model_source = env_lookup("MODEL")

    if models_default is not None and not isinstance(models_default, str):
        report.add("warning", "models-default-type", "[models].default should be a string.")
        models_default = None
    if chat_model is not None and not isinstance(chat_model, str):
        report.add("error", "chat-model-type", "[chat].model should be a string.")
        chat_model = None

    if models_default and env_model and models_default != env_model:
        report.add(
            "warning",
            "model-default-conflict",
            "[models].default and MODEL differ; [models].default wins unless CLI/chat model overrides it.",
        )

    selected_model: str | None
    selected_source: str | None
    if chat_model:
        selected_model, selected_source = chat_model, "chat [chat].model"
    elif models_default:
        selected_model, selected_source = models_default, "global [models].default"
    elif env_model:
        selected_model, selected_source = env_model, env_model_source
    else:
        selected_model = None
        selected_source = None

    auto_provider = None
    if not selected_model:
        for provider in AUTO_DETECT_ORDER:
            env_var = PROVIDER_API_KEYS[provider]
            value, source = env_lookup(env_var)
            if value:
                auto_provider = provider
                selected_model = provider
                selected_source = f"auto-detected from {source}"
                break
        if auto_provider is None:
            for provider in sorted(credential_providers):
                auto_provider = provider
                selected_model = provider
                selected_source = "auto-detected from credential store"
                break

    if selected_model:
        report.summary["selected_model_without_cli_override"] = selected_model
        report.summary["selected_source"] = selected_source
    else:
        report.add("warning", "no-model", "No model/default/API-key source found for static auto-detection.")

    provider = selected_provider(selected_model, custom_provider_names)
    report.summary["selected_provider"] = provider

    if selected_model and provider is None:
        report.add("warning", "model-prefix", f"selected model {selected_model!r} has no recognized provider prefix in this static check.")

    if provider == "local":
        base_value, base_source = env_lookup("OPENAI_API_BASE")
        if not base_value:
            base_value, base_source = env_lookup("OPENAI_BASE_URL")
        if not base_value:
            report.add("error", "local-base-url", "local/... model selected but OPENAI_BASE_URL is not configured.")
        else:
            report.add("info", "local-base-url", f"local provider base URL is configured via {base_source} (value hidden).")
        report.add("info", "local-summary", "local provider has no separate summary model; gptme uses the selected local model for summaries.")
    elif provider in PROVIDER_API_KEYS:
        env_var = PROVIDER_API_KEYS[provider]
        value, source = env_lookup(env_var)
        if not value and provider not in credential_providers:
            report.add("warning", "provider-key-missing", f"provider {provider!r} selected but {env_var} was not found in env/config or credential store.")
        else:
            source_text = source or "credential store"
            report.add("info", "provider-key-present", f"provider {provider!r} has a key source: {source_text} (value hidden).")
        if provider == "azure":
            endpoint, endpoint_source = env_lookup("AZURE_OPENAI_ENDPOINT")
            if not endpoint:
                report.add("warning", "azure-endpoint", "azure selected but AZURE_OPENAI_ENDPOINT is not configured.")
            else:
                report.add("info", "azure-endpoint", f"AZURE_OPENAI_ENDPOINT is configured via {endpoint_source} (value hidden).")
    elif provider == "gptme":
        cloud_key, cloud_key_source = env_lookup("GPTME_CLOUD_API_KEY")
        if cloud_key:
            report.add("info", "gptme-cloud-key", f"gptme cloud key source present via {cloud_key_source} (value hidden).")
        else:
            report.add("info", "gptme-cloud-auth", "gptme provider may use a stored cloud token; static checker did not validate live auth.")
    elif provider in {"openai-subscription", "grok-subscription"}:
        report.add("info", "subscription-auth", f"{provider} uses local OAuth token files; static checker does not validate token freshness.")
    elif provider in custom_provider_names:
        report.add("info", "custom-provider-selected", f"custom provider {provider!r} selected; static config entry exists.")

    base_url, base_url_source = env_lookup("OPENAI_BASE_URL")
    if base_url and provider not in {"local", None}:
        report.add("info", "openai-base-url-scope", f"OPENAI_BASE_URL is configured via {base_url_source}, but gptme applies it only to local/... models.")

    data_collection, dc_source = env_lookup("OPENROUTER_DATA_COLLECTION")
    if data_collection and data_collection not in {"allow", "deny"}:
        report.add("warning", "openrouter-data-collection", f"OPENROUTER_DATA_COLLECTION from {dc_source} is {data_collection!r}; expected allow or deny.")
    quantization, q_source = env_lookup("OPENROUTER_QUANTIZATION")
    if quantization:
        parsed = [q.strip() for q in quantization.split(",") if q.strip()]
        invalid = [q for q in parsed if q not in VALID_OPENROUTER_QUANTIZATIONS]
        if invalid:
            report.add("warning", "openrouter-quantization", f"OPENROUTER_QUANTIZATION from {q_source} contains unknown value(s): {', '.join(invalid)}")

    check_numeric_env(env_lookup, report)

    report.summary["loaded_files"] = [asdict(item) | {"data": "<parsed>" if item.exists and item.data else {}} for item in report.loaded]
    return report


def print_human(report: Report) -> None:
    print("gptme static configuration report")
    print("=" * 34)
    print()
    print("Loaded files:")
    for item in report.loaded:
        status = "present" if item.exists else "missing"
        print(f"- {item.label}: {status} ({item.path})")
    print()
    selected = report.summary.get("selected_model_without_cli_override")
    if selected:
        print("Effective model without CLI override:")
        print(f"- model/provider request: {selected}")
        print(f"- source: {report.summary.get('selected_source')}")
        print(f"- provider prefix: {report.summary.get('selected_provider') or 'unknown'}")
    else:
        print("Effective model without CLI override: not resolved")
    print()

    if not report.findings:
        print("Findings: none")
        return
    print("Findings:")
    order = {"error": 0, "warning": 1, "info": 2}
    for finding in sorted(report.findings, key=lambda f: (order.get(f.severity, 9), f.code, f.message)):
        print(f"- [{finding.severity}] {finding.code}: {finding.message}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Statically validate gptme TOML/env/provider configuration without "
            "API calls and without printing secret values."
        )
    )
    parser.add_argument(
        "--global-config",
        default="~/.config/gptme/config.toml",
        help="Path to global config.toml (default: %(default)s).",
    )
    parser.add_argument(
        "--global-local",
        help="Path to config.local.toml (default: sibling of --global-config).",
    )
    parser.add_argument("--project-config", help="Path to project gptme.toml.")
    parser.add_argument(
        "--project-local",
        help="Path to gptme.local.toml (default: sibling of --project-config).",
    )
    parser.add_argument("--chat-config", help="Path to a chat log config.toml.")
    parser.add_argument(
        "--credentials",
        default=str(default_config_dir() / "credentials.toml"),
        help="Path to credentials.toml (default: platform gptme config directory).",
    )
    parser.add_argument(
        "--no-credentials",
        action="store_true",
        help="Do not inspect a credential store file.",
    )
    parser.add_argument(
        "--env",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="Supply an env value for static resolution; may be repeated. Values are never printed if secret-like.",
    )
    parser.add_argument(
        "--include-process-env",
        action="store_true",
        help="Consider the current process environment as an input source. Values are not dumped.",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON report.")
    parser.add_argument(
        "--strict-warnings",
        action="store_true",
        help="Exit non-zero when warnings are present, not only errors.",
    )
    args = parser.parse_args(argv)

    try:
        # Validate --env syntax before checks.
        for item in args.env:
            parse_env_assignment(item)
    except argparse.ArgumentTypeError as exc:
        parser.error(str(exc))

    report = run_checks(args)
    if args.json:
        payload = {
            "summary": report.summary,
            "findings": [asdict(finding) for finding in report.findings],
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print_human(report)

    if report.has_errors() or (args.strict_warnings and report.has_warnings()):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
