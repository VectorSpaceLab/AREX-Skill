from recovery_evaluation import score_recovery

def test_score_recovery_pass_and_fail():
    checks={key: True for key in ['entropy_term_used','replay_batch_used','twin_q_min_used','value_update_executed','q_update_executed','policy_update_executed','polyak_target_update_executed','optimizer_step_executed','reduced_training_executed']}
    trace={'loss_before':1.0,'loss_after':0.9,'params_before':{'a':1},'params_after':{'a':2}}
    ok=score_recovery(checks, trace, [1,2,3,4], [])
    assert ok['ok'] is True
    bad=score_recovery({}, trace, [], ['repo'])
    assert bad['ok'] is False
    assert 'source_boundary_ok' in bad['failed_checks']
