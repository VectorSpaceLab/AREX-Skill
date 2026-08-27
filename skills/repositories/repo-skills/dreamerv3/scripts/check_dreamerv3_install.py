#!/usr/bin/env python3
"""Check that DreamerV3 can be imported and that a requested JAX backend works.

This helper is intentionally safe: it performs imports, config parsing, a tiny
JAX array operation, and optionally constructs the dummy environment. It does not
start training, download ROMs, construct optional heavy environments, or write a
logdir.

Examples:
  python scripts/check_dreamerv3_install.py --backend cpu
  python scripts/check_dreamerv3_install.py --backend auto --json
  python scripts/check_dreamerv3_install.py --backend cuda --skip-dummy-env
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
import importlib.resources as resources
import json
import os
import platform
import sys
from pathlib import Path
from typing import Any


def build_parser() -> argparse.ArgumentParser:
  parser = argparse.ArgumentParser(
      description='Run safe DreamerV3 import, config, dummy-env, and JAX backend checks.')
  parser.add_argument(
      '--backend',
      choices=['auto', 'cpu', 'cuda'],
      default='auto',
      help='JAX backend expectation. cpu sets JAX_PLATFORM_NAME=cpu before importing JAX.',
  )
  parser.add_argument(
      '--repo-root',
      type=Path,
      help='Optional local development checkout to prepend to sys.path before imports.',
  )
  parser.add_argument(
      '--skip-dummy-env',
      action='store_true',
      help='Skip constructing embodied.envs.dummy.Dummy.',
  )
  parser.add_argument('--json', action='store_true', help='Print a JSON report.')
  return parser


def import_module(name: str, report: dict[str, Any]) -> Any:
  try:
    module = importlib.import_module(name)
  except Exception as exc:  # pragma: no cover - diagnostic path
    report['imports'][name] = {'ok': False, 'error': repr(exc)}
    raise
  else:
    report['imports'][name] = {'ok': True, 'module': getattr(module, '__name__', name)}
    return module


def main() -> int:
  args = build_parser().parse_args()
  if args.repo_root is not None:
    root = args.repo_root.expanduser().resolve()
    if not root.exists():
      raise SystemExit(f'--repo-root does not exist: {root}')
    sys.path.insert(0, str(root))

  if args.backend == 'cpu':
    os.environ.setdefault('JAX_PLATFORM_NAME', 'cpu')

  report: dict[str, Any] = {
      'python': sys.version.split()[0],
      'platform': platform.platform(),
      'backend_requested': args.backend,
      'imports': {},
      'checks': [],
      'warnings': [],
  }

  try:
    report['dreamer_version'] = metadata.version('dreamer')
  except metadata.PackageNotFoundError:
    report['dreamer_version'] = None
    report['warnings'].append('Distribution metadata for dreamer was not found.')

  try:
    import_module('dreamerv3', report)
    embodied = import_module('embodied', report)
    import_module('dreamerv3.main', report)
    import_module('embodied.jax', report)

    config_text = resources.files('dreamerv3').joinpath('configs.yaml').read_text()
    import ruamel.yaml as yaml
    configs = yaml.YAML(typ='safe').load(config_text)
    report['configs'] = {
        'count': len(configs),
        'has_defaults': 'defaults' in configs,
        'has_debug': 'debug' in configs,
        'task_presets': sorted(k for k in configs if k not in ('defaults',) and not k.startswith('size')),
    }
    report['checks'].append({'name': 'config_parse', 'ok': True})

    import jax
    import jax.numpy as jnp
    value = float((jnp.ones((1,), dtype=jnp.float32) + 1).sum())
    backend = jax.default_backend()
    devices = [str(device) for device in jax.devices()]
    report['jax'] = {
        'version': getattr(jax, '__version__', None),
        'backend': backend,
        'device_count': len(devices),
        'devices': devices[:8],
        'tiny_sum': value,
    }
    if args.backend == 'cuda' and backend != 'gpu':
      report['checks'].append({'name': 'jax_cuda_backend', 'ok': False, 'backend': backend})
      raise RuntimeError(f'Expected JAX CUDA/GPU backend but default backend is {backend!r}')
    if args.backend == 'cpu' and backend != 'cpu':
      report['checks'].append({'name': 'jax_cpu_backend', 'ok': False, 'backend': backend})
      raise RuntimeError(f'Expected JAX CPU backend but default backend is {backend!r}')
    report['checks'].append({'name': 'jax_backend', 'ok': True, 'backend': backend})

    if not args.skip_dummy_env:
      from embodied.envs import dummy
      env = dummy.Dummy('disc', length=3)
      try:
        obs_keys = sorted(env.obs_space.keys())
        act_keys = sorted(env.act_space.keys())
        first = env.step({'reset': True})
        report['dummy_env'] = {
            'obs_keys': obs_keys,
            'act_keys': act_keys,
            'first_is_first': bool(first['is_first']),
            'first_is_last': bool(first['is_last']),
        }
        required_obs = {'reward', 'is_first', 'is_last', 'is_terminal'}
        missing = sorted(required_obs - set(obs_keys))
        if 'reset' not in act_keys or missing:
          raise RuntimeError(f'Dummy env contract failed: missing obs={missing}, reset={"reset" not in act_keys}')
        report['checks'].append({'name': 'dummy_env_contract', 'ok': True})
      finally:
        env.close()

  except Exception as exc:
    report['status'] = 'failed'
    report['error'] = repr(exc)
    if args.json:
      print(json.dumps(report, indent=2, sort_keys=True))
    else:
      print(f'FAIL: {exc}', file=sys.stderr)
      for name, data in report['imports'].items():
        print(f'import {name}: {data}')
    return 1

  report['status'] = 'ok'
  if args.json:
    print(json.dumps(report, indent=2, sort_keys=True))
  else:
    print(f"PASS: dreamer version={report['dreamer_version']} backend={report['jax']['backend']} devices={report['jax']['device_count']}")
    print(f"PASS: configs parsed={report['configs']['count']} dummy_env={'skipped' if args.skip_dummy_env else 'ok'}")
  return 0


if __name__ == '__main__':
  raise SystemExit(main())
