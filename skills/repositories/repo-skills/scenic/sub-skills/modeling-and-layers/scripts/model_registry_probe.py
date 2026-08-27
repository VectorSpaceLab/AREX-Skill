#!/usr/bin/env python3
"""Probe the Scenic model registry.

This helper lists registered Scenic model names or resolves one registered
model name to its module/class without instantiating the model or allocating
large tensors.
"""

import argparse
from typing import Optional, Sequence


def build_parser() -> argparse.ArgumentParser:
  parser = argparse.ArgumentParser(
      description=(
          'List Scenic model registry names or resolve one registered model '
          'class without instantiating it.'))
  parser.add_argument(
      '--model-name',
      '-m',
      help='Resolve one registered model name and print its module/class.')
  return parser


def load_models_module():
  try:
    from scenic.model_lib import models
  except Exception as exc:  # pragma: no cover - surfaced as a clean CLI error.
    raise RuntimeError(
        'Could not import scenic.model_lib.models. Install Scenic runtime '
        f'dependencies first: {exc}') from exc
  return models


def print_registered_names(models_module) -> int:
  for name in sorted(models_module.ALL_MODELS):
    print(name)
  return 0


def print_resolved_class(models_module, model_name: str) -> int:
  try:
    model_cls = models_module.get_model_cls(model_name)
  except ValueError as exc:
    available = ', '.join(sorted(models_module.ALL_MODELS))
    raise SystemExit(f'{exc}\nAvailable names: {available}') from exc
  print(f'{model_name}\t{model_cls.__module__}.{model_cls.__name__}')
  return 0


def main(argv: Optional[Sequence[str]] = None) -> int:
  parser = build_parser()
  args = parser.parse_args(argv)

  try:
    models_module = load_models_module()
  except RuntimeError as exc:
    parser.error(str(exc))

  if args.model_name:
    return print_resolved_class(models_module, args.model_name)
  return print_registered_names(models_module)


if __name__ == '__main__':
  raise SystemExit(main())
