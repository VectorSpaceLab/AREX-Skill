#!/usr/bin/env python3
'''
Read-only validator for GeoAI MCP client configuration.

This script does not start the server, contact the network, download models,
or write into user directories. It validates Claude Desktop style config files
or the current environment for sandbox and routing mistakes.
'''

from __future__ import annotations

import argparse
import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable


VALID_DEVICES = {'auto', 'cuda', 'mps', 'cpu'}
VALID_LOG_LEVELS = {'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'}
PROVIDER_KEYS = (
    'OPENAI_API_KEY',
    'ANTHROPIC_API_KEY',
    'GOOGLE_API_KEY',
    'MINIMAX_API_KEY',
    'AWS_ACCESS_KEY_ID',
    'AWS_SECRET_ACCESS_KEY',
    'AWS_SESSION_TOKEN',
)


@dataclass(frozen=True)
class Issue:
    severity: str
    field: str
    message: str


@dataclass(frozen=True)
class CheckResult:
    ok: bool
    server_name: str
    launch_mode: str
    command: str | None
    cwd: str | None
    input_dir: str | None
    output_dir: str | None
    log_file: str | None
    device: str | None
    timeout: int | None
    max_memory_gb: int | None
    model_cache_size: int | None
    issues: list[Issue]
    provider_keys: list[dict[str, str]]


def _read_json(path: Path) -> dict[str, Any]:
    with path.open('r', encoding='utf-8') as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError('Top-level config must be a JSON object')
    return payload


def _pick_server_entry(config: dict[str, Any], server_name: str) -> dict[str, Any]:
    servers = config.get('mcpServers')
    if not isinstance(servers, dict):
        raise ValueError('Missing top-level mcpServers object')
    entry = servers.get(server_name)
    if not isinstance(entry, dict):
        raise ValueError(f'Missing MCP server entry for {server_name!r}')
    return entry


def _coerce_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _coerce_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _join_command(command: Any, args: list[Any]) -> str | None:
    if not isinstance(command, str) or not command.strip():
        return None
    parts = [command.strip()]
    for arg in args:
        if isinstance(arg, str):
            parts.append(arg)
        else:
            parts.append(str(arg))
    return ' '.join(parts)


def _normalize_path(raw: str | None, cwd: Path | None) -> Path | None:
    if raw is None or not str(raw).strip():
        return None
    path = Path(raw).expanduser()
    if path.is_absolute():
        return path.resolve(strict=False)
    if cwd is not None:
        return (cwd / path).resolve(strict=False)
    return (Path.cwd() / path).resolve(strict=False)


def _is_within(path: Path, roots: Iterable[Path]) -> bool:
    try:
        resolved = path.resolve(strict=False)
    except Exception:
        resolved = path
    for root in roots:
        try:
            resolved_root = root.resolve(strict=False)
        except Exception:
            continue
        try:
            if resolved.is_relative_to(resolved_root):
                return True
        except AttributeError:
            try:
                resolved.relative_to(resolved_root)
                return True
            except Exception:
                continue
        except Exception:
            continue
    return False


def _check_common_env(
    env: dict[str, Any],
    cwd: Path | None,
    sandbox_roots: list[Path],
    issues: list[Issue],
) -> tuple[str | None, str | None, str | None, str | None, int | None, int | None, str | None]:
    input_dir_raw = env.get('GEOAI_INPUT_DIR')
    output_dir_raw = env.get('GEOAI_OUTPUT_DIR')
    timeout_raw = env.get('GEOAI_TIMEOUT')
    max_memory_raw = env.get('GEOAI_MAX_MEMORY_GB')
    device_raw = env.get('GEOAI_DEVICE', 'auto')
    log_level_raw = env.get('GEOAI_LOG_LEVEL', 'INFO')
    log_file_raw = env.get('GEOAI_LOG_FILE')
    cache_size_raw = env.get('GEOAI_MODEL_CACHE_SIZE')

    input_dir = _normalize_path(input_dir_raw, cwd)
    output_dir = _normalize_path(output_dir_raw, cwd)
    log_file = _normalize_path(log_file_raw, cwd)

    if input_dir_raw is None:
        issues.append(Issue('warning', 'env.GEOAI_INPUT_DIR', 'Not set; the server will default to ./input relative to its cwd.'))
    if output_dir_raw is None:
        issues.append(Issue('warning', 'env.GEOAI_OUTPUT_DIR', 'Not set; the server will default to ./output relative to its cwd.'))

    if isinstance(input_dir_raw, str) and '..' in Path(input_dir_raw).parts:
        issues.append(Issue('warning', 'env.GEOAI_INPUT_DIR', 'Contains path traversal segments. Prefer an absolute sandbox path.'))
    if isinstance(output_dir_raw, str) and '..' in Path(output_dir_raw).parts:
        issues.append(Issue('warning', 'env.GEOAI_OUTPUT_DIR', 'Contains path traversal segments. Prefer an absolute sandbox path.'))

    if input_dir is not None and output_dir is not None and input_dir == output_dir:
        issues.append(Issue('warning', 'env.GEOAI_INPUT_DIR / env.GEOAI_OUTPUT_DIR', 'Input and output directories are identical. Separate them if you want stricter sandboxing.'))

    if input_dir is not None:
        if sandbox_roots and not _is_within(input_dir, sandbox_roots):
            issues.append(Issue('error', 'env.GEOAI_INPUT_DIR', f'{input_dir} is outside the declared sandbox roots.'))
        elif not input_dir.exists():
            issues.append(Issue('warning', 'env.GEOAI_INPUT_DIR', f'{input_dir} does not exist yet. The server can create it, but tools cannot read missing input data.'))
        elif not input_dir.is_dir():
            issues.append(Issue('error', 'env.GEOAI_INPUT_DIR', f'{input_dir} is not a directory.'))
        elif not os.access(input_dir, os.R_OK | os.X_OK):
            issues.append(Issue('error', 'env.GEOAI_INPUT_DIR', f'{input_dir} is not readable.'))

    if output_dir is not None:
        if sandbox_roots and not _is_within(output_dir, sandbox_roots):
            issues.append(Issue('error', 'env.GEOAI_OUTPUT_DIR', f'{output_dir} is outside the declared sandbox roots.'))
        elif not output_dir.exists():
            issues.append(Issue('warning', 'env.GEOAI_OUTPUT_DIR', f'{output_dir} does not exist yet. The server can create it.'))
        elif not output_dir.is_dir():
            issues.append(Issue('error', 'env.GEOAI_OUTPUT_DIR', f'{output_dir} is not a directory.'))
        elif not os.access(output_dir, os.W_OK | os.X_OK):
            issues.append(Issue('error', 'env.GEOAI_OUTPUT_DIR', f'{output_dir} is not writable.'))

    if log_file is not None and sandbox_roots and not _is_within(log_file, sandbox_roots):
        issues.append(Issue('warning', 'env.GEOAI_LOG_FILE', f'{log_file} is outside the declared sandbox roots.'))

    timeout = None
    if timeout_raw is not None:
        try:
            timeout = int(timeout_raw)
            if timeout < 10:
                issues.append(Issue('error', 'env.GEOAI_TIMEOUT', 'Timeout is too small; use at least 10 seconds.'))
            if timeout > 3600:
                issues.append(Issue('error', 'env.GEOAI_TIMEOUT', 'Timeout is too large; use 3600 seconds or less.'))
        except Exception:
            issues.append(Issue('error', 'env.GEOAI_TIMEOUT', 'Timeout must be an integer.'))

    max_memory = None
    if max_memory_raw is not None:
        try:
            max_memory = int(max_memory_raw)
            if max_memory <= 0:
                issues.append(Issue('error', 'env.GEOAI_MAX_MEMORY_GB', 'Memory budget must be positive.'))
        except Exception:
            issues.append(Issue('error', 'env.GEOAI_MAX_MEMORY_GB', 'Memory budget must be an integer.'))

    if device_raw not in VALID_DEVICES:
        issues.append(Issue('error', 'env.GEOAI_DEVICE', f'Invalid device {device_raw!r}; use one of {sorted(VALID_DEVICES)}.'))

    if str(log_level_raw).upper() not in VALID_LOG_LEVELS:
        issues.append(Issue('error', 'env.GEOAI_LOG_LEVEL', f'Invalid log level {log_level_raw!r}; use one of {sorted(VALID_LOG_LEVELS)}.'))

    cache_size = None
    if cache_size_raw is not None:
        try:
            cache_size = int(cache_size_raw)
            if cache_size < 0:
                issues.append(Issue('error', 'env.GEOAI_MODEL_CACHE_SIZE', 'Cache size must be zero or positive.'))
        except Exception:
            issues.append(Issue('error', 'env.GEOAI_MODEL_CACHE_SIZE', 'Cache size must be an integer.'))

    return (
        str(input_dir) if input_dir is not None else None,
        str(output_dir) if output_dir is not None else None,
        str(log_file) if log_file is not None else None,
        str(device_raw) if device_raw is not None else None,
        timeout,
        max_memory,
        cache_size,
    )


def _provider_key_status(env: dict[str, Any]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for name in PROVIDER_KEYS:
        value = env.get(name)
        state = 'missing'
        if isinstance(value, str) and value.strip():
            state = 'set'
        elif value not in (None, ''):
            state = 'set'
        rows.append({'name': name, 'state': state})
    return rows


def check_config(args: argparse.Namespace) -> CheckResult:
    issues: list[Issue] = []
    server_name = args.server_name
    cwd: Path | None = None
    command = None
    launch_mode = 'env-only' if args.env_only else 'config-file'
    env: dict[str, Any] = {}

    if not args.env_only:
        config_path = Path(args.config).expanduser()
        if not config_path.exists():
            issues.append(Issue('error', 'config', f'Config file not found: {config_path}'))
            return CheckResult(
                ok=False,
                server_name=server_name,
                launch_mode=launch_mode,
                command=None,
                cwd=None,
                input_dir=None,
                output_dir=None,
                log_file=None,
                device=None,
                timeout=None,
                max_memory_gb=None,
                model_cache_size=None,
                issues=issues,
                provider_keys=[],
            )

        try:
            config = _read_json(config_path)
        except Exception as exc:
            issues.append(Issue('error', 'config', f'Could not read JSON config: {exc}'))
            return CheckResult(
                ok=False,
                server_name=server_name,
                launch_mode=launch_mode,
                command=None,
                cwd=None,
                input_dir=None,
                output_dir=None,
                log_file=None,
                device=None,
                timeout=None,
                max_memory_gb=None,
                model_cache_size=None,
                issues=issues,
                provider_keys=[],
            )

        try:
            server = _pick_server_entry(config, server_name)
        except Exception as exc:
            issues.append(Issue('error', 'mcpServers', str(exc)))
            return CheckResult(
                ok=False,
                server_name=server_name,
                launch_mode=launch_mode,
                command=None,
                cwd=None,
                input_dir=None,
                output_dir=None,
                log_file=None,
                device=None,
                timeout=None,
                max_memory_gb=None,
                model_cache_size=None,
                issues=issues,
                provider_keys=[],
            )

        command = server.get('command')
        args_list = _coerce_list(server.get('args'))
        cwd_raw = server.get('cwd')
        env = _coerce_dict(server.get('env'))

        if not isinstance(command, str) or not command.strip():
            issues.append(Issue('error', 'command', 'Server command must be a non-empty string.'))
        elif not isinstance(args_list, list):
            issues.append(Issue('error', 'args', 'Server args must be a list.'))
        else:
            command_base = Path(command.strip()).name.lower()
            resolved = _join_command(command, args_list)
            if resolved is not None:
                command = resolved
            python_launchers = {
                'python',
                'python3',
                'pythonw',
                'py',
                'python.exe',
                'python3.exe',
                'pythonw.exe',
                'py.exe',
            }
            if command_base in python_launchers:
                if '-m' not in args_list or 'geoai_mcp_server.server' not in args_list:
                    issues.append(Issue('warning', 'command', 'Python launch detected but the args do not look like `-m geoai_mcp_server.server`.'))
                else:
                    launch_mode = 'python-module'
            elif command_base == 'geoai-mcp-server':
                launch_mode = 'console-script'
            else:
                issues.append(Issue('warning', 'command', 'Unrecognized launch shape. Use the installed console script or `python -m geoai_mcp_server.server`.'))

        if cwd_raw is not None:
            if isinstance(cwd_raw, str) and cwd_raw and not Path(cwd_raw).is_absolute():
                issues.append(Issue('warning', 'cwd', 'Working directory is relative; prefer an absolute path.'))
            cwd = _normalize_path(str(cwd_raw), None)
        else:
            cwd = None

        sandbox_roots: list[Path] = []
        for root in args.sandbox_root:
            sandbox_roots.append(Path(root).expanduser().resolve(strict=False))

        input_dir, output_dir, log_file, device, timeout, max_memory, cache_size = _check_common_env(
            env,
            cwd,
            sandbox_roots,
            issues,
        )

        provider_status = _provider_key_status(env)

        ok = not any(issue.severity == 'error' for issue in issues)
        if args.strict:
            ok = ok and not issues

        return CheckResult(
            ok=ok,
            server_name=server_name,
            launch_mode=launch_mode,
            command=command,
            cwd=str(cwd) if cwd is not None else None,
            input_dir=input_dir,
            output_dir=output_dir,
            log_file=log_file,
            device=device,
            timeout=timeout,
            max_memory_gb=max_memory,
            model_cache_size=cache_size,
            issues=issues,
            provider_keys=provider_status,
        )

    # env-only mode
    sandbox_roots = [Path(root).expanduser().resolve(strict=False) for root in args.sandbox_root]
    input_dir, output_dir, log_file, device, timeout, max_memory, cache_size = _check_common_env(
        os.environ,
        None,
        sandbox_roots,
        issues,
    )
    provider_status = _provider_key_status(os.environ)
    ok = not any(issue.severity == 'error' for issue in issues)
    if args.strict:
        ok = ok and not issues

    return CheckResult(
        ok=ok,
        server_name=server_name,
        launch_mode=launch_mode,
        command=None,
        cwd=None,
        input_dir=input_dir,
        output_dir=output_dir,
        log_file=log_file,
        device=device,
        timeout=timeout,
        max_memory_gb=max_memory,
        model_cache_size=cache_size,
        issues=issues,
        provider_keys=provider_status,
    )


def render_text(result: CheckResult) -> str:
    lines: list[str] = []
    lines.append('GeoAI MCP config check')
    lines.append(f'Server: {result.server_name}')
    lines.append(f'Launch mode: {result.launch_mode}')
    if result.command:
        lines.append(f'Command: {result.command}')
    if result.cwd:
        lines.append(f'Working directory: {result.cwd}')
    if result.input_dir:
        lines.append(f'Input dir: {result.input_dir}')
    if result.output_dir:
        lines.append(f'Output dir: {result.output_dir}')
    if result.log_file:
        lines.append(f'Log file: {result.log_file}')
    if result.device:
        lines.append(f'Device: {result.device}')
    if result.timeout is not None:
        lines.append(f'Timeout: {result.timeout}')
    if result.max_memory_gb is not None:
        lines.append(f'Max memory GB: {result.max_memory_gb}')
    if result.model_cache_size is not None:
        lines.append(f'Model cache size: {result.model_cache_size}')

    if result.provider_keys:
        lines.append('Provider keys:')
        for item in result.provider_keys:
            lines.append(f"- {item['name']}: {item['state']}")

    if result.issues:
        lines.append('Issues:')
        for issue in result.issues:
            lines.append(f"- {issue.severity.upper()} [{issue.field}] {issue.message}")
    else:
        lines.append('Issues: none')

    lines.append('')
    lines.append('Status: ' + ('ok' if result.ok else 'needs attention'))
    return '\n'.join(lines).rstrip() + '\n'


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description='Validate a GeoAI MCP client config or environment skeleton.'
    )
    parser.add_argument('--config', help='Path to a Claude Desktop style JSON config file.')
    parser.add_argument('--server-name', default='geoai', help='Server key to validate.')
    parser.add_argument(
        '--sandbox-root',
        action='append',
        default=[],
        help='Allowed sandbox root directory. May be passed multiple times.',
    )
    parser.add_argument('--env-only', action='store_true', help='Validate the current environment instead of a config file.')
    parser.add_argument('--strict', action='store_true', help='Treat warnings as failures.')
    parser.add_argument('--format', choices=['text', 'json'], default='text')
    args = parser.parse_args(argv)

    if not args.env_only and not args.config:
        parser.error('Provide --config or use --env-only.')

    result = check_config(args)
    if args.format == 'json':
        print(json.dumps(asdict(result), indent=2, sort_keys=True, default=str))
    else:
        print(render_text(result), end='')

    return 0 if result.ok else 1


if __name__ == '__main__':
    raise SystemExit(main())
