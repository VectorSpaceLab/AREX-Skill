#!/usr/bin/env python3
"""Bounded DreamerV3 CPU smoke and CLI translator.

This helper keeps the command surface small:
- short smoke flags are translated into the dotted DreamerV3 config keys
- the default run is CPU + dummy env + debug preset + tiny step budget
- `--dry-run-config` prints the translated command and expected artifacts

Examples:
  python scripts/smoke_train_debug.py --help
  python scripts/smoke_train_debug.py --dry-run-config
  python scripts/smoke_train_debug.py --random-agent
  python scripts/smoke_train_debug.py --repo-root /path/to/dreamerv3
"""

from __future__ import annotations

import argparse
import shlex
import sys
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
  parser = argparse.ArgumentParser(
      description='Run a tiny CPU DreamerV3 smoke or print the command.',
      formatter_class=argparse.RawDescriptionHelpFormatter,
      epilog=(
          'The wrapper translates short flags into DreamerV3 dotted config keys.\n'
          'Default smoke settings are intentionally tiny and CPU-safe.'
      ),
  )
  parser.add_argument(
      '--repo-root',
      type=Path,
      help='Optional local checkout override for development only.',
  )
  parser.add_argument(
      '--dry-run-config',
      action='store_true',
      help='Print the translated DreamerV3 command and exit.',
  )
  parser.add_argument(
      '--configs',
      nargs='+',
      default=['debug'],
      help='DreamerV3 config blocks to apply in order.',
  )
  parser.add_argument(
      '--task',
      default='dummy_disc',
      help='DreamerV3 task name, defaulting to the dummy smoke env.',
  )
  parser.add_argument(
      '--logdir',
      default='~/logdir/dreamer/debug/{timestamp}',
      help='Target logdir passed through to DreamerV3.',
  )
  parser.add_argument(
      '--steps',
      type=int,
      default=16,
      help='Maps to run.steps; keep this tiny for smoke runs.',
  )
  parser.add_argument(
      '--train-ratio',
      type=float,
      default=1.0,
      help='Maps to run.train_ratio; 1.0 is a safe smoke default.',
  )
  parser.add_argument(
      '--envs',
      type=int,
      default=1,
      help='Maps to run.envs; 1 avoids multiprocess fanout.',
  )
  parser.add_argument(
      '--jax-platform',
      default='cpu',
      help='Maps to jax.platform; cpu is the smoke default.',
  )
  parser.add_argument(
      '--batch-size',
      type=int,
      default=1,
      help='Maps to batch_size; 1 keeps replay warmup cheap.',
  )
  parser.add_argument(
      '--random-agent',
      action='store_true',
      help='Enable the no-op random agent for pure plumbing smoke tests.',
  )
  parser.add_argument(
      '--from-checkpoint',
      default='',
      help='Optional run.from_checkpoint value for resume smoke checks.',
  )
  parser.add_argument(
      '--from-checkpoint-regex',
      default='',
      help='Optional run.from_checkpoint_regex value for partial restore checks.',
  )
  return parser


def build_dreamerv3_argv(args: argparse.Namespace) -> list[str]:
  argv = [
      '--configs', *args.configs,
      '--task', args.task,
      '--logdir', args.logdir,
      '--batch_size', str(args.batch_size),
      '--jax.platform', args.jax_platform,
      '--run.steps', str(args.steps),
      '--run.train_ratio', str(args.train_ratio),
      '--run.envs', str(args.envs),
  ]
  if args.random_agent:
    argv += ['--random_agent', 'True']
  if args.from_checkpoint:
    argv += ['--run.from_checkpoint', args.from_checkpoint]
  if args.from_checkpoint_regex:
    argv += ['--run.from_checkpoint_regex', args.from_checkpoint_regex]
  return argv


def print_dry_run(argv: list[str], args: argparse.Namespace) -> None:
  cmd = ['python', '-m', 'dreamerv3.main', *argv]
  print('DreamerV3 smoke configuration')
  if args.repo_root is not None:
    print(f'Local-dev override: {args.repo_root}')
  print()
  print('Translated command:')
  print('  ' + shlex.join(cmd))
  print()
  print('Expected artifacts:')
  print('  - config.yaml')
  print('  - ckpt/')
  print('  - metrics.jsonl and scores.jsonl once the log interval is reached')
  if args.random_agent:
    print('  - random-agent plumbing smoke; Dreamer model training is disabled')
  else:
    print('  - Dreamer training loop smoke with the debug preset')
  print()
  print('Resume rule: reuse the same logdir only when the checkpoint shape is compatible.')


def run_main(argv: list[str], repo_root: Path | None) -> None:
  if repo_root is not None:
    resolved = repo_root.expanduser().resolve()
    if not resolved.exists():
      raise SystemExit(f'--repo-root does not exist: {resolved}')
    sys.path.insert(0, str(resolved))

  from dreamerv3.main import main as dreamerv3_main

  dreamerv3_main(argv)


def main() -> None:
  parser = build_parser()
  args = parser.parse_args()
  dreamerv3_argv = build_dreamerv3_argv(args)

  if args.dry_run_config:
    print_dry_run(dreamerv3_argv, args)
    return

  run_main(dreamerv3_argv, args.repo_root)


if __name__ == '__main__':
  main()
