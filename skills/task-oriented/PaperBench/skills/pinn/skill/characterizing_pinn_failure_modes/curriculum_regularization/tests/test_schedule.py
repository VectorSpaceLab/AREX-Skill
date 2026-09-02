from schedule import make_schedule, validate_schedule


def test_schedule_monotone_and_endpoint():
    sched = make_schedule(1.0, 30.0, 5)
    validation = validate_schedule(sched, 1.0, 30.0)
    assert len(sched) == 5
    assert validation["monotone"] is True
    assert validation["ends_at_target"] is True
    assert sched[0]["beta"] == 1.0
    assert sched[-1]["beta"] == 30.0
