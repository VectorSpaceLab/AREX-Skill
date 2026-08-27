#!/usr/bin/env python3
"""Validate legacy Mobile-Agent config notes before building commands."""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path

def main():
    p=argparse.ArgumentParser(description='Validate legacy Mobile-Agent config shape.')
    p.add_argument('--config', required=True)
    a=p.parse_args()
    try: obj=json.loads(Path(a.config).read_text(encoding='utf-8'))
    except Exception as e: print(f'ERROR: cannot parse config: {e}', file=sys.stderr); return 2
    errors=[]; warnings=[]
    version=obj.get('version')
    if version not in {'v1-local','v1-api','v2','v3-android','v3-harmony'}:
        errors.append('version must be v1-local, v1-api, v2, v3-android, or v3-harmony')
    if not obj.get('instruction'): errors.append('instruction is required')
    if version in {'v1-local','v1-api','v3-android'} and not obj.get('adb_path'):
        errors.append(f'{version} requires adb_path')
    if version=='v3-harmony':
        if not obj.get('hdc_path'): errors.append('v3-harmony requires hdc_path')
        if obj.get('adb_path'): errors.append('v3-harmony must not also set adb_path')
    if version=='v1-api':
        for k in ['url','token_env']:
            if not obj.get(k): errors.append(f'v1-api requires {k}')
    if version=='v1-local': warnings.append('v1-local requires legacy local perception stack and model downloads')
    if version=='v2':
        warnings.append('v2 settings are edited variables in run.py, not CLI flags')
        for k in ['api_url','token_env','caption_call_method','caption_model','add_info']:
            if not obj.get(k): warnings.append(f'v2 config missing recommended edited setting {k}')
    if version and version.startswith('v3'):
        for k in ['api_key_env','base_url','model']:
            if not obj.get(k): errors.append(f'{version} requires {k}')
        if obj.get('coor_type')=='qwen-vl': warnings.append('qwen-vl coordinate mode maps normalized 0..1000 coordinates')
    print('version=',version)
    for w in warnings: print('WARNING:',w)
    for e in errors: print('ERROR:',e,file=sys.stderr)
    return 2 if errors else 0
if __name__=='__main__': raise SystemExit(main())
