from budget_schedule import schedule

def test_schedule_phases_and_monotonicity():
    vals=[schedule(s,10,2,2,8,4,2)['rank'] for s in range(1,10)]
    assert vals[0]==8 and vals[-1]==4
    assert all(vals[i] >= vals[i+1] for i in range(len(vals)-1))

def test_mask_interval():
    assert schedule(3,10,2,2,8,4,2)['mask'] is False
    assert schedule(4,10,2,2,8,4,2)['mask'] is True

def test_invalid_total_steps_blocked():
    try:
        schedule(1,4,2,2,8,4,1)
        assert False
    except ValueError as exc:
        assert 'total_step' in str(exc)
