#!/usr/bin/env python3
"""Build grounding or GUI-knowledge benchmark commands safely."""
from __future__ import annotations
import argparse, shlex

def main():
    p=argparse.ArgumentParser(description='Print grounding/knowledge evaluation command without loading models.')
    p.add_argument('--repo-root-env', default='MOBILE_AGENT_REPO'); p.add_argument('--repo-root')
    p.add_argument('--kind', choices=['grounding','knowledge'], required=True)
    p.add_argument('--model-path', required=True); p.add_argument('--ds-path', required=True); p.add_argument('--save-path', required=True)
    p.add_argument('--eval-benchmark-type', required=True)
    a=p.parse_args()
    repo=shlex.quote(a.repo_root) if a.repo_root else f'"${{{a.repo_root_env}}}"'
    script='eval_grounding_benchmarks.py' if a.kind=='grounding' else 'eval_gui_knowledge_benchmark.py'
    print('# Safe template only: requires dataset, checkpoint/model path, compatible GPU/CPU inference stack, and runtime budget.')
    print(' '.join(['cd',f'{repo}/Mobile-Agent-v3.5/grounding_and_kb','&&','python',script,'--model_path',shlex.quote(a.model_path),'--ds_path',shlex.quote(a.ds_path),'--save_path',shlex.quote(a.save_path),'--eval_benchmark_type',shlex.quote(a.eval_benchmark_type)]))
if __name__=='__main__': main()
