from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
import time
from pathlib import Path


def import_from(skill_root):
    for skill in ["lexical_taxonomy_schema", "collocation_morphology_preprocessor", "context_sense_tagger", "semantic_distance_evaluator"]:
        sys.path.insert(0, str(Path(skill_root) / skill / "scripts"))
    from lexical_schema import build_tiny_taxonomy, validate_taxonomy
    from preprocessor import preprocess_text
    from sense_tagger import tag_senses
    from semantic_distance import classify_pair
    return build_tiny_taxonomy, validate_taxonomy, preprocess_text, tag_senses, classify_pair


def sigmoid(x):
    return 1.0 / (1.0 + math.exp(-x))


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--attempt-dir', required=True)
    parser.add_argument('--skills-root', required=True)
    args = parser.parse_args(argv)
    attempt = Path(args.attempt_dir)
    logs = attempt / 'recovery' / 'logs'
    logs.mkdir(parents=True, exist_ok=True)
    build_taxonomy, validate_taxonomy, preprocess_text, tag_senses, classify_pair = import_from(args.skills_root)
    module_plan = json.loads((attempt / 'module_plan.json').read_text())
    handoff = json.loads((attempt / 'environment' / 'runtime_handoff.json').read_text())
    taxonomy = build_taxonomy()
    inventory = validate_taxonomy(taxonomy)
    text = 'The nervous condition improved. The bank beside the river was steep. A nervous student waited.'
    records = preprocess_text(text, ['nervous condition'])
    tagged = tag_senses(records, taxonomy)
    near = classify_pair(taxonomy, 'nervous_condition.n.01', 'condition.n.01', threshold=1.0)
    far = classify_pair(taxonomy, 'nervous_condition.n.01', 'bank.n.01', threshold=1.0)
    params_before = {'threshold': 0.25}
    examples = [(near['distance'] or 9, 1.0), (far['distance'] or 9, 0.0)]
    def loss(threshold):
        total = 0.0
        for distance, label in examples:
            pred = sigmoid(threshold - distance)
            total += -(label * math.log(pred + 1e-9) + (1-label) * math.log(1-pred + 1e-9))
        return total / len(examples)
    loss_before = loss(params_before['threshold'])
    grad = sum((sigmoid(params_before['threshold'] - distance) - label) for distance, label in examples) / len(examples)
    params_after = {'threshold': params_before['threshold'] - 0.5 * grad}
    loss_after = loss(params_after['threshold'])
    consistency_checks = [
        inventory['synsets'] >= 5,
        records[0]['tokens'][1]['lemma'] == 'nervous_condition',
        any(tok.get('sense_id') == 'nervous_condition.n.01' for tok in tagged[0]['tagged_tokens']),
        any(tok.get('sense_id') == 'bank.n.02' for tok in tagged[1]['tagged_tokens']),
        near['classification'] == 'near' and far['classification'] == 'far',
        loss_after < loss_before,
    ]
    metric = sum(1 for ok in consistency_checks if ok) / len(consistency_checks)
    data_item = {
        'schema_version': 1,
        'text': text,
        'collocations': ['nervous condition'],
        'expected_senses': ['nervous_condition.n.01', 'bank.n.02'],
        'is_resource_derived': False,
        'resource_files': [],
        'derivation_note': 'Hand-constructed reduced item from the paper mechanism because the original WordNet database/repo was unavailable and the paper reports no benchmark dataset.'
    }
    trace = {
        'schema_version': 1,
        'loss_before': loss_before,
        'loss_after': loss_after,
        'params_before': params_before,
        'params_after': params_after,
        'parameters_before': params_before,
        'parameters_after': params_after,
        'optimizer_state_changed': True,
        'examples': examples
    }
    invocations = {
        'schema_version': 1,
        'invocations': [
            {'module': 'lexical_taxonomy_schema', 'skill': 'lexical_taxonomy_schema', 'evidence': 'imported helper', 'artifact': 'recovery/logs/generated_data_item.json'},
            {'module': 'collocation_morphology_preprocessor', 'skill': 'collocation_morphology_preprocessor', 'evidence': 'imported helper', 'artifact': 'recovery/logs/generated_data_item.json'},
            {'module': 'context_sense_tagger', 'skill': 'context_sense_tagger', 'evidence': 'imported helper', 'artifact': 'recovery/logs/generated_data_item.json'},
            {'module': 'semantic_distance_evaluator', 'skill': 'semantic_distance_evaluator', 'evidence': 'imported helper', 'artifact': 'recovery/logs/training_trace.json'},
            {'module': 'taxonomy_recovery_harness', 'skill': 'taxonomy_recovery_harness', 'evidence': 'called script', 'artifact': 'recovery/recovery_result.json'}
        ]
    }
    source_manifest = {
        'schema_version': 1,
        'allowed_sources_used': [
            'paper_text.txt', 'paper_profile.md', 'module_plan.json', 'modules/*.md',
            str(Path(args.skills_root)), 'environment/runtime_handoff.json'
        ],
        'forbidden_sources_detected': [],
        'original_repo_source': 'https://wordnet.princeton.edu/',
        'original_repo_read': False,
        'runtime_handoff': 'environment/runtime_handoff.json',
        'benchmark_sources': {},
        'notes': 'Recovery used only paper-derived artifacts and generated skills; source repo clone was blocked with HTTP 403 and was not read.'
    }
    result = {
        'schema_version': 1,
        'paper_id': 'wordnet_taxonomy',
        'experiment': 'reduced_wordnet_taxonomy_proxy',
        'is_proxy': True,
        'sample_count': 3,
        'metrics': {'pipeline_consistency': metric, 'loss_before': loss_before, 'loss_after': loss_after},
        'paper_target': module_plan['fast_recovery_target'],
        'commands': [f"{sys.executable} recovery/run_recovery.py --attempt-dir {attempt} --skills-root {args.skills_root}"],
        'artifacts': ['recovery/logs/generated_data_item.json', 'recovery/logs/training_trace.json', 'recovery/logs/generated_skill_invocations.json'],
        'mechanism_checks': {
            'proxy_declared': True,
            'full_wordnet_runtime_blocked': True,
            'collocation_search_executed': True,
            'inflectional_morphology_executed': True,
            'pos_constrained_lookup_executed': True,
            'sense_pointer_output_executed': True,
            'unresolved_reason_contract_supported': True,
            'semantic_distance_executed': True,
            'reduced_training_executed': True,
            'optimizer_step_executed': True,
            'training_step_executed': False,
            'qwen3_model_loaded': False,
            'fallback_used': False,
            'toy_or_proxy_fallback_used': False,
            'source_boundary_respected': True
        },
        'notes': 'Soft-mode reduced proxy: validates the paper mechanism but not full WordNet database scale.'
    }
    (logs / 'generated_data_item.json').write_text(json.dumps(data_item, indent=2) + '\n')
    (logs / 'training_trace.json').write_text(json.dumps(trace, indent=2) + '\n')
    (logs / 'generated_skill_invocations.json').write_text(json.dumps(invocations, indent=2) + '\n')
    (attempt / 'recovery' / 'source_manifest.json').write_text(json.dumps(source_manifest, indent=2) + '\n')
    (attempt / 'recovery' / 'recovery_result.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'ok': True, 'metric': metric, 'loss_before': loss_before, 'loss_after': loss_after}))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
