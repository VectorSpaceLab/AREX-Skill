from proxy_eval import evaluate_proxy_trace

def test_complete_trace_passes():
    trace={'invoked_skills':['state_memory_model','interruptible_strategy_controller','combat_priority_scorer','survival_resource_rules'], 'state_memory':{'derived_flags':{'low_hp':True}}, 'strategy':{'actions':[{'type':'heal'}]}, 'combat':{'ranked_actions':[{'reasons':['avoid_contact_hazard']}]}, 'survival':{'action':{'type':'eat_inventory'}}, 'command_evidence':['python recovery/run_recovery.py']}
    result=evaluate_proxy_trace(trace)
    assert result['mechanism_pass_rate'] == 1.0
    assert not result['missing']

def test_missing_invocation_fails():
    result=evaluate_proxy_trace({'invoked_skills':[], 'command_evidence':[]})
    assert result['mechanism_pass_rate'] < 1.0
    assert 'all_core_skills_invoked' in result['missing']
