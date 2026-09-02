from sac_update import run_sac_update

def test_update_changes_parameters_and_records_mechanism():
    batch={'transitions':[{'reward':1.0,'log_prob':-0.5,'done':False},{'reward':0.0,'log_prob':-0.2,'done':True}]}
    result=run_sac_update(batch)
    assert result['loss_before'] >= 0
    assert result['params_before'] != result['params_after']
    assert result['mechanism_checks']['twin_q_min_used'] is True
    assert result['mechanism_checks']['polyak_target_update_executed'] is True
