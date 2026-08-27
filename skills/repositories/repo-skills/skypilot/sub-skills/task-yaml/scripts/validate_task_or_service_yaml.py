#!/usr/bin/env python3
"""Validate SkyPilot task or service YAMLs with parser-only APIs.

This helper imports SkyPilot and instantiates YAML parser objects. It does not
launch clusters, contact cloud providers, start API servers, or write remote
resources.
"""

from __future__ import annotations

import argparse
import copy
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, Optional, Tuple


def _import_skypilot() -> Tuple[Any, Any, Any]:
    try:
        import yaml  # type: ignore
        import sky  # type: ignore
        from sky.serve import service_spec  # type: ignore
    except ImportError as exc:
        raise SystemExit(
            'SkyPilot is required for validation. Install SkyPilot in the '
            'current Python environment, then rerun this helper. Original '
            f'import error: {exc}') from exc
    return yaml, sky, service_spec


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


def _validate_task(path: Path, config: Dict[str, Any], sky_module: Any) -> None:
    if path.exists():
        sky_module.Task.from_yaml(str(path))
    else:
        sky_module.Task.from_yaml_config(copy.deepcopy(config))


def _validate_service_fragment(config: Dict[str, Any], service_spec_module: Any
                               ) -> None:
    service_spec_module.SkyServiceSpec.from_yaml_config(copy.deepcopy(config))


def _validate_service(path: Path, config: Dict[str, Any], sky_module: Any,
                      service_spec_module: Any) -> str:
    if 'service' in config:
        _validate_task(path, config, sky_module)
        return 'task-with-service'
    _validate_service_fragment(config, service_spec_module)
    return 'service-fragment'


def _validate_auto(path: Path, config: Dict[str, Any], sky_module: Any,
                   service_spec_module: Any) -> str:
    if 'service' in config:
        _validate_task(path, config, sky_module)
        return 'task-with-service'

    service_keys = {
        'readiness_probe',
        'replicas',
        'replica_policy',
        'ports',
        'load_balancer',
        'load_balancing_policy',
        'pool',
        'workers',
    }
    task_keys = {
        'name',
        'workdir',
        'num_nodes',
        'resources',
        'envs',
        'secrets',
        'managed_secrets',
        'api_server_access',
        'volumes',
        'file_mounts',
        'setup',
        'run',
        'config',
        'inputs',
        'outputs',
    }

    config_keys = set(config)
    if config_keys & service_keys and not config_keys & task_keys:
        _validate_service_fragment(config, service_spec_module)
        return 'service-fragment'

    _validate_task(path, config, sky_module)
    return 'task'


def _validate_one(path: Path, kind: str, yaml_module: Any, sky_module: Any,
                  service_spec_module: Any) -> Tuple[bool, str]:
    try:
        config = _load_yaml(path, yaml_module)
        if kind == 'task':
            _validate_task(path, config, sky_module)
            detected = 'task'
        elif kind == 'service':
            detected = _validate_service(path, config, sky_module,
                                         service_spec_module)
        else:
            detected = _validate_auto(path, config, sky_module,
                                      service_spec_module)
    except Exception as exc:  # pylint: disable=broad-except
        return False, f'{path}: invalid ({type(exc).__name__}: {exc})'
    return True, f'{path}: valid {detected} YAML'


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            'Validate SkyPilot task/service YAMLs using parser-only APIs. '
            'No launch, cloud credential check, network call, or destructive '
            'write is performed by this helper.'))
    parser.add_argument(
        '--kind',
        choices=('task', 'service', 'auto'),
        default='auto',
        help=(
            'Validation target. task uses sky.Task.from_yaml; service accepts '
            'either a full task YAML with service: or a service-spec fragment; '
            'auto infers from top-level keys. Default: auto.'))
    parser.add_argument(
        'yaml_files',
        nargs='+',
        type=Path,
        help='One or more YAML files to validate.')
    return parser


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    yaml_module, sky_module, service_spec_module = _import_skypilot()

    all_ok = True
    for yaml_file in args.yaml_files:
        ok, message = _validate_one(yaml_file, args.kind, yaml_module,
                                    sky_module, service_spec_module)
        print(message)
        all_ok = all_ok and ok
    return 0 if all_ok else 1


if __name__ == '__main__':
    sys.exit(main())
