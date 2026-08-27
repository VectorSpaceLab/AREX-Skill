#!/usr/bin/env python3
"""Build safe legacy Mobile-Agent v1/v2/v3 command templates."""
from __future__ import annotations
import argparse, shlex

def env_ref(n):
    if not n or not n.replace('_','').replace('-','').isalnum(): raise SystemExit(f'invalid env var: {n!r}')
    return f'"${{{n}}}"'

def choose(v,e,label,required=True):
    if v is not None: return shlex.quote(v)
    if e: return env_ref(e)
    if required: raise SystemExit(f'missing --{label} or --{label}-env')
    return None

def main():
    p=argparse.ArgumentParser(description='Print legacy Mobile-Agent command templates without live device/API calls.')
    p.add_argument('--repo-root'); p.add_argument('--repo-root-env', default='MOBILE_AGENT_REPO')
    p.add_argument('--version', choices=['v1-local','v1-api','v2','v3-android','v3-harmony'], required=True)
    p.add_argument('--instruction', required=True)
    p.add_argument('--adb-path'); p.add_argument('--adb-path-env')
    p.add_argument('--hdc-path'); p.add_argument('--hdc-path-env')
    p.add_argument('--api'); p.add_argument('--api-env')
    p.add_argument('--url'); p.add_argument('--url-env')
    p.add_argument('--token'); p.add_argument('--token-env')
    p.add_argument('--api-key'); p.add_argument('--api-key-env')
    p.add_argument('--base-url'); p.add_argument('--base-url-env')
    p.add_argument('--model'); p.add_argument('--model-env')
    p.add_argument('--add-info', default='')
    p.add_argument('--coor-type', choices=['abs','qwen-vl'], default='abs')
    p.add_argument('--notetaker', action='store_true')
    p.add_argument('--one-line', action='store_true')
    a=p.parse_args()
    repo=shlex.quote(a.repo_root) if a.repo_root else env_ref(a.repo_root_env)
    if a.version=='v1-local':
        parts=['cd',f'{repo}/Mobile-Agent-v1','&&','python','run.py','--instruction',shlex.quote(a.instruction),'--adb_path',choose(a.adb_path,a.adb_path_env,'adb-path'),'--api',choose(a.api,a.api_env,'api')]
        warn='v1 local downloads/loads GroundingDINO/OCR/CLIP stack; prefer v1-api if using hosted service.'
    elif a.version=='v1-api':
        parts=['cd',f'{repo}/Mobile-Agent-v1','&&','python','run_api.py','--instruction',shlex.quote(a.instruction),'--adb_path',choose(a.adb_path,a.adb_path_env,'adb-path'),'--url',choose(a.url,a.url_env,'url'),'--token',choose(a.token,a.token_env,'token')]
        warn='v1 API uses hosted service; local GroundingDINO/CLIP/TensorFlow/ModelScope stack is not required.'
    elif a.version=='v2':
        parts=['cd',f'{repo}/Mobile-Agent-v2','&&','python','run.py']
        warn='v2 stores settings in top-of-file variables. Patch a private runtime copy for adb_path/instruction/API_url/token/caption/add_info/reflection/memory; do not expect CLI flags.'
    else:
        if a.version=='v3-android':
            device=['--adb_path',choose(a.adb_path,a.adb_path_env,'adb-path')]
        else:
            device=['--hdc_path',choose(a.hdc_path,a.hdc_path_env,'hdc-path')]
        parts=['cd',f'{repo}/Mobile-Agent-v3/mobile_v3','&&','python','run_mobileagentv3.py']+device+['--api_key',choose(a.api_key,a.api_key_env,'api-key'),'--base_url',choose(a.base_url,a.base_url_env,'base-url'),'--model',choose(a.model,a.model_env,'model'),'--instruction',shlex.quote(a.instruction),'--coor_type',a.coor_type,'--notetaker','True' if a.notetaker else 'False']
        if a.add_info: parts += ['--add_info', shlex.quote(a.add_info)]
        warn='v3 qwen-vl coor_type maps 0..1000 relative coordinates; HarmonyOS uses HDC, not ADB.'
    if not a.one_line:
        print('# Safe template only:', warn)
        print('# Verify device authorization, keyboard/input method, endpoint health, and secrets privately before live execution.')
    print(' '.join(parts))
if __name__=='__main__': main()
