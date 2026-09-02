from ddpm_utils import linear_beta_schedule

def test_single_step_schedule_uses_beta_end():
    assert linear_beta_schedule(0.1, 0.2, 1) == [0.2]

def test_invalid_beta_range_raises():
    try:
        linear_beta_schedule(0.2, 0.1, 2)
    except ValueError:
        return
    raise AssertionError('invalid schedule should raise')
