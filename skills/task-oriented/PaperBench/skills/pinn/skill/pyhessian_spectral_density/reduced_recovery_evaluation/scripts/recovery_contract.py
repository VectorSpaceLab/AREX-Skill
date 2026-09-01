def mechanism_score(checks):
    required = ['hvp_executed','power_iteration_executed','hutchinson_trace_executed','slq_density_executed','architecture_comparison_executed','optimizer_step_executed']
    return sum(1 for key in required if checks.get(key) is True) / float(len(required))

def build_result(paper_id, target, metrics, checks, command):
    return {'schema_version': 1, 'paper_id': paper_id, 'experiment': target['dataset'], 'is_proxy': bool(target.get('proxy')), 'sample_count': 3, 'metrics': metrics, 'paper_target': target, 'commands': [command], 'mechanism_checks': checks, 'notes': 'Reduced soft-mode recovery with executable analytic curvature proxy.'}

def source_boundary_ok(sources, forbidden_fragments):
    joined = '\n'.join(str(s) for s in sources)
    return not any(fragment and fragment in joined for fragment in forbidden_fragments)
