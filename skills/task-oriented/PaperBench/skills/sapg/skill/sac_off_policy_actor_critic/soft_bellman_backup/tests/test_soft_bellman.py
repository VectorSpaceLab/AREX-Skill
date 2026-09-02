from soft_bellman import soft_values, q_targets, backup_report

def test_soft_values_subtract_log_prob():
    assert soft_values([1.0], [-0.5], alpha=0.2) == [1.1]

def test_terminal_target_does_not_bootstrap():
    assert q_targets([2.0, 1.0], [True, False], [99.0, 3.0], gamma=0.5) == [2.0, 2.5]

def test_backup_report_has_loss():
    out=backup_report([0.0], [-1.0], [1.0], [False], [2.0], gamma=0.5, alpha=1.0)
    assert out['q_loss'] > 0.0


def test_all_terminal_targets_equal_rewards():
    assert q_targets([1.0, -1.0], [True, True], [100.0, 100.0], gamma=0.99) == [1.0, -1.0]
