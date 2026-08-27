#!/usr/bin/env python3
"""Validate SkyServe service YAMLs with parser-only checks.

This helper imports SkyPilot parser APIs and inspects YAML structure. It does
not launch services, start API servers, contact cloud providers, open network
sockets, or write remote resources.
"""

from __future__ import annotations

import argparse
import copy
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple


SERVICE_KEYS = {
    'readiness_probe',
    'replicas',
    'replica_policy',
    'ports',
    'load_balancer',
    'load_balancing_policy',
    'pool',
    'workers',
    'tls',
}


def _import_dependencies() -> Tuple[Any, Any, Any, Any, Any]:
    try:
        import yaml  # type: ignore
        import sky  # type: ignore
        from sky.serve import serve_utils  # type: ignore
        from sky.serve import service_spec  # type: ignore
        from sky.utils import resources_utils  # type: ignore
    except ImportError as exc:
        raise SystemExit(
            'SkyPilot and PyYAML are required for validation. Install '
            'SkyPilot in the current Python environment, then rerun this '
            f'helper. Original import error: {exc}') from exc
    return yaml, sky, service_spec, serve_utils, resources_utils


def _load_yaml(path: Path, yaml_module: Any) -> Dict[str, Any]:
    try:
        with path.open('r', encoding='utf-8') as file_handle:
            loaded = yaml_module.safe_load(file_handle)
    except OSError as exc:
        raise ValueError(f'could not read file: {exc}') from exc
    except yaml_module.YAMLError as exc:
        raise ValueError(f'invalid YAML syntax: {exc}') from exc

    if loaded is None:
        return {}
    if not isinstance(loaded, dict):
        raise ValueError(
            f'top-level YAML must be a mapping, got {type(loaded).__name__}')
    return loaded


def _secret_overrides_for_nulls(config: Mapping[str, Any]) -> List[Tuple[str, str]]:
    raw_secrets = config.get('secrets')
    if not isinstance(raw_secrets, Mapping):
        return []
    overrides = []
    for key, value in raw_secrets.items():
        if value is None and not str(key).startswith('secrets:'):
            overrides.append((str(key), 'DUMMY_SECRET_FOR_PARSER_ONLY_VALIDATION'))
    return overrides


def _parse_full_service_task(config: Dict[str, Any], sky_module: Any) -> Any:
    if 'service' not in config:
        raise ValueError('full service YAML must contain a top-level service: section')
    config_copy = copy.deepcopy(config)
    secret_overrides = _secret_overrides_for_nulls(config_copy)
    return sky_module.Task.from_yaml_config(
        config_copy,
        secrets_overrides=secret_overrides or None,
    )


def _parse_service_fragment(config: Dict[str, Any], service_spec_module: Any) -> Any:
    unknown_keys = sorted(set(config) - SERVICE_KEYS)
    if unknown_keys:
        raise ValueError(
            'service fragment contains non-service keys: ' + ', '.join(unknown_keys))
    return service_spec_module.SkyServiceSpec.from_yaml_config(copy.deepcopy(config))


def _normalize_ports(value: Any) -> Optional[List[str]]:
    if value is None:
        return None
    if isinstance(value, int):
        return [str(value)]
    if isinstance(value, str):
        return [value]
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray)):
        return [str(item) for item in value]
    return None


def _port_values(value: Any, resources_utils_module: Any) -> Set[int]:
    normalized = _normalize_ports(value)
    if normalized is None:
        return set()
    try:
        return set(resources_utils_module.port_ranges_to_set(normalized))
    except Exception:  # pylint: disable=broad-except
        return set()


def _resource_configs(config: Mapping[str, Any]) -> List[Mapping[str, Any]]:
    resources = config.get('resources') or {}
    if isinstance(resources, Mapping):
        if isinstance(resources.get('ordered'), list):
            return [item for item in resources['ordered'] if isinstance(item, Mapping)]
        if isinstance(resources.get('any_of'), list):
            return [item for item in resources['any_of'] if isinstance(item, Mapping)]
        return [resources]
    if isinstance(resources, list):
        return [item for item in resources if isinstance(item, Mapping)]
    return []


def _run_commands(config: Mapping[str, Any]) -> str:
    pieces: List[str] = []
    for key in ('setup', 'run'):
        value = config.get(key)
        if isinstance(value, str):
            pieces.append(value)
        elif isinstance(value, list):
            pieces.extend(str(item) for item in value)
    return '\n'.join(pieces)


def _static_warnings(config: Mapping[str, Any], service_spec_obj: Any,
                     resources_utils_module: Any) -> List[str]:
    warnings: List[str] = []
    service_config = config.get('service')
    if not isinstance(service_config, Mapping):
        return warnings

    service_ports = getattr(service_spec_obj, 'ports', None)
    service_port = int(service_ports) if service_ports is not None else None
    resource_configs = _resource_configs(config)
    resource_ports_by_config = [
        _port_values(resource.get('ports'), resources_utils_module)
        for resource in resource_configs
    ]
    nonempty_resource_ports = [ports for ports in resource_ports_by_config if ports]

    if service_port is not None:
        for index, ports in enumerate(nonempty_resource_ports, start=1):
            if service_port not in ports:
                warnings.append(
                    f'service.ports={service_port} is not exposed by resources option {index}: '
                    f'{sorted(ports)}')
    elif len(nonempty_resource_ports) == 0:
        warnings.append('resources.ports is not set; SkyServe replicas need an exposed HTTP port')
    else:
        flattened = set().union(*nonempty_resource_ports)
        if len(flattened) != 1:
            warnings.append(
                'multiple resource ports are exposed; set service.ports to the single '
                'load-balancer ingress port')

    run_text = _run_commands(config)
    if run_text and '127.0.0.1' in run_text and '0.0.0.0' not in run_text:
        warnings.append(
            'run/setup mentions 127.0.0.1 but not 0.0.0.0; bind the serving '
            'process on all interfaces when possible')

    readiness_path = getattr(service_spec_obj, 'readiness_path', None)
    if readiness_path == '/v1/models' and run_text and 'vllm' not in run_text.lower():
        warnings.append('/v1/models readiness is commonly used for vLLM/OpenAI-compatible servers; verify the framework exposes it')
    if readiness_path == '/health' and run_text and 'vllm' in run_text.lower():
        warnings.append('vLLM OpenAI-compatible examples commonly use /v1/models rather than /health')

    if getattr(service_spec_obj, 'initial_delay_seconds', 0) < 300:
        lower_run = run_text.lower()
        if any(marker in lower_run for marker in ('vllm', 'sglang', 'text-generation-inference', 'fastchat')):
            warnings.append(
                'initial_delay_seconds is below 300 for an LLM service; large '
                'model download/warmup may require a longer delay')

    raw_secrets = config.get('secrets')
    if isinstance(raw_secrets, Mapping):
        inline_secret_keys = [
            str(key) for key, value in raw_secrets.items()
            if value not in (None, '') and not str(key).startswith('secrets:')
        ]
        if inline_secret_keys:
            warnings.append(
                'inline secret values found for ' + ', '.join(sorted(inline_secret_keys)) +
                '; prefer null placeholders plus CLI --secret for shared YAML')

    return warnings


def _summary_for_task(config: Mapping[str, Any], service_spec_obj: Any) -> List[str]:
    service_config = config.get('service') if isinstance(config.get('service'), Mapping) else {}
    assert isinstance(service_config, Mapping)
    summary = [
        f'readiness={service_spec_obj.probe_str()}',
        f'min_replicas={getattr(service_spec_obj, "min_replicas", None)}',
        f'max_replicas={getattr(service_spec_obj, "max_replicas", None)}',
        f'ports={getattr(service_spec_obj, "ports", None)}',
        f'load_balancing_policy={getattr(service_spec_obj, "load_balancing_policy", None)}',
    ]
    if 'replicas' in service_config:
        summary.append(f'fixed_replicas={service_config["replicas"]}')
    if 'replica_policy' in service_config:
        summary.append('autoscaling_policy=replica_policy')
    return summary


def _validate_one(path: Path, args: argparse.Namespace, modules: Tuple[Any, Any, Any, Any, Any]) -> Tuple[bool, List[str]]:
    yaml_module, sky_module, service_spec_module, serve_utils_module, resources_utils_module = modules
    messages: List[str] = []
    try:
        config = _load_yaml(path, yaml_module)
        if args.fragment:
            service_spec_obj = _parse_service_fragment(config, service_spec_module)
            detected = 'service-fragment'
            warnings: List[str] = []
        else:
            task_obj = _parse_full_service_task(config, sky_module)
            service_spec_obj = task_obj.service
            if service_spec_obj is None:
                raise ValueError('service parser returned no service spec')
            serve_utils_module.validate_service_task(task_obj, pool=False)
            detected = 'task-with-service'
            warnings = _static_warnings(config, service_spec_obj, resources_utils_module)
    except Exception as exc:  # pylint: disable=broad-except
        return False, [f'{path}: invalid ({type(exc).__name__}: {exc})']

    messages.append(f'{path}: valid {detected} YAML')
    if args.summary:
        messages.extend(f'  {item}' for item in _summary_for_task(config, service_spec_obj))
    if warnings:
        messages.append('  warnings:')
        messages.extend(f'    - {warning}' for warning in warnings)
    return True, messages


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            'Validate SkyServe service YAMLs using parser-only APIs. No launch, '
            'cloud credential check, network call, API-server start, or remote '
            'write is performed.'))
    parser.add_argument(
        'yaml_files',
        nargs='+',
        type=Path,
        help='One or more full SkyServe YAML files to validate.')
    parser.add_argument(
        '--fragment',
        action='store_true',
        help='Treat inputs as service: fragments rather than full task YAMLs.')
    parser.add_argument(
        '--summary',
        action='store_true',
        help='Print parsed readiness, replica, port, and load-balancing summary.')
    return parser


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    modules = _import_dependencies()

    all_ok = True
    for yaml_file in args.yaml_files:
        ok, messages = _validate_one(yaml_file, args, modules)
        print('\n'.join(messages))
        all_ok = all_ok and ok
    return 0 if all_ok else 1


if __name__ == '__main__':
    sys.exit(main())
