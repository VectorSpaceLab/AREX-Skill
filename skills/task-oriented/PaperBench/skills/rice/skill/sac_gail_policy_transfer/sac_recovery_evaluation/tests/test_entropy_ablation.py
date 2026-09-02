from recovery_evaluation import score_recovery

def test_entropy_ablation_fails_mechanism_score():
    checks={key: True for key in ['replay_batch_used','twin_q_min_used','value_update_executed','q_update_executed','policy_update_executed','polyak_target_update_executed','optimizer_step_executed','reduced_training_executed']}
    checks['entropy_term_used'] = False
    trace={'loss_before':1.0,'loss_after':0.8,'params_before':{'a':1},'params_after':{'a':2}}
    result=score_recovery(checks, trace, [1,2,3,4], [])
    assert result['ok'] is False
    assert 'entropy_term_used' in result['failed_checks']
