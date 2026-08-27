#!/usr/bin/env python3
"""Safe static validator for AReaL 2.0 service CLI command text.

The checker deliberately does not import AReaL, start services, start training,
contact HTTP endpoints, read model files, or expand shell variables. It only
parses command strings, TOML config files, backend specs, and nested
engine/proxy argument strings.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python < 3.11 fallback
    tomllib = None  # type: ignore[assignment]


DEFAULT_INF_KEY = "areal-admin-key"
DEFAULT_AGENT_KEY = "areal-agent-admin"
DEFAULT_KEYS = {DEFAULT_INF_KEY, DEFAULT_AGENT_KEY, "areal-admin-key"}
LOCAL_HOSTS = {"127.0.0.1", "localhost", "::1"}
SHELL_CONTROL_TOKENS = {"&&", "||", ";", "|", "<", ">", ">>", "2>", "2>>"}

PROXY_KNOWN_FLAGS = {
    "--request-timeout": True,
    "--set-reward-finish-timeout": True,
    "--tool-call-parser": True,
    "--reasoning-parser": True,
    "--engine-max-tokens": True,
    "--chat-template-type": True,
}

LOG_LEVELS = {"debug", "info", "warning", "error"}
ROUTING_STRATEGIES = {"round_robin", "least_busy"}


@dataclass
class CheckReport:
    subject: str
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    info: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors

    def add_error(self, msg: str) -> None:
        self.errors.append(msg)

    def add_warning(self, msg: str) -> None:
        self.warnings.append(msg)

    def add_info(self, msg: str) -> None:
        self.info.append(msg)

    def as_dict(self) -> dict[str, Any]:
        return {
            "subject": self.subject,
            "ok": self.ok,
            "errors": self.errors,
            "warnings": self.warnings,
            "info": self.info,
        }


@dataclass
class ParsedOptions:
    options: dict[str, Any] = field(default_factory=dict)
    positionals: list[str] = field(default_factory=list)


def _basename(cmd: str) -> str:
    return os.path.basename(cmd)


def _flag_key(flag: str) -> str:
    return flag.lstrip("-").replace("-", "_")


def _parse_options(
    tokens: list[str],
    *,
    value_flags: set[str],
    bool_flags: set[str],
    short_aliases: dict[str, str] | None = None,
    allow_unknown_positionals: bool = False,
    report: CheckReport,
) -> ParsedOptions:
    """Small option parser for validation only.

    It accepts ``--flag value`` and ``--flag=value`` forms. It is stricter than
    Click for known command options so that common quoting mistakes become
    visible before a user starts a service.
    """

    short_aliases = short_aliases or {}
    out = ParsedOptions()
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        if tok == "--":
            out.positionals.extend(tokens[i + 1 :])
            break
        if tok in short_aliases:
            full = short_aliases[tok]
            if full in bool_flags:
                out.options[_flag_key(full)] = True
                i += 1
                continue
            if full in value_flags:
                if i + 1 >= len(tokens):
                    report.add_error(f"{tok} requires a value")
                    i += 1
                    continue
                out.options[_flag_key(full)] = tokens[i + 1]
                i += 2
                continue
        if tok.startswith("--"):
            if "=" in tok:
                flag, value = tok.split("=", 1)
            else:
                flag, value = tok, None
            if flag in bool_flags:
                if value is not None:
                    report.add_warning(f"{flag} is a boolean flag; value {value!r} is ignored by this validator")
                out.options[_flag_key(flag)] = True
                i += 1
                continue
            if flag in value_flags:
                if value is None:
                    if i + 1 >= len(tokens):
                        report.add_error(f"{flag} requires a value")
                        i += 1
                        continue
                    value = tokens[i + 1]
                    i += 2
                else:
                    i += 1
                out.options[_flag_key(flag)] = value
                continue
            report.add_error(f"unknown option for this command: {flag}")
            i += 1
            continue
        out.positionals.append(tok)
        i += 1

    if out.positionals and not allow_unknown_positionals:
        report.add_error(
            "unexpected positional tokens: "
            + " ".join(shlex.quote(x) for x in out.positionals)
            + "; if these were nested engine/proxy flags, quote the whole --engine-args/--proxy-args value"
        )
    return out


def _parse_positive_int(value: Any, name: str, report: CheckReport, *, min_value: int = 1, max_value: int | None = None) -> int | None:
    try:
        ivalue = int(value)
    except (TypeError, ValueError):
        report.add_error(f"{name} must be an integer, got {value!r}")
        return None
    if ivalue < min_value:
        report.add_error(f"{name} must be >= {min_value}, got {ivalue}")
    if max_value is not None and ivalue > max_value:
        report.add_error(f"{name} must be <= {max_value}, got {ivalue}")
    return ivalue


def _parse_float(value: Any, name: str, report: CheckReport, *, min_value: float | None = None) -> float | None:
    try:
        fvalue = float(value)
    except (TypeError, ValueError):
        report.add_error(f"{name} must be a number, got {value!r}")
        return None
    if min_value is not None and fvalue < min_value:
        report.add_error(f"{name} must be >= {min_value}, got {fvalue}")
    return fvalue


def validate_backend_spec(spec: str, report: CheckReport, *, context: str = "backend") -> dict[str, int | str] | None:
    if not spec:
        report.add_error(f"{context} spec is empty")
        return None
    if ":" in spec:
        engine, rest = spec.split(":", 1)
    else:
        engine, rest = spec, ""
        report.add_warning(f"{context} spec {spec!r} has no explicit d/t/p allocation; verify this is intentional")
    if engine not in {"sglang", "vllm"}:
        report.add_error(f"{context} engine must be 'sglang' or 'vllm', got {engine!r}")
        return None

    result: dict[str, int | str] = {"engine": engine, "d": 1, "t": 1, "p": 1}
    if rest:
        pos = 0
        seen: set[str] = set()
        for match in re.finditer(r"([dtp])(\d+)", rest):
            if match.start() != pos:
                report.add_error(f"invalid {context} allocation segment near {rest[pos:]!r} in {spec!r}")
                return None
            key, raw = match.groups()
            if key in seen:
                report.add_error(f"duplicate allocation key {key!r} in {spec!r}")
            seen.add(key)
            value = int(raw)
            if value < 1:
                report.add_error(f"allocation {key} must be >= 1 in {spec!r}")
            result[key] = value
            pos = match.end()
        if pos != len(rest):
            report.add_error(f"invalid {context} allocation tail {rest[pos:]!r} in {spec!r}")
            return None
    if int(result.get("p", 1)) > 1:
        report.add_error("pipeline parallelism p>1 is not supported by the local `areal inf` registration path")
    gpus = int(result.get("d", 1)) * int(result.get("t", 1)) * int(result.get("p", 1))
    report.add_info(f"{context}: engine={engine}, dp={result['d']}, tp={result['t']}, pp={result['p']}, estimated worker GPUs={gpus}")
    return result


def validate_nested_args(value: str, report: CheckReport, *, label: str, known_flags: dict[str, bool] | None = None) -> list[str]:
    try:
        parts = shlex.split(value) if value else []
    except ValueError as exc:
        report.add_error(f"{label} cannot be parsed as shell-style args: {exc}")
        return []
    report.add_info(f"{label}: parsed {len(parts)} token(s): {parts!r}")
    if known_flags is not None:
        i = 0
        while i < len(parts):
            tok = parts[i]
            if tok.startswith("--"):
                flag = tok.split("=", 1)[0]
                expects_value = known_flags.get(flag)
                if expects_value is None:
                    report.add_warning(f"{label}: unknown proxy flag {flag!r}; verify against your AReaL version")
                    i += 1
                    continue
                if expects_value and "=" not in tok:
                    if i + 1 >= len(parts) or parts[i + 1].startswith("--"):
                        report.add_warning(f"{label}: {flag} usually expects a value")
                    else:
                        i += 2
                        continue
            i += 1
    return parts


def _host_nonlocal(host: str | None) -> bool:
    if not host:
        return False
    return host not in LOCAL_HOSTS and not host.startswith("127.")


def _check_admin_key(opts: dict[str, Any], report: CheckReport, *, default_key: str, host_key: str = "host") -> None:
    key = str(opts.get("admin_api_key") or default_key)
    host = str(opts.get(host_key) or "127.0.0.1")
    if "${" in key:
        report.add_warning("TOML/CLI values are not shell-expanded by AReaL; replace ${...} placeholders before live execution")
    if key in DEFAULT_KEYS:
        if _host_nonlocal(host):
            report.add_error(f"non-local bind host {host!r} with demo admin key {key!r} is unsafe and may be rejected")
        else:
            report.add_warning(f"using demo admin key {key!r}; replace it outside isolated local development")


def _validate_choice(opts: dict[str, Any], key: str, choices: set[str], report: CheckReport) -> None:
    if key in opts and str(opts[key]) not in choices:
        report.add_error(f"--{key.replace('_', '-')} must be one of {sorted(choices)}, got {opts[key]!r}")


def _validate_inf(verb: str, args: list[str], report: CheckReport) -> None:
    side_effects = {"run", "register", "deregister", "stop"}
    if verb in side_effects:
        report.add_warning(f"`areal inf {verb}` is side-effecting; this script only validates the command text")

    common_service_value = {"--service"}
    if verb == "run":
        opts = _parse_options(
            args,
            value_flags={
                "--service", "--port", "--host", "--admin-api-key", "--routing-strategy",
                "--log-level", "--launch-timeout", "--model", "--backend", "--model-path",
                "--tokenizer-path", "--engine-args", "--proxy-args", "--model-health-timeout",
                "--scheduler",
            },
            bool_flags={"--detach", "--force"},
            short_aliases={"-d": "--detach"},
            report=report,
        ).options
        _check_admin_key(opts, report, default_key=DEFAULT_INF_KEY)
        _validate_choice(opts, "routing_strategy", ROUTING_STRATEGIES, report)
        _validate_choice(opts, "log_level", LOG_LEVELS, report)
        if "port" in opts:
            _parse_positive_int(opts["port"], "--port", report, min_value=1, max_value=65535)
        if "launch_timeout" in opts:
            _parse_float(opts["launch_timeout"], "--launch-timeout", report, min_value=0.0)
        if "scheduler" in opts and opts["scheduler"] != "local":
            report.add_error("current `areal inf run --scheduler` choice is only 'local'")
        if opts.get("backend") and not opts.get("model"):
            report.add_error("model registration flags on `areal inf run` require --model")
        if opts.get("model"):
            if not opts.get("backend"):
                report.add_error("--model startup registration requires --backend")
            if not opts.get("model_path"):
                report.add_error("--model startup registration requires --model-path")
        if opts.get("backend"):
            validate_backend_spec(str(opts["backend"]), report)
        if "engine_args" in opts:
            validate_nested_args(str(opts["engine_args"]), report, label="--engine-args")
        if "proxy_args" in opts:
            validate_nested_args(str(opts["proxy_args"]), report, label="--proxy-args", known_flags=PROXY_KNOWN_FLAGS)
        return

    if verb == "register":
        opts = _parse_options(
            args,
            value_flags={
                "--model-name", "--service", "--backend", "--model-path", "--tokenizer-path",
                "--engine-args", "--proxy-args", "--model-health-timeout", "--log-level",
            },
            bool_flags=set(),
            report=report,
        ).options
        for required in ("model_name", "backend", "model_path"):
            if not opts.get(required):
                report.add_error(f"areal inf register requires --{required.replace('_', '-')}")
        if opts.get("backend"):
            validate_backend_spec(str(opts["backend"]), report)
        if "engine_args" in opts:
            validate_nested_args(str(opts["engine_args"]), report, label="--engine-args")
        if "proxy_args" in opts:
            validate_nested_args(str(opts["proxy_args"]), report, label="--proxy-args", known_flags=PROXY_KNOWN_FLAGS)
        _validate_choice(opts, "log_level", LOG_LEVELS, report)
        return

    if verb == "deregister":
        opts = _parse_options(
            args,
            value_flags={"--model-name", "--service", "--grace"},
            bool_flags={"--force"},
            report=report,
        ).options
        if not opts.get("model_name"):
            report.add_error("areal inf deregister requires --model-name")
        if "grace" in opts:
            _parse_float(opts["grace"], "--grace", report, min_value=0.0)
        return

    if verb == "stop":
        opts = _parse_options(
            args,
            value_flags={"--service", "--grace"},
            bool_flags={"--force", "--keep-state"},
            report=report,
        ).options
        if "grace" in opts:
            _parse_float(opts["grace"], "--grace", report, min_value=0.0)
        return

    if verb in {"status", "models"}:
        _parse_options(args, value_flags=common_service_value, bool_flags={"--json"}, report=report)
        report.add_info(f"`areal inf {verb}` performs live state/HTTP inspection if executed")
        return

    if verb == "ps":
        _parse_options(args, value_flags=set(), bool_flags={"--json", "--all"}, report=report)
        report.add_info("`areal inf ps` reads local state; use --all to include stale services")
        return

    if verb == "logs":
        opts = _parse_options(
            args,
            value_flags={"--service", "--component", "--lines"},
            bool_flags={"--follow"},
            short_aliases={"-f": "--follow", "-n": "--lines"},
            report=report,
        ).options
        if "lines" in opts:
            _parse_positive_int(opts["lines"], "--lines", report)
        if opts.get("follow"):
            report.add_warning("--follow can run indefinitely because it tails logs with follow mode")
        return

    if verb in {"--help", "-h"}:
        report.add_info("help command is safe")
        return
    report.add_error(f"unknown `areal inf` command: {verb}")


def _validate_agent(verb: str, args: list[str], report: CheckReport) -> None:
    if verb in {"run", "stop"}:
        report.add_warning(f"`areal agent {verb}` is side-effecting; this script only validates the command text")

    if verb == "run":
        opts = _parse_options(
            args,
            value_flags={
                "--service", "--agent", "--num-pairs", "--admin-api-key", "--setup-timeout",
                "--health-poll-interval", "--drain-timeout", "--session-timeout", "--log-level",
            },
            bool_flags={"--force"},
            report=report,
        ).options
        if not opts.get("agent"):
            report.add_error("areal agent run requires --agent")
        if "num_pairs" in opts:
            _parse_positive_int(opts["num_pairs"], "--num-pairs", report)
        for key in ("setup_timeout", "health_poll_interval", "drain_timeout", "session_timeout"):
            if key in opts:
                _parse_float(opts[key], f"--{key.replace('_', '-')}", report, min_value=0.0)
        _validate_choice(opts, "log_level", LOG_LEVELS, report)
        _check_admin_key(opts, report, default_key=DEFAULT_AGENT_KEY)
        return

    if verb == "stop":
        opts = _parse_options(
            args,
            value_flags={"--service", "--grace-period"},
            bool_flags={"--keep-state", "--force"},
            report=report,
        ).options
        if "grace_period" in opts:
            _parse_float(opts["grace_period"], "--grace-period", report, min_value=0.0)
        return

    if verb == "status":
        opts = _parse_options(
            args,
            value_flags={"--service", "--interval"},
            bool_flags={"--watch", "--json"},
            report=report,
        ).options
        if "interval" in opts:
            _parse_float(opts["interval"], "--interval", report, min_value=0.0)
        if opts.get("watch"):
            report.add_warning("--watch can run indefinitely")
        return

    if verb == "ps":
        _parse_options(args, value_flags=set(), bool_flags={"--json", "--all"}, report=report)
        return

    if verb == "logs":
        opts = _parse_options(
            args,
            value_flags={"--service", "--component", "--lines"},
            bool_flags={"--follow"},
            short_aliases={"-f": "--follow", "-n": "--lines"},
            report=report,
        ).options
        if "lines" in opts:
            _parse_positive_int(opts["lines"], "--lines", report)
        if opts.get("follow"):
            report.add_warning("--follow can run indefinitely because it tails logs with follow mode")
        return

    if verb in {"new_session", "switch_session", "chat", "reward"}:
        report.add_error(f"`areal agent {verb}` is not a registered command; use agent/inference HTTP endpoints")
        return
    if verb in {"--help", "-h"}:
        report.add_info("help command is safe")
        return
    report.add_error(f"unknown `areal agent` command: {verb}")


def _validate_train(verb: str, args: list[str], report: CheckReport) -> None:
    if verb != "run":
        if verb in {"--help", "-h"}:
            report.add_info("help command is safe")
        else:
            report.add_error(f"unknown `areal train` command: {verb}")
        return
    report.add_warning("`areal train run` starts a user training driver if executed; this script only validates invocation shape")
    parsed = _parse_options(
        args,
        value_flags={"--config", "--driver"},
        bool_flags=set(),
        allow_unknown_positionals=True,
        report=report,
    )
    opts = parsed.options
    if not opts.get("config"):
        report.add_error("areal train run requires --config")
    elif not any(ch in str(opts["config"]) for ch in "<>$"):
        if not Path(str(opts["config"])).exists():
            report.add_warning(f"config path {opts['config']!r} does not exist from the current working directory")
    if not opts.get("driver"):
        report.add_error("areal train run requires --driver")
    elif ":" not in str(opts["driver"]):
        report.add_error("--driver must be in module.path:func form")
    if parsed.positionals:
        report.add_info(f"training overrides captured: {parsed.positionals!r}")


def validate_areal_command(tokens: list[str], report: CheckReport) -> None:
    if len(tokens) == 1 or tokens[1] in {"--help", "-h", "--version"}:
        report.add_info("top-level `areal` help/version command is safe")
        return
    group = tokens[1]
    rest = tokens[2:]
    if group in {"inf", "agent"}:
        # Group-level --config is accepted before the verb. Parse it manually
        # so both `--config file` and `--config=file` leave the following verb
        # intact for command-specific validation.
        while rest:
            tok = rest[0]
            if tok == "--config":
                if len(rest) < 2:
                    report.add_error("--config requires a value")
                    return
                report.add_info(f"group config file supplied: {rest[1]!r}")
                rest = rest[2:]
                continue
            if tok.startswith("--config="):
                report.add_info(f"group config file supplied: {tok.split('=', 1)[1]!r}")
                rest = rest[1:]
                continue
            break
        if not rest:
            report.add_error(f"areal {group} requires a command such as run/status/ps/logs")
            return
        verb, args = rest[0], rest[1:]
        if group == "inf":
            _validate_inf(verb, args, report)
        else:
            _validate_agent(verb, args, report)
        return
    if group == "train":
        if not rest:
            report.add_error("areal train requires a command such as run")
            return
        _validate_train(rest[0], rest[1:], report)
        return
    report.add_error(f"unknown areal command group {group!r}; expected inf, agent, or train")


DIRECT_MODULE_SPECS: dict[str, dict[str, Any]] = {
    "areal.v2.inference_service.gateway": {
        "default_key": DEFAULT_INF_KEY,
        "values": {"--host", "--port", "--admin-api-key", "--router-addr", "--router-timeout", "--forward-timeout", "--log-level"},
        "required": set(),
    },
    "areal.v2.inference_service.router": {
        "default_key": DEFAULT_INF_KEY,
        "values": {"--host", "--port", "--admin-api-key", "--poll-interval", "--worker-health-timeout", "--routing-strategy", "--log-level"},
        "required": set(),
    },
    "areal.v2.inference_service.data_proxy": {
        "default_key": DEFAULT_INF_KEY,
        "values": {"--host", "--port", "--backend-addr", "--backend-type", "--tokenizer-path", "--log-level", "--request-timeout", "--set-reward-finish-timeout", "--admin-api-key", "--callback-server-addr", "--tool-call-parser", "--reasoning-parser", "--engine-max-tokens", "--chat-template-type"},
        "required": {"tokenizer_path"},
    },
    "areal.v2.agent_service.gateway": {
        "default_key": DEFAULT_AGENT_KEY,
        "values": {"--router-addr", "--host", "--port", "--admin-api-key", "--router-timeout", "--forward-timeout", "--log-level"},
        "required": {"router_addr"},
    },
    "areal.v2.agent_service.router": {
        "default_key": DEFAULT_AGENT_KEY,
        "values": {"--host", "--port", "--admin-api-key", "--poll-interval", "--worker-health-timeout", "--log-level"},
        "required": set(),
    },
    "areal.v2.agent_service.data_proxy": {
        "default_key": DEFAULT_AGENT_KEY,
        "values": {"--worker-addr", "--host", "--port", "--request-timeout", "--session-timeout", "--log-level"},
        "required": {"worker_addr"},
    },
    "areal.v2.agent_service.worker": {
        "default_key": DEFAULT_AGENT_KEY,
        "values": {"--agent", "--host", "--port", "--log-level"},
        "required": {"agent"},
    },
    "areal.v2.training_service.gateway": {
        "default_key": DEFAULT_INF_KEY,
        "values": {"--host", "--port", "--admin-api-key", "--router-addr", "--router-timeout", "--forward-timeout", "--log-level"},
        "required": set(),
    },
    "areal.v2.training_service.router": {
        "default_key": DEFAULT_INF_KEY,
        "values": {"--host", "--port", "--admin-api-key", "--poll-interval", "--worker-health-timeout", "--log-level"},
        "required": set(),
    },
    "areal.v2.training_service.data_proxy": {
        "default_key": DEFAULT_INF_KEY,
        "values": {"--host", "--port", "--worker-addrs", "--admin-api-key", "--idle-timeout", "--warmup-timeout", "--request-timeout", "--log-level"},
        "required": {"worker_addrs"},
    },
    "areal.v2.training_service.worker": {
        "default_key": DEFAULT_INF_KEY,
        "values": {"--host", "--port", "--admin-api-key", "--log-level"},
        "required": set(),
    },
    "areal.v2.weight_update.gateway": {
        "default_key": DEFAULT_INF_KEY,
        "values": {"--host", "--port", "--admin-api-key", "--init-timeout", "--update-timeout", "--log-level"},
        "required": set(),
    },
}


def validate_direct_module(module: str, args: list[str], report: CheckReport) -> None:
    report.add_warning(f"`python -m {module}` starts a service if executed; this script only validates command text")
    spec = DIRECT_MODULE_SPECS.get(module)
    if spec is None:
        if module.startswith("areal.v2.") and module.endswith(".guard"):
            report.add_warning("guard module detected; validate its arguments against the RPC guard contract before live use")
            return
        report.add_error(f"unsupported direct AReaL service module: {module}")
        return
    opts = _parse_options(args, value_flags=set(spec["values"]), bool_flags=set(), allow_unknown_positionals=False, report=report).options
    for required in spec["required"]:
        if not opts.get(required):
            report.add_error(f"python -m {module} requires --{required.replace('_', '-')}")
    if "port" in opts:
        _parse_positive_int(opts["port"], "--port", report, min_value=1, max_value=65535)
    _validate_choice(opts, "log_level", LOG_LEVELS, report)
    if "routing_strategy" in opts:
        _validate_choice(opts, "routing_strategy", ROUTING_STRATEGIES, report)
    if "backend_type" in opts and opts["backend_type"] not in {"sglang", "vllm"}:
        report.add_error("--backend-type must be 'sglang' or 'vllm'")
    if "chat_template_type" in opts and opts["chat_template_type"] not in {"hf", "concat"}:
        report.add_error("--chat-template-type must be 'hf' or 'concat'")
    if "--admin-api-key" in spec["values"]:
        _check_admin_key(opts, report, default_key=str(spec["default_key"]), host_key="host")


def validate_command(command: str) -> CheckReport:
    report = CheckReport(subject=command)
    try:
        tokens = shlex.split(command)
    except ValueError as exc:
        report.add_error(f"command cannot be parsed by shlex: {exc}")
        return report
    if not tokens:
        report.add_error("empty command")
        return report
    if any(tok in SHELL_CONTROL_TOKENS for tok in tokens):
        report.add_warning("shell control token detected; validate each command separately before live execution")

    # Strip common wrappers without executing them.
    if len(tokens) >= 2 and tokens[0] == "uv" and tokens[1] == "run":
        report.add_info("stripped leading `uv run` wrapper for static validation")
        tokens = tokens[2:]
    if not tokens:
        report.add_error("no command remains after wrapper stripping")
        return report

    first = _basename(tokens[0])
    if first == "areal":
        validate_areal_command(tokens, report)
        return report
    if first in {"python", "python3"} or first.startswith("python"):
        if len(tokens) >= 3 and tokens[1] == "-m":
            module = tokens[2]
            if module == "areal.v2.cli.main":
                validate_areal_command(["areal", *tokens[3:]], report)
            else:
                validate_direct_module(module, tokens[3:], report)
            return report
    report.add_warning("unsupported command family; checker only understands `areal ...` and `python -m areal.v2...` service commands")
    return report


INF_ALLOWED: dict[str, set[str]] = {
    "default": {"service", "admin_api_key", "log_level"},
    "launch": {"gateway_host", "gateway_port", "routing_strategy", "launch_timeout"},
    "scheduler": {"type"},
    "register.internal": {"backend", "model_health_timeout", "engine_args", "proxy_args"},
}
AGENT_ALLOWED: dict[str, set[str]] = {
    "default": {"service", "admin_api_key", "log_level"},
    "run": {"agent", "num_pairs", "setup_timeout", "health_poll_interval", "drain_timeout", "session_timeout"},
}


def _flatten_toml(data: dict[str, Any], parent: str = "") -> dict[tuple[str, str], Any]:
    out: dict[tuple[str, str], Any] = {}
    for key, value in data.items():
        section = f"{parent}.{key}" if parent else key
        if isinstance(value, dict):
            out.update(_flatten_toml(value, section))
        else:
            out[(parent, key)] = value
    return out


def _guess_config_type(flat: dict[tuple[str, str], Any]) -> str:
    sections = {s for s, _ in flat}
    if "register.internal" in sections or "launch" in sections or "scheduler" in sections:
        return "inf"
    if "run" in sections:
        return "agent"
    return "inf"


def validate_config(path: Path, config_type: str) -> CheckReport:
    report = CheckReport(subject=f"config:{path}")
    if tomllib is None:
        report.add_error("tomllib is unavailable; use Python 3.11+ to validate TOML configs")
        return report
    if not path.exists():
        report.add_error(f"config file does not exist: {path}")
        return report
    try:
        data = tomllib.loads(path.read_text())
    except Exception as exc:
        report.add_error(f"failed to parse TOML: {exc}")
        return report
    flat = _flatten_toml(data)
    ctype = _guess_config_type(flat) if config_type == "auto" else config_type
    allowed = INF_ALLOWED if ctype == "inf" else AGENT_ALLOWED
    report.add_info(f"validating as {ctype} config")
    for (section, key), value in sorted(flat.items()):
        if section not in allowed or key not in allowed[section]:
            report.add_warning(f"unknown or unbound key [{section}].{key}; AReaL config loader will ignore unbound keys")
        if isinstance(value, str) and "${" in value:
            report.add_warning(f"[{section}].{key} contains a shell-style placeholder; AReaL TOML loader does not expand environment variables")
    if ctype == "inf":
        defaults = data.get("default", {}) if isinstance(data.get("default"), dict) else {}
        launch = data.get("launch", {}) if isinstance(data.get("launch"), dict) else {}
        register = data.get("register", {}).get("internal", {}) if isinstance(data.get("register"), dict) else {}
        scheduler = data.get("scheduler", {}) if isinstance(data.get("scheduler"), dict) else {}
        opts = {
            "admin_api_key": defaults.get("admin_api_key", DEFAULT_INF_KEY),
            "host": launch.get("gateway_host", "127.0.0.1"),
        }
        _check_admin_key(opts, report, default_key=DEFAULT_INF_KEY)
        if "log_level" in defaults and defaults["log_level"] not in LOG_LEVELS:
            report.add_error("[default].log_level must be debug/info/warning/error")
        if "routing_strategy" in launch and launch["routing_strategy"] not in ROUTING_STRATEGIES:
            report.add_error("[launch].routing_strategy must be round_robin or least_busy")
        if "gateway_port" in launch:
            _parse_positive_int(launch["gateway_port"], "[launch].gateway_port", report, min_value=1, max_value=65535)
        if "type" in scheduler and scheduler["type"] != "local":
            report.add_error("[scheduler].type for the local CLI must be 'local'")
        if "backend" in register:
            validate_backend_spec(str(register["backend"]), report, context="[register.internal].backend")
        if "engine_args" in register:
            validate_nested_args(str(register["engine_args"]), report, label="[register.internal].engine_args")
        if "proxy_args" in register:
            validate_nested_args(str(register["proxy_args"]), report, label="[register.internal].proxy_args", known_flags=PROXY_KNOWN_FLAGS)
    else:
        defaults = data.get("default", {}) if isinstance(data.get("default"), dict) else {}
        run = data.get("run", {}) if isinstance(data.get("run"), dict) else {}
        _check_admin_key({"admin_api_key": defaults.get("admin_api_key", DEFAULT_AGENT_KEY)}, report, default_key=DEFAULT_AGENT_KEY)
        if "log_level" in defaults and defaults["log_level"] not in LOG_LEVELS:
            report.add_error("[default].log_level must be debug/info/warning/error")
        if "num_pairs" in run:
            _parse_positive_int(run["num_pairs"], "[run].num_pairs", report)
        for key in ("setup_timeout", "health_poll_interval", "drain_timeout", "session_timeout"):
            if key in run:
                _parse_float(run[key], f"[run].{key}", report, min_value=0.0)
    return report


def inspect_areal_home(path: Path) -> CheckReport:
    report = CheckReport(subject=f"areal-home:{path}")
    if not path.exists():
        report.add_warning(f"AREAL_HOME path does not exist: {path}")
        return report
    for namespace in ("inf", "agent"):
        root = path / namespace
        services = root / "services"
        logs = root / "logs"
        current = root / "current-service"
        names = sorted(p.stem for p in services.glob("*.json")) if services.exists() else []
        report.add_info(f"{namespace}: services={names}")
        if current.exists():
            report.add_info(f"{namespace}: current-service={current.read_text().strip()!r}")
        if logs.exists():
            log_summary = {p.name: sorted(q.name for q in p.glob("*.log")) for p in logs.iterdir() if p.is_dir()}
            report.add_info(f"{namespace}: logs={log_summary}")
    return report


def print_text(reports: list[CheckReport]) -> None:
    for report in reports:
        status = "OK" if report.ok else "ERROR"
        print(f"[{status}] {report.subject}")
        for msg in report.errors:
            print(f"  error: {msg}")
        for msg in report.warnings:
            print(f"  warning: {msg}")
        for msg in report.info:
            print(f"  info: {msg}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Safely validate AReaL 2.0 service CLI commands/configs without launching services.",
    )
    parser.add_argument("--command", action="append", default=[], help="Command string to statically validate. Repeatable.")
    parser.add_argument("--config", action="append", type=Path, default=[], help="TOML config file to inspect. Repeatable.")
    parser.add_argument("--config-type", choices=["inf", "agent", "auto"], default="auto", help="Config schema to use for --config files.")
    parser.add_argument("--backend", action="append", default=[], help="Backend spec to validate, e.g. sglang:d1 or vllm:d2t4. Repeatable.")
    parser.add_argument("--engine-args", action="append", default=[], help="Nested engine args string to shlex-parse. Repeatable.")
    parser.add_argument("--proxy-args", action="append", default=[], help="Nested data-proxy args string to shlex-parse. Repeatable.")
    parser.add_argument("--areal-home", type=Path, default=None, help="Inspect local AReaL CLI state/log names without probing processes.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not (args.command or args.config or args.backend or args.engine_args or args.proxy_args or args.areal_home):
        parser.print_help()
        return 0

    reports: list[CheckReport] = []
    for command in args.command:
        reports.append(validate_command(command))
    for path in args.config:
        reports.append(validate_config(path, args.config_type))
    for spec in args.backend:
        report = CheckReport(subject=f"backend:{spec}")
        validate_backend_spec(spec, report)
        reports.append(report)
    for value in args.engine_args:
        report = CheckReport(subject=f"engine-args:{value}")
        validate_nested_args(value, report, label="engine args")
        reports.append(report)
    for value in args.proxy_args:
        report = CheckReport(subject=f"proxy-args:{value}")
        validate_nested_args(value, report, label="proxy args", known_flags=PROXY_KNOWN_FLAGS)
        reports.append(report)
    if args.areal_home is not None:
        reports.append(inspect_areal_home(args.areal_home.expanduser()))

    if args.json:
        print(json.dumps([r.as_dict() for r in reports], indent=2, default=str))
    else:
        print_text(reports)
    return 2 if any(not r.ok for r in reports) else 0


if __name__ == "__main__":
    raise SystemExit(main())
