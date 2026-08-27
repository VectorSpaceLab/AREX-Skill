#!/usr/bin/env python3
"""Print a safe Mobile-Agent-E run.py command template."""
from __future__ import annotations
import argparse, shlex

def env_ref(n: str) -> str:
    if not n or not n.replace('_','').replace('-','').isalnum(): raise SystemExit(f'invalid env var: {n!r}')
    return f'"${{{n}}}"'

def main():
    p=argparse.ArgumentParser(description='Build Mobile-Agent-E command without running ADB/model calls.')
    p.add_argument('--repo-root'); p.add_argument('--repo-root-env', default='MOBILE_AGENT_REPO')
    group=p.add_mutually_exclusive_group(required=True)
    group.add_argument('--instruction')
    group.add_argument('--tasks-json')
    p.add_argument('--setting', choices=['individual','evolution'], default='individual')
    p.add_argument('--log-root', default='logs/mobile_agent_E')
    p.add_argument('--run-name', default='test')
    p.add_argument('--specified-tips-path'); p.add_argument('--specified-shortcuts-path')
    p.add_argument('--seed', type=int, default=1234); p.add_argument('--max-itr', type=int, default=40)
    p.add_argument('--max-consecutive-failures', type=int, default=5); p.add_argument('--max-repetitive-actions', type=int, default=5)
    p.add_argument('--overwrite-task-log-dir', action='store_true'); p.add_argument('--enable-experience-retriever', action='store_true')
    p.add_argument('--temperature', type=float, default=0.0); p.add_argument('--screenrecord', action='store_true')
    p.add_argument('--one-line', action='store_true')
    a=p.parse_args()
    if a.instruction and a.setting=='evolution':
        raise SystemExit('evolution mode is meaningful for --tasks-json; use individual for a single --instruction')
    repo=shlex.quote(a.repo_root) if a.repo_root else env_ref(a.repo_root_env)
    parts=['cd',f'{repo}/Mobile-Agent-E','&&','python','run.py','--seed',str(a.seed),'--log_root',shlex.quote(a.log_root),'--run_name',shlex.quote(a.run_name),'--setting',a.setting,'--max_itr',str(a.max_itr),'--max_consecutive_failures',str(a.max_consecutive_failures),'--max_repetitive_actions',str(a.max_repetitive_actions),'--temperature',str(a.temperature)]
    if a.instruction: parts += ['--instruction', shlex.quote(a.instruction)]
    if a.tasks_json: parts += ['--tasks_json', shlex.quote(a.tasks_json)]
    if a.specified_tips_path: parts += ['--specified_tips_path', shlex.quote(a.specified_tips_path)]
    if a.specified_shortcuts_path: parts += ['--specified_shortcuts_path', shlex.quote(a.specified_shortcuts_path)]
    if a.overwrite_task_log_dir: parts.append('--overwrite_task_log_dir')
    if a.enable_experience_retriever: parts.append('--enable_experience_retriever')
    if a.screenrecord: parts.append('--screenrecord')
    if not a.one_line:
        print('# Safe template only: Mobile-Agent-E live run needs ADB/device, configured perception/model services, and private runtime configs.')
        print('# In evolution mode, persistent_tips.txt and persistent_shortcuts.json are written under log_root/run_name.')
    print(' '.join(parts))
if __name__=='__main__': main()
