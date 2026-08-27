#!/usr/bin/env python3
"""Build safe PC-Agent current/v1 command templates."""
from __future__ import annotations
import argparse, shlex

def env_ref(n):
    if not n or not n.replace('_','').replace('-','').isalnum(): raise SystemExit(f'invalid env var: {n!r}')
    return f'"${{{n}}}"'

def choose(v,e,label,required=False):
    if v is not None: return shlex.quote(v)
    if e: return env_ref(e)
    if required: raise SystemExit(f'missing --{label} or --{label}-env')
    return None

def main():
    p=argparse.ArgumentParser(description='Print PC-Agent command without live desktop/API actions.')
    p.add_argument('--repo-root'); p.add_argument('--repo-root-env', default='MOBILE_AGENT_REPO')
    p.add_argument('--version', choices=['current','v1'], default='current')
    p.add_argument('--instruction', required=True); p.add_argument('--os', choices=['mac','windows'], default='mac')
    p.add_argument('--config', default='config.json')
    p.add_argument('--api-url'); p.add_argument('--api-url-env'); p.add_argument('--api-token'); p.add_argument('--api-token-env')
    p.add_argument('--qwen-api-env')
    p.add_argument('--add-info', default='')
    p.add_argument('--use-som', type=int, choices=[0,1], default=1); p.add_argument('--draw-text-box', type=int, choices=[0,1], default=0)
    p.add_argument('--ratio', type=float); p.add_argument('--font-path')
    p.add_argument('--use-a11y', type=int, choices=[0,1], default=1); p.add_argument('--ocr-api', type=int, choices=[0,1], default=1)
    p.add_argument('--num-step-limit', type=int, default=20); p.add_argument('--screenshot-root', default='task_')
    p.add_argument('--disable-reflection', action='store_true'); p.add_argument('--one-line', action='store_true')
    a=p.parse_args()
    repo=shlex.quote(a.repo_root) if a.repo_root else env_ref(a.repo_root_env)
    if a.version=='current':
        parts=['cd',f'{repo}/PC-Agent','&&','python','run.py','--instruction',shlex.quote(a.instruction),'--mac','1' if a.os=='mac' else '0','--use_som',str(a.use_som),'--draw_text_box',str(a.draw_text_box),'--use_a11y',str(a.use_a11y),'--ocr_api',str(a.ocr_api),'--num_step_limit',str(a.num_step_limit),'--screenshot_root',shlex.quote(a.screenshot_root)]
        parts += ['--ratio', str(a.ratio if a.ratio is not None else (2.0 if a.os=='mac' else 1.0))]
        if a.font_path: parts += ['--font_path', shlex.quote(a.font_path)]
        if a.add_info: parts += ['--add_info', shlex.quote(a.add_info)]
        if a.disable_reflection: parts += ['--disable_reflection','1']
        if a.config != 'config.json':
            parts.insert(2, '&&'); parts.insert(2, f'cp {shlex.quote(a.config)} config.json')
    else:
        parts=['cd',f'{repo}/PC-Agent','&&','python','run_v1.py','--instruction',shlex.quote(a.instruction),'--pc_type',a.os,'--use_som',str(a.use_som),'--draw_text_box',str(a.draw_text_box)]
        if a.api_url or a.api_url_env: parts += ['--api_url', choose(a.api_url,a.api_url_env,'api-url')]
        if a.api_token or a.api_token_env: parts += ['--api_token', choose(a.api_token,a.api_token_env,'api-token')]
        if a.qwen_api_env: parts += ['--qwen_api', env_ref(a.qwen_api_env)]
        if a.add_info: parts += ['--add_info', shlex.quote(a.add_info)]
        if a.disable_reflection: parts.append('--disable_reflection')
    if not a.one_line:
        print('# Safe template only: live PC-Agent requires Mac/Windows GUI session, screenshot/accessibility permissions, OCR/API credentials, and private config.')
        print('# For current PC-Agent, model/token/url are read from config.json; keep it private and redacted.')
    print(' '.join(parts))
if __name__=='__main__': main()
