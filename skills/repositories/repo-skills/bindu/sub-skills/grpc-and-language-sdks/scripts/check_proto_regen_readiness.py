#!/usr/bin/env python3
"""Read-only Bindu proto regeneration readiness check."""
from __future__ import annotations
import argparse, importlib.util, json, shutil
from pathlib import Path

def find_root(start: Path) -> Path:
    for p in [start.resolve(), *start.resolve().parents]:
        if (p/'proto'/'agent_handler.proto').is_file() and (p/'pyproject.toml').is_file(): return p
    return start.resolve()

def main() -> int:
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('--root', default='.', help='Bindu checkout root or subdirectory'); p.add_argument('--json', action='store_true'); args=p.parse_args()
    root=find_root(Path(args.root))
    checks={
        'proto': (root/'proto'/'agent_handler.proto').is_file(),
        'script': (root/'scripts'/'generate_protos.sh').is_file(),
        'python_generated_dir': (root/'bindu'/'grpc'/'generated').is_dir(),
        'typescript_sdk_dir': (root/'sdks'/'typescript').is_dir(),
        'grpc_tools_importable': importlib.util.find_spec('grpc_tools') is not None,
        'node': shutil.which('node') is not None,
        'npm': shutil.which('npm') is not None,
        'npx': shutil.which('npx') is not None,
    }
    data={'root_detected': str(root), 'checks': checks, 'commands':['bash scripts/generate_protos.sh python','bash scripts/generate_protos.sh typescript','bash scripts/generate_protos.sh all'], 'ok_required': checks['proto'] and checks['script'] and checks['python_generated_dir']}
    print(json.dumps(data, indent=2, sort_keys=True) if args.json else '\n'.join([f"{k}: {v}" for k,v in data.items()]))
    return 0 if data['ok_required'] else 1
if __name__ == '__main__': raise SystemExit(main())
