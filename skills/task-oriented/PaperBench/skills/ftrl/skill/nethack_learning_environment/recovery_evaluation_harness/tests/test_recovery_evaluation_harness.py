from recovery_checks import target_matches, source_boundary_ok, proxy_mechanism_ok, metric_gap

def test_recovery_checks():
    target = {'dataset':'x','metric':'m','paper_value':1.0}
    assert target_matches(target, dict(target))
    assert source_boundary_ok(['paper_profile.md'], '/repo')
    assert proxy_mechanism_ok({'symbolic_observation_parsed':True,'action_protocol_exercised':True,'rnd_bonus_computed':True,'reduced_training_executed':True,'optimizer_step_executed':True,'evaluation_metric_computed':True})
    assert metric_gap(0.75, 1.0) == 0.25


def test_source_boundary_detects_original_repo_fragment():
    from recovery_checks import source_boundary_ok
    assert not source_boundary_ok(['/tmp/original/repo/nle/env/tasks.py'], '/repo')
