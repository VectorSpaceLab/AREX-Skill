import json
CORE = ['state_memory_model','interruptible_strategy_controller','combat_priority_scorer','survival_resource_rules']

def evaluate_proxy_trace(trace):
    inv = set(trace.get('invoked_skills', []))
    checks = {
        'all_core_skills_invoked': all(x in inv for x in CORE),
        'state_memory_has_flags': bool(trace.get('state_memory', {}).get('derived_flags')),
        'strategy_has_explicit_actions': bool(trace.get('strategy', {}).get('actions')),
        'combat_has_safety_reason': any(r for item in trace.get('combat', {}).get('ranked_actions', []) for r in item.get('reasons', []) if 'hazard' in r or 'blocker' in r),
        'survival_decision_recorded': bool(trace.get('survival', {}).get('action')),
        'executable_command_evidence': bool(trace.get('command_evidence')),
    }
    passed = sum(1 for v in checks.values() if v)
    missing = [k for k,v in checks.items() if not v]
    return {'mechanism_checks': checks, 'mechanism_pass_rate': passed / len(checks), 'missing': missing}

def main():
    import argparse
    p=argparse.ArgumentParser(); p.add_argument('trace'); p.add_argument('--output', required=True)
    a=p.parse_args(); json.dump(evaluate_proxy_trace(json.load(open(a.trace))), open(a.output,'w'), indent=2)
if __name__ == '__main__': main()
