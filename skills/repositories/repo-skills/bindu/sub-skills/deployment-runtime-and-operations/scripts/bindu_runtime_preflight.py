#!/usr/bin/env python3
"""Safe Bindu runtime preflight: no deployment, no server start."""
from __future__ import annotations
import argparse, json, os, shutil, socket
from pathlib import Path

def port_free(port:int)->bool:
    s=socket.socket(); s.settimeout(0.2)
    try: s.bind(('127.0.0.1', port)); return True
    except OSError: return False
    finally: s.close()

def sensitive_count(root:Path)->int:
    pats={'.env','.pem','.key','.p12','.pfx','id_rsa','id_dsa','id_ecdsa','id_ed25519','credentials.json','credentials.yaml','credentials.yml'}
    count=0
    for p in root.rglob('*'):
        if p.is_file() and (p.name in pats or p.name.startswith('.env')): count += 1
    return count

def main():
    ap=argparse.ArgumentParser(description=__doc__); ap.add_argument('--root', default='.'); ap.add_argument('--ports', default='3773,3774'); ap.add_argument('--json', action='store_true'); args=ap.parse_args()
    root=Path(args.root).resolve()
    data={'bindu_cli': bool(shutil.which('bindu')), 'boxd_token_present': bool(os.getenv('BOXD_API_KEY') or os.getenv('BOXD_TOKEN')), 'root_markers': [m for m in ['pyproject.toml','setup.py','requirements.txt','.git'] if (root/m).exists()], 'sensitive_file_count': sensitive_count(root), 'ports': {p: port_free(int(p)) for p in args.ports.split(',') if p.strip()}}
    print(json.dumps(data, indent=2, sort_keys=True) if args.json else data)
if __name__=='__main__': main()
