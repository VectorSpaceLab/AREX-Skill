#!/usr/bin/env python3
"""Build a safe UI-S1 AndroidControl/SOP evaluation command."""
from __future__ import annotations
import argparse, shlex

def main():
    p=argparse.ArgumentParser(description='Print UI-S1 eval command without calling model server.')
    p.add_argument('--repo-root'); p.add_argument('--repo-root-env', default='MOBILE_AGENT_REPO')
    p.add_argument('--evaluator', choices=['qwenvl','agentcpm','os-atlas-7b','os-genesis-7b','ui-tars-7b'], default='qwenvl')
    p.add_argument('--jsonl-file', required=True); p.add_argument('--output-dir', required=True); p.add_argument('--model-name', required=True)
    p.add_argument('--n-history-image-limit', type=int, default=2); p.add_argument('--max-workers', type=int, default=4); p.add_argument('--one-line', action='store_true')
    a=p.parse_args()
    script={'qwenvl':'eval_qwenvl.py','agentcpm':'eval_agentcpm.py','os-atlas-7b':'eval_os-atlas-7b.py','os-genesis-7b':'eval_os-genesis-7b.py','ui-tars-7b':'eval_ui-tars-7b.py'}[a.evaluator]
    repo=shlex.quote(a.repo_root) if a.repo_root else f'"${{{a.repo_root_env}}}"'
    parts=['cd',f'{repo}/UI-S1','&&','python',f'evaluation/{script}','--jsonl_file',shlex.quote(a.jsonl_file),'--output_dir',shlex.quote(a.output_dir),'--model_name',shlex.quote(a.model_name),'--n_history_image_limit',str(a.n_history_image_limit),'--max_workers',str(a.max_workers)]
    if not a.one_line: print('# Safe template only: requires prepared model serving/API utilities and does not run here.')
    print(' '.join(parts))
if __name__=='__main__': main()
