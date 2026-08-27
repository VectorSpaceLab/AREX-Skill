#!/usr/bin/env python3
"""Run the TensorLayer CLI help text safely.

The helper unsets an empty CUDA_VISIBLE_DEVICES value before invoking the CLI
because tensorlayer.cli.train currently parses an empty token as int("") and
crashes. Leave the variable unset if you want the help smoke to pass.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        '--python',
        default=sys.executable,
        help='Python executable used to invoke tensorlayer.cli.',
    )
    args = parser.parse_args()

    env = os.environ.copy()
    if env.get('CUDA_VISIBLE_DEVICES', '__unset__') == '':
        env.pop('CUDA_VISIBLE_DEVICES', None)
        print('note: unset empty CUDA_VISIBLE_DEVICES before running tensorlayer.cli', file=sys.stderr)

    proc = subprocess.run(
        [args.python, '-m', 'tensorlayer.cli', '--help'],
        text=True,
        capture_output=True,
        env=env,
    )

    sys.stdout.write(proc.stdout)
    if proc.returncode != 0:
        sys.stderr.write(proc.stderr)
        return proc.returncode

    if 'train' not in proc.stdout:
        print('train subcommand not shown in help output', file=sys.stderr)
        return 2

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
