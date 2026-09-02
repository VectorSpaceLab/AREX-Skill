def target_matches(plan_target, result_target):
    return (plan_target.get('dataset') == result_target.get('dataset') and plan_target.get('metric') == result_target.get('metric') and plan_target.get('paper_value') == result_target.get('paper_value'))

def source_boundary_ok(sources, forbidden_fragment):
    return all(forbidden_fragment not in str(src) for src in sources)

def proxy_mechanism_ok(checks):
    required = ['symbolic_observation_parsed','action_protocol_exercised','rnd_bonus_computed','reduced_training_executed','optimizer_step_executed','evaluation_metric_computed']
    return all(checks.get(k) is True for k in required)

def metric_gap(metric, target):
    return float(target) - float(metric)
