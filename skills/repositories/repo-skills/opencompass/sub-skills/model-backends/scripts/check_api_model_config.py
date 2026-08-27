#!/usr/bin/env python3
"""Dry-run checks for OpenCompass API model configs.

This script loads an OpenCompass config, inspects model dictionaries, and warns
about common API credential/resource issues without building models or making
network calls.
"""

from __future__ import annotations

import argparse
import os
import sys
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any, Optional

PLACEHOLDER_VALUES = {
    '',
    'YOUR_API_KEY',
    'YOUR_OPENAI_KEY',
    'YOUR_KEY',
    'YOUR_SECRET',
    'TODO',
    'EMPTY_KEY',
    '<KEY>',
    '<API_KEY>',
}

API_HINT_FIELDS = {
    'key',
    'api_key',
    'api_secret',
    'api_addr',
    'openai_api_base',
    'openai_proxy_url',
    'query_per_second',
    'retry',
    'rpm_verbose',
}

API_TYPE_HINTS = (
    'api',
    'openai',
    'sdk',
    'claude',
    'gemini',
    'zhipu',
    'minimax',
    'xunfei',
    'turbomindapi',
    'lightllm',
)

ENV_BY_FIELD = {
    'key': ('OPENAI_API_KEY',),
    'openai_proxy_url': ('OPENAI_PROXY_URL',),
    'openai_api_base': ('OPENAI_BASE_URL',),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Inspect OpenCompass API model configs without network calls.')
    parser.add_argument('config', help='Path to an OpenCompass config file.')
    parser.add_argument(
        '--all-models',
        action='store_true',
        help='Report non-API-looking models as informational entries too.',
    )
    return parser.parse_args()


def load_config(config_path: Path) -> Any:
    try:
        from mmengine.config import Config
    except Exception as exc:  # pragma: no cover - environment dependent
        raise RuntimeError(
            'mmengine is required to parse OpenCompass config files. '
            'Install OpenCompass runtime dependencies before using this checker.'
        ) from exc

    return Config.fromfile(str(config_path))


def as_plain(value: Any) -> Any:
    if hasattr(value, 'to_dict'):
        return value.to_dict()
    if isinstance(value, Mapping):
        return {key: as_plain(item) for key, item in value.items()}
    if isinstance(value, list):
        return [as_plain(item) for item in value]
    if isinstance(value, tuple):
        return tuple(as_plain(item) for item in value)
    return value


def type_name(type_value: Any) -> str:
    if isinstance(type_value, str):
        return type_value
    name = getattr(type_value, '__name__', None)
    module = getattr(type_value, '__module__', None)
    if name and module:
        return f'{module}.{name}'
    if name:
        return name
    return str(type_value)


def is_api_like(model: Mapping[str, Any]) -> bool:
    model_type = type_name(model.get('type', '')).replace('_', '').lower()
    if any(hint in model_type for hint in API_TYPE_HINTS):
        return True
    return bool(API_HINT_FIELDS.intersection(model.keys()))


def model_label(model: Mapping[str, Any], index: int) -> str:
    return str(model.get('abbr') or model.get('path') or f'model[{index}]')


def is_placeholder(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        normalized = value.strip()
        return normalized in PLACEHOLDER_VALUES or normalized.startswith('YOUR_')
    if isinstance(value, Iterable) and not isinstance(value, (bytes, str, Mapping)):
        return any(is_placeholder(item) for item in value)
    return False


def env_status(field: str) -> Optional[str]:
    names = ENV_BY_FIELD.get(field)
    if not names:
        return None
    missing = [name for name in names if not os.getenv(name)]
    if missing:
        return f'ENV requested for {field}, but missing: {", ".join(missing)}'
    return None


def check_credential_field(model: Mapping[str, Any], field: str) -> list[str]:
    warnings: list[str] = []
    if field not in model:
        return warnings

    value = model[field]
    if value == 'ENV':
        status = env_status(field)
        if status:
            warnings.append(status)
    elif is_placeholder(value):
        warnings.append(f'{field} appears to contain a placeholder, not a real runtime secret')
    elif field in {'key', 'api_key', 'api_secret'} and isinstance(value, str) and len(value) > 8:
        warnings.append(f'{field} is inline; prefer environment variables or local-only untracked config')
    return warnings


def check_api_model(model: Mapping[str, Any], index: int) -> tuple[list[str], list[str]]:
    warnings: list[str] = []
    infos: list[str] = []

    model_type = type_name(model.get('type', ''))
    infos.append(f'type={model_type}')

    for required in ('max_seq_len', 'max_out_len', 'batch_size'):
        if required not in model:
            warnings.append(f'missing common field: {required}')

    if 'run_cfg' not in model:
        warnings.append('missing run_cfg; API models usually use run_cfg=dict(num_gpus=0)')
    else:
        run_cfg = as_plain(model.get('run_cfg'))
        if isinstance(run_cfg, Mapping):
            num_gpus = run_cfg.get('num_gpus')
            if isinstance(num_gpus, (int, float)) and num_gpus > 0:
                warnings.append(
                    f'run_cfg.num_gpus={num_gpus}; remote API clients usually reserve 0 local GPUs')
        else:
            warnings.append('run_cfg is not a mapping')

    for field in ('key', 'api_key', 'api_secret', 'openai_proxy_url', 'openai_api_base'):
        warnings.extend(check_credential_field(model, field))

    if 'key' not in model and any(name in model_type.lower() for name in ('openai', 'sdk')):
        warnings.append('OpenAI-compatible model has no key field; use key="ENV" or key="EMPTY" intentionally')

    if 'openai_api_base' in model:
        base = model['openai_api_base']
        if isinstance(base, str) and base.startswith('http://') and '127.0.0.1' not in base and 'localhost' not in base:
            warnings.append('openai_api_base uses plain HTTP for a non-local host')
        if isinstance(base, str) and ('23333' in base or '8000' in base) and not base.rstrip('/').endswith('/v1'):
            warnings.append('OpenAI-compatible local service base often needs a /v1 suffix')

    if 'api_addr' in model and not str(model['api_addr']).startswith(('http://', 'https://')):
        warnings.append('api_addr should include http:// or https://')

    query_per_second = model.get('query_per_second')
    if isinstance(query_per_second, (int, float)) and query_per_second > 10:
        warnings.append(f'query_per_second={query_per_second}; confirm provider/service rate limits')

    retry = model.get('retry')
    if isinstance(retry, int) and retry > 10:
        warnings.append(f'retry={retry}; high retries can hide permanent auth/quota errors')

    batch_size = model.get('batch_size')
    if isinstance(batch_size, int) and batch_size > 16:
        warnings.append(f'batch_size={batch_size}; confirm API wrapper/provider supports this concurrency')

    return warnings, infos


def main() -> int:
    args = parse_args()
    config_path = Path(args.config).expanduser()
    if not config_path.exists():
        print(f'ERROR: config not found: {config_path}', file=sys.stderr)
        return 2

    try:
        cfg = load_config(config_path)
    except Exception as exc:
        print(f'ERROR: failed to load config: {exc}', file=sys.stderr)
        return 2

    if 'models' not in cfg:
        print('ERROR: config has no models = [...] entry', file=sys.stderr)
        return 2

    models = as_plain(cfg.models)
    if not isinstance(models, list):
        print('ERROR: cfg.models is not a list', file=sys.stderr)
        return 2

    print(f'Loaded {len(models)} model config(s) from {config_path}')
    warning_count = 0
    api_count = 0

    for index, raw_model in enumerate(models):
        if not isinstance(raw_model, Mapping):
            print(f'WARN model[{index}]: entry is not a mapping')
            warning_count += 1
            continue

        model = dict(raw_model)
        api_like = is_api_like(model)
        if not api_like and not args.all_models:
            continue

        if api_like:
            api_count += 1
        label = model_label(model, index)
        kind = 'API-like' if api_like else 'non-API'
        print(f'\n[{kind}] {label}')
        warnings, infos = check_api_model(model, index) if api_like else ([], [f'type={type_name(model.get("type", ""))}'])
        for info in infos:
            print(f'  INFO: {info}')
        for warning in warnings:
            print(f'  WARN: {warning}')
        warning_count += len(warnings)

    if api_count == 0:
        print('\nNo API-like model configs found. Use --all-models to inspect every model entry.')

    if warning_count:
        print(f'\nCompleted dry-run with {warning_count} warning(s). No models were built and no network calls were made.')
        return 1

    print('\nCompleted dry-run with no warnings. No models were built and no network calls were made.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
