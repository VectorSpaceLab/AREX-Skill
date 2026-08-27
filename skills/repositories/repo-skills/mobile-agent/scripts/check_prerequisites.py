#!/usr/bin/env python3
"""Report MobileAgent route prerequisites without live side effects."""
from __future__ import annotations
import argparse, importlib.util, json, os, shutil, sys

ROUTES={'current-gui-owl','benchmarks','mobile-agent-e','pc-agent','legacy-agents','ui-s1-training'}

def have_module(name): return importlib.util.find_spec(name) is not None

def route_report(route):
    r={'route':route,'checks':{},'warnings':[]}
    if route in {'current-gui-owl','mobile-agent-e','legacy-agents','benchmarks'}:
        r['checks']['adb_in_path']=bool(shutil.which('adb'))
        r['checks']['ADB_PATH_env_set']=bool(os.environ.get('ADB_PATH'))
        if not (r['checks']['adb_in_path'] or r['checks']['ADB_PATH_env_set']): r['warnings'].append('ADB not found/exported; Android live routes need adb or explicit path')
    if route=='legacy-agents':
        r['checks']['hdc_in_path']=bool(shutil.which('hdc'))
        r['checks']['HDC_PATH_env_set']=bool(os.environ.get('HDC_PATH'))
    if route in {'current-gui-owl','pc-agent','benchmarks'}:
        r['checks']['display_env_set']=bool(os.environ.get('DISPLAY') or os.environ.get('WAYLAND_DISPLAY'))
        if not r['checks']['display_env_set']: r['warnings'].append('No DISPLAY/WAYLAND_DISPLAY; desktop/browser live control may need an interactive GUI session')
    if route in {'current-gui-owl','benchmarks'}:
        r['checks']['playwright_importable']=have_module('playwright')
    if route in {'ui-s1-training','mobile-agent-e'}:
        r['checks']['torch_importable']=have_module('torch')
        try:
            import torch  # type: ignore
            r['checks']['torch_cuda_available']=bool(torch.cuda.is_available())
        except Exception:
            r['checks']['torch_cuda_available']=False
    if route=='ui-s1-training' and not r['checks'].get('torch_cuda_available'):
        r['warnings'].append('CUDA not proven; UI-S1 live training/eval remains unverified')
    for env in ['GUI_OWL_API_KEY','GUI_OWL_BASE_URL','GUI_OWL_MODEL','MOBILE_AGENT_REPO']:
        if route in {'current-gui-owl','benchmarks','legacy-agents'}:
            r['checks'][f'{env}_set']=bool(os.environ.get(env))
    return r

def main():
    p=argparse.ArgumentParser(description='Check host prerequisites without connecting to devices, browsers, APIs, or GPUs.')
    p.add_argument('--route', action='append', choices=sorted(ROUTES), required=True)
    p.add_argument('--strict', action='store_true', help='Exit nonzero if warnings exist.')
    p.add_argument('--json', action='store_true', help='Emit JSON only.')
    a=p.parse_args()
    reports=[route_report(r) for r in a.route]
    if a.json:
        print(json.dumps(reports, indent=2))
    else:
        for rep in reports:
            print(f"route={rep['route']}")
            for k,v in rep['checks'].items(): print(f"  {k}={v}")
            for w in rep['warnings']: print(f"  WARNING: {w}")
    return 2 if a.strict and any(r['warnings'] for r in reports) else 0
if __name__=='__main__': raise SystemExit(main())
