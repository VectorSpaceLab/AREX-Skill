#!/usr/bin/env python3
"""Build a VSE Sushi CLI command without executing it."""
from __future__ import annotations
import argparse, shlex

def main() -> int:
    ap=argparse.ArgumentParser(description='Print a safe python -m backend.sushi command for subtitle sync.')
    ap.add_argument('--src', required=True)
    ap.add_argument('--dst', required=True)
    ap.add_argument('--script', required=True)
    ap.add_argument('--output', '-o')
    ap.add_argument('--temp-dir')
    ap.add_argument('--no-cleanup', action='store_true')
    ap.add_argument('--verbose', '-v', action='store_true')
    ap.add_argument('--extra', nargs='*', default=[], help='Additional raw Sushi flags, e.g. --extra --window 20')
    args=ap.parse_args()
    cmd=['python','-m','backend.sushi','--src',args.src,'--dst',args.dst,'--script',args.script]
    if args.output: cmd += ['--output', args.output]
    if args.temp_dir: cmd += ['--temp-dir', args.temp_dir]
    if args.no_cleanup: cmd.append('--no-cleanup')
    if args.verbose: cmd.append('--verbose')
    cmd += args.extra
    print(' '.join(shlex.quote(x) for x in cmd))
    return 0
if __name__=='__main__':
    raise SystemExit(main())
