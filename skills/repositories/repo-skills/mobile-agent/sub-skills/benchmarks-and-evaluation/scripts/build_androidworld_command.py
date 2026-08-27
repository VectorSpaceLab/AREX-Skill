#!/usr/bin/env python3
"""Print a safe AndroidWorld/MiniWoB MobileAgent command template."""
from __future__ import annotations
import argparse, shlex

def env_ref(n):
    if not n or not n.replace('_','').replace('-','').isalnum(): raise SystemExit(f'invalid env var: {n!r}')
    return f'"${{{n}}}"'

def choose(value, env, label, required=True):
    if value is not None: return shlex.quote(value)
    if env: return env_ref(env)
    if required: raise SystemExit(f'missing --{label} or --{label}-env')
    return None

def main():
    p=argparse.ArgumentParser(description='Build AndroidWorld command without running emulator/API.')
    p.add_argument('--repo-root'); p.add_argument('--repo-root-env', default='MOBILE_AGENT_REPO')
    p.add_argument('--version', choices=['v35','v3'], default='v35')
    p.add_argument('--adb-path'); p.add_argument('--adb-path-env')
    p.add_argument('--model'); p.add_argument('--model-env', default='GUI_OWL_MODEL')
    p.add_argument('--api-key'); p.add_argument('--api-key-env', default='GUI_OWL_API_KEY')
    p.add_argument('--base-url'); p.add_argument('--base-url-env', default='GUI_OWL_BASE_URL')
    p.add_argument('--suite-family', default='android_world')
    p.add_argument('--agent-name', choices=['gui_owl','mobile_agent_v3'], default='mobile_agent_v3')
    p.add_argument('--tasks', help='Comma-separated task names.')
    p.add_argument('--n-task-combinations', type=int, default=1)
    p.add_argument('--task-random-seed', type=int, default=30)
    p.add_argument('--fixed-task-seed', action='store_true')
    p.add_argument('--console-port', type=int, default=5554); p.add_argument('--grpc-port', type=int, default=8554)
    p.add_argument('--checkpoint-dir', default=''); p.add_argument('--output-path', default='android_world/runs')
    p.add_argument('--traj-output-path', default=''); p.add_argument('--perform-emulator-setup', action='store_true')
    p.add_argument('--log-file', default=''); p.add_argument('--one-line', action='store_true')
    a=p.parse_args()
    repo=shlex.quote(a.repo_root) if a.repo_root else env_ref(a.repo_root_env)
    sub='Mobile-Agent-v3.5/android_world_v3.5' if a.version=='v35' else 'Mobile-Agent-v3/android_world_v3'
    script='run_ma35.py' if a.version=='v35' else 'run_ma3.py'
    parts=['cd',f'{repo}/{sub}','&&','python',script,
           f'--suite_family={shlex.quote(a.suite_family)}',f'--agent_name={a.agent_name}',
           f'--model={choose(a.model,a.model_env,"model")}',f'--api_key={choose(a.api_key,a.api_key_env,"api-key")}',
           f'--base_url={choose(a.base_url,a.base_url_env,"base-url")}',f'--console_port={a.console_port}',f'--grpc_port={a.grpc_port}',
           f'--n_task_combinations={a.n_task_combinations}',f'--task_random_seed={a.task_random_seed}',f'--output_path={shlex.quote(a.output_path)}']
    if a.adb_path or a.adb_path_env: parts.append(f'--adb_path={choose(a.adb_path,a.adb_path_env,"adb-path")}')
    if a.tasks: parts.append(f'--tasks={shlex.quote(a.tasks)}')
    if a.fixed_task_seed: parts.append('--fixed_task_seed=True')
    if a.checkpoint_dir: parts.append(f'--checkpoint_dir={shlex.quote(a.checkpoint_dir)}')
    if a.traj_output_path: parts.append(f'--traj_output_path={shlex.quote(a.traj_output_path)}')
    if a.perform_emulator_setup: parts.append('--perform_emulator_setup=True')
    cmd=' '.join(parts)
    if a.log_file: cmd += ' 2>&1 | tee ' + shlex.quote(a.log_file)
    if not a.one_line:
        print('# Safe template only: emulator/ADB ports/API/model are live prerequisites; no score is verified by this builder.')
    print(cmd)
if __name__=='__main__': main()
