#!/usr/bin/env python3
"""Print a safe OSWorld command for MobileAgent v3/GUI-Owl variants."""
from __future__ import annotations
import argparse, shlex

def env_ref(n): return f'"${{{n}}}"'
def choose(v,e,label):
    if v is not None: return shlex.quote(v)
    if e: return env_ref(e)
    raise SystemExit(f'missing --{label} or --{label}-env')

def main():
    p=argparse.ArgumentParser(description='Build OSWorld command without launching a VM.')
    p.add_argument('--repo-root'); p.add_argument('--repo-root-env', default='MOBILE_AGENT_REPO')
    p.add_argument('--variant', choices=['mobile-agent-v3','gui-owl'], default='mobile-agent-v3')
    p.add_argument('--path-to-vm', required=True); p.add_argument('--test-all-meta-path', default=''); p.add_argument('--result-dir', default='./results')
    p.add_argument('--domain', default='all'); p.add_argument('--num-envs', type=int, default=1); p.add_argument('--max-steps', type=int, default=50)
    p.add_argument('--model'); p.add_argument('--model-env', default='GUI_OWL_MODEL'); p.add_argument('--api-key'); p.add_argument('--api-key-env', default='GUI_OWL_API_KEY'); p.add_argument('--api-url'); p.add_argument('--api-url-env', default='GUI_OWL_BASE_URL')
    p.add_argument('--engine', default='openai'); p.add_argument('--one-line', action='store_true')
    a=p.parse_args()
    repo=shlex.quote(a.repo_root) if a.repo_root else env_ref(a.repo_root_env)
    script='run_multienv_mobileagent_v3.py' if a.variant=='mobile-agent-v3' else 'run_multienv_owl.py'
    parts=['cd',f'{repo}/Mobile-Agent-v3/os_world_v3','&&','python',script,'--path_to_vm',shlex.quote(a.path_to_vm),'--result_dir',shlex.quote(a.result_dir),'--domain',shlex.quote(a.domain),'--num_envs',str(a.num_envs),'--max_steps',str(a.max_steps),'--engine',shlex.quote(a.engine),'--model',choose(a.model,a.model_env,'model'),'--api_key',choose(a.api_key,a.api_key_env,'api-key'),'--api_url',choose(a.api_url,a.api_url_env,'api-url')]
    if a.test_all_meta_path: parts += ['--test_all_meta_path', shlex.quote(a.test_all_meta_path)]
    if not a.one_line: print('# Safe template only: requires OSWorld VM, service config, display automation, and model API.')
    print(' '.join(parts))
if __name__=='__main__': main()
