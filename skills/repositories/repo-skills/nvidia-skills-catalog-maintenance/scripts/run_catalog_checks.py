#!/usr/bin/env python3
"""Plan or run safe local NVIDIA skills catalog maintenance checks."""
from __future__ import annotations
import argparse, json, shutil, subprocess
from pathlib import Path

PROFILES = {
    'metadata': [
        ['python3', '.github/scripts/marketplace/generate-skill-metadata.py', '--check', '--no-ai'],
        ['python3', '.github/scripts/aggregate_benchmarks.py', '--check'],
    ],
    'plugins': [
        ['bash', '.github/scripts/build-plugins.sh', '--check'],
        ['bash', '.github/scripts/version-plugins.sh', '--check'],
    ],
    'integrity': [
        ['python3', '.github/scripts/verify_content_integrity.py'],
    ],
    'pre-pr': [
        ['python3', '.github/scripts/marketplace/generate-skill-metadata.py', '--check', '--no-ai'],
        ['python3', '.github/scripts/aggregate_benchmarks.py', '--check'],
        ['bash', '.github/scripts/build-plugins.sh', '--check'],
        ['bash', '.github/scripts/version-plugins.sh', '--check'],
        ['python3', '.github/scripts/verify_content_integrity.py'],
    ],
    'regenerate-plan': [
        ['bash', '.github/scripts/regenerate-readme.sh'],
        ['python3', '.github/scripts/marketplace/generate-skill-metadata.py', '--no-ai'],
        ['python3', '.github/scripts/aggregate_benchmarks.py'],
        ['bash', '.github/scripts/build-plugins.sh'],
        ['bash', '.github/scripts/version-plugins.sh', '--apply'],
    ],
}

def main() -> int:
    ap = argparse.ArgumentParser(description='Plan or execute catalog maintenance check commands.')
    ap.add_argument('--repo-root', default='.', help='Path to NVIDIA skills catalog checkout')
    ap.add_argument('--profile', choices=sorted(PROFILES), default='pre-pr')
    ap.add_argument('--plan', action='store_true', help='Print commands without running them')
    ap.add_argument('--execute', action='store_true', help='Run commands in order')
    ap.add_argument('--json', action='store_true', help='Emit JSON result')
    args = ap.parse_args()
    root = Path(args.repo_root).resolve()
    commands = PROFILES[args.profile]
    if not args.execute:
        args.plan = True
    if args.plan:
        payload = {'repo_root': str(root), 'profile': args.profile, 'commands': [' '.join(c) for c in commands]}
        if args.json:
            print(json.dumps(payload, indent=2))
        else:
            print(f"Profile: {args.profile}")
            print(f"Repo: {root}")
            for c in commands:
                print('  ' + ' '.join(c))
        return 0
    results = []
    for cmd in commands:
        exe = shutil.which(cmd[0])
        if exe is None:
            results.append({'command': cmd, 'returncode': None, 'status': 'missing-executable'})
            break
        proc = subprocess.run(cmd, cwd=root, text=True, capture_output=True)
        results.append({'command': cmd, 'returncode': proc.returncode, 'stdout_tail': proc.stdout[-4000:], 'stderr_tail': proc.stderr[-4000:]})
        if proc.returncode != 0:
            break
    failed = [r for r in results if r.get('returncode') not in (0, None) or r.get('status')]
    if args.json:
        print(json.dumps({'repo_root': str(root), 'profile': args.profile, 'results': results}, indent=2))
    else:
        for r in results:
            print(f"$ {' '.join(r['command'])}")
            if r.get('status'):
                print(f"  {r['status']}")
            else:
                print(f"  exit {r['returncode']}")
                if r.get('stdout_tail'):
                    print(r['stdout_tail'])
                if r.get('stderr_tail'):
                    print(r['stderr_tail'])
    return 1 if failed else 0
if __name__ == '__main__':
    raise SystemExit(main())
