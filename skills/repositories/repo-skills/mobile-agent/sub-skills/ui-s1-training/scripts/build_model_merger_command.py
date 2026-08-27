#!/usr/bin/env python3
"""Build safe UI-S1/verl model_merger.py commands."""
from __future__ import annotations
import argparse, shlex

def main():
    p=argparse.ArgumentParser(description='Print UI-S1 checkpoint merge/test command without loading checkpoints.')
    p.add_argument('--repo-root'); p.add_argument('--repo-root-env', default='MOBILE_AGENT_REPO')
    p.add_argument('--operation', choices=['merge','test'], default='merge')
    p.add_argument('--backend', choices=['fsdp','megatron'], default='fsdp')
    p.add_argument('--local-dir', required=True); p.add_argument('--target-dir', default='tmp'); p.add_argument('--hf-model-path')
    p.add_argument('--test-hf-dir'); p.add_argument('--hf-upload-path'); p.add_argument('--private', action='store_true')
    p.add_argument('--tie-word-embedding', action='store_true'); p.add_argument('--is-value-model', action='store_true')
    a=p.parse_args()
    if a.operation=='test' and not a.test_hf_dir: raise SystemExit('--test-hf-dir required for test')
    repo=shlex.quote(a.repo_root) if a.repo_root else f'"${{{a.repo_root_env}}}"'
    parts=['cd',f'{repo}/UI-S1','&&','python','scripts/model_merger.py',a.operation,'--backend',a.backend,'--local_dir',shlex.quote(a.local_dir)]
    if a.operation=='merge': parts += ['--target_dir', shlex.quote(a.target_dir)]
    if a.hf_model_path: parts += ['--hf_model_path', shlex.quote(a.hf_model_path)]
    if a.test_hf_dir: parts += ['--test_hf_dir', shlex.quote(a.test_hf_dir)]
    if a.hf_upload_path: parts += ['--hf_upload_path', shlex.quote(a.hf_upload_path)]
    if a.private: parts.append('--private')
    if a.tie_word_embedding: parts.append('--tie-word-embedding')
    if a.is_value_model: parts.append('--is-value-model')
    print('# Safe template only: verify checkpoint layout/config/backend and avoid upload without private HF token.')
    print(' '.join(parts))
if __name__=='__main__': main()
