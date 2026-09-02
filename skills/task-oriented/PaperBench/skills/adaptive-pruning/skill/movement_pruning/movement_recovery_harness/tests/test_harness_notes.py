from harness_notes import expected_mechanism_checks

def test_checks():
    checks=expected_mechanism_checks()
    assert 'movement_scores_updated' in checks and 'optimizer_step_executed' in checks
