from proxy_recovery import tiny_update, mechanism_summary

def test_tiny_update_changes_params_and_reduces_loss():
    trace=tiny_update(0.0, 2.0, 1.0)
    assert trace['params_before'] != trace['params_after']
    assert trace['loss_after'] < trace['loss_before']

def test_mechanism_summary_marks_reduced_not_full_training():
    trace=tiny_update(0.0, 1.0, 1.0)
    checks=mechanism_summary(75, 25, trace)
    assert checks['reduced_training_executed'] is True
    assert checks['training_step_executed'] is False
