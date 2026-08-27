#!/usr/bin/env python3
"""Print a safe UI-S1 / verl GRPO-DAPO training command template."""
from __future__ import annotations
import argparse, shlex

def main():
    p=argparse.ArgumentParser(description='Build UI-S1 training command without starting Ray/vLLM/training.')
    p.add_argument('--repo-root'); p.add_argument('--repo-root-env', default='MOBILE_AGENT_REPO')
    p.add_argument('--config-path', default='examples/qwen_gui_static_grpo/config'); p.add_argument('--config-name', default='traj_grpo')
    p.add_argument('--train-files', required=True); p.add_argument('--val-files', default=''); p.add_argument('--model-path', required=True)
    p.add_argument('--preset', default='uis1-7b'); p.add_argument('--gpus-per-node', type=int, default=8); p.add_argument('--nnodes', type=int, default=1)
    p.add_argument('--engine', choices=['vllm','sglang'], default='vllm'); p.add_argument('--train-batch-size', type=int); p.add_argument('--val-batch-size', type=int)
    p.add_argument('--project-name', default='gui_traj_grpo'); p.add_argument('--experiment-name', default='mobile-agent-ui-s1')
    p.add_argument('--workdir', default=''); p.add_argument('--extra', action='append', default=[]); p.add_argument('--one-line', action='store_true')
    a=p.parse_args()
    repo=shlex.quote(a.repo_root) if a.repo_root else f'"${{{a.repo_root_env}}}"'
    train=f'{repo}/UI-S1' if not a.workdir else shlex.quote(a.workdir)
    parts=['cd',train,'&&','python3','-m','verl.trainer.main_dapo',f'--config-path={shlex.quote(a.config_path)}',f'--config-name={shlex.quote(a.config_name)}','algorithm.adv_estimator=uis1',f'data.train_files={shlex.quote(a.train_files)}',f'actor_rollout_ref.model.path={shlex.quote(a.model_path)}',f'actor_rollout_ref.rollout.name={a.engine}',f'trainer.project_name={shlex.quote(a.project_name)}',f'trainer.experiment_name={shlex.quote(a.experiment_name)}',f'trainer.n_gpus_per_node={a.gpus_per_node}',f'trainer.nnodes={a.nnodes}']
    if a.val_files: parts.append(f'data.val_files={shlex.quote(a.val_files)}')
    if a.train_batch_size: parts.append(f'data.train_batch_size={a.train_batch_size}')
    if a.val_batch_size: parts.append(f'data.val_batch_size={a.val_batch_size}')
    parts += [shlex.quote(x) for x in a.extra]
    if not a.one_line:
        print(f'# Safe template only: preset={a.preset}; no Ray, vLLM, model download, or training is started.')
        print(f'# WARNING: many UI-S1 public examples assume 8 GPUs; gpus-per-node={a.gpus_per_node} needs a compatible prepared host.')
        print('# Verify CUDA/PyTorch, flash-attn, Ray, vLLM/sglang, checkpoints, dataset paths, and ports before running.')
    print(' '.join(parts))
if __name__=='__main__': main()
