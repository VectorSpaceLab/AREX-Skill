#!/usr/bin/env python3
import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path


def run_py(code):
    return subprocess.run([sys.executable, '-c', code], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', required=True, choices=['source_boundary', 'target_match', 'ablation_unnormalized', 'api_imports', 'mechanism_threshold'])
    parser.add_argument('--attempt-dir', required=True)
    parser.add_argument('--skills-root', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    attempt = Path(args.attempt_dir)
    skills = Path(args.skills_root)
    result = {'schema_version': 1, 'check': args.check, 'ok': False, 'metric': None, 'details': {}}
    if args.check == 'source_boundary':
        manifest = json.loads((attempt/'recovery/source_manifest.json').read_text())
        result['ok'] = not manifest.get('original_repo_used_during_recovery', True) and 'repo' not in ' '.join(manifest.get('allowed_sources_used', []))
        result['metric'] = 1.0 if result['ok'] else 0.0
        result['details'] = {'original_repo_used': manifest.get('original_repo_used_during_recovery')}
    elif args.check == 'target_match':
        plan = json.loads((attempt/'module_plan.json').read_text())['fast_recovery_target']
        recovery = json.loads((attempt/'recovery/recovery_result.json').read_text())['paper_target']
        result['ok'] = plan == recovery
        result['metric'] = 1.0 if result['ok'] else 0.0
        result['details'] = {'plan_metric': plan.get('metric'), 'recovery_metric': recovery.get('metric')}
    elif args.check == 'ablation_unnormalized':
        code = f"""
import sys
sys.path.insert(0, {str(skills/'clip_contrastive_objective'/'scripts')!r})
from contrastive_objective import compute_contrastive
matched=compute_contrastive([[10,0],[0,1]], [[1,0],[0,1]], 10.0)
print(matched['loss'])
"""
        proc = run_py(code)
        loss = float(proc.stdout.strip()) if proc.returncode == 0 else None
        result['ok'] = proc.returncode == 0 and loss is not None and loss > 0
        result['metric'] = loss
        result['details'] = {'returncode': proc.returncode, 'stderr_tail': proc.stderr[-500:]}
    elif args.check == 'api_imports':
        modules = {
            'scale': skills/'openclip_scale_protocol'/'scripts',
            'contrastive': skills/'clip_contrastive_objective'/'scripts',
            'eval': skills/'clip_zeroshot_retrieval_eval'/'scripts',
            'fit': skills/'clip_power_law_scaling'/'scripts'
        }
        code = '\n'.join([f"import sys; sys.path.insert(0, {str(path)!r})" for path in modules.values()]) + "\nfrom scale_protocol import build_scale_table\nfrom contrastive_objective import compute_contrastive\nfrom zeroshot_retrieval_eval import evaluate_clip_embeddings\nfrom power_law_scaling import fit_power_law\nprint('imports_ok')\n"
        proc = run_py(code)
        result['ok'] = proc.returncode == 0 and 'imports_ok' in proc.stdout
        result['metric'] = 1.0 if result['ok'] else 0.0
        result['details'] = {'stdout_tail': proc.stdout[-500:], 'stderr_tail': proc.stderr[-500:]}
    elif args.check == 'mechanism_threshold':
        recovery = json.loads((attempt/'recovery/recovery_result.json').read_text())
        checks = recovery.get('mechanism_checks', {})
        required = ['scale_table_constructed','normalized_embeddings_checked','contrastive_loss_computed','zeroshot_accuracy_computed','retrieval_recall_computed','power_law_fit_executed']
        passed = sum(1 for key in required if checks.get(key) is True)
        result['ok'] = passed == len(required)
        result['metric'] = passed / len(required)
        result['details'] = {'passed': passed, 'required': len(required)}
    Path(args.output).write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result))
    return 0 if result['ok'] else 1

if __name__ == '__main__':
    raise SystemExit(main())
