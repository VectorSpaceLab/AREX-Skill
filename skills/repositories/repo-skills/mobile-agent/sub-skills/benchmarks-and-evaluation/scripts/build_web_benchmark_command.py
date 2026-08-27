#!/usr/bin/env python3
"""Print a safe Mobile-Agent-v3.5 web benchmark command."""
from __future__ import annotations
import argparse, shlex

def env_ref(n):
    if not n or not n.replace('_','').replace('-','').isalnum(): raise SystemExit(f'invalid env var: {n!r}')
    return f'"${{{n}}}"'

def val(v,e,label):
    if v is not None: return shlex.quote(v)
    if e: return env_ref(e)
    raise SystemExit(f'missing --{label} or --{label}-env')

def main():
    p=argparse.ArgumentParser(description='Build WebArena/WebVoyager/VisualWebArena-style GUI-Owl benchmark command.')
    p.add_argument('--repo-root'); p.add_argument('--repo-root-env', default='MOBILE_AGENT_REPO')
    p.add_argument('--task-id', default=''); p.add_argument('--task', required=True); p.add_argument('--web', default='')
    p.add_argument('--model'); p.add_argument('--model-env', default='GUI_OWL_MODEL')
    p.add_argument('--base-url'); p.add_argument('--base-url-env', default='GUI_OWL_BASE_URL')
    p.add_argument('--output-dir', default='results_log'); p.add_argument('--rollout-id', default='0'); p.add_argument('--max-iter', type=int, default=50)
    p.add_argument('--image-type', choices=['oss','base64','file'], default='oss')
    p.add_argument('--headless', action='store_true'); p.add_argument('--login', action='store_true')
    p.add_argument('--use-css-som', action='store_true'); p.add_argument('--use-omni-som', action='store_true'); p.add_argument('--omni-url', default='')
    p.add_argument('--eval', action='store_true'); p.add_argument('--eval-model', default='o4-mini-2025-04-16'); p.add_argument('--eval-mode', default='WebJudge_Online_Mind2Web_eval')
    p.add_argument('--one-line', action='store_true')
    a=p.parse_args()
    if a.use_css_som and a.use_omni_som: raise SystemExit('choose only one SoM mode')
    repo=shlex.quote(a.repo_root) if a.repo_root else env_ref(a.repo_root_env)
    parts=['cd',f'{repo}/Mobile-Agent-v3.5/web_benchmark','&&','python','main_for_eval.py','--task',shlex.quote(a.task),
           '--model',val(a.model,a.model_env,'model'),'--base_url',val(a.base_url,a.base_url_env,'base-url'),
           '--output_dir',shlex.quote(a.output_dir),'--rollout_id',shlex.quote(a.rollout_id),'--max_iter',str(a.max_iter),'--image_type',a.image_type]
    if a.task_id: parts += ['--task_id', shlex.quote(a.task_id)]
    if a.web: parts += ['--web', shlex.quote(a.web)]
    if a.headless: parts.append('--headless')
    if a.login: parts.append('--login')
    if a.use_css_som: parts.append('--use_css_som')
    if a.use_omni_som: parts.append('--use_omni_som')
    if a.omni_url: parts += ['--omni_url', shlex.quote(a.omni_url)]
    if a.eval: parts += ['--eval','--eval_model',shlex.quote(a.eval_model),'--eval_mode',shlex.quote(a.eval_mode)]
    if not a.one_line: print('# Safe template only: browser services/login/OSS/API/judge model are live prerequisites.')
    print(' '.join(parts))
if __name__=='__main__': main()
