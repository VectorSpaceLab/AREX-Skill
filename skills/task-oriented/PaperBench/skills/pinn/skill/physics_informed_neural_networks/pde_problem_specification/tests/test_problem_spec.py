from problem_spec import build_burgers_problem, validate_problem


def test_builds_separated_burgers_item():
    item = build_burgers_problem(observation_count=4, collocation_count=5, nu=0.02)
    summary = validate_problem(item)
    assert summary["ok"] is True
    assert summary["observation_count"] == 4
    assert summary["collocation_count"] == 5
    assert item["coefficients"]["nu"] == 0.02
    assert all("u" in point for point in item["observations"])
    assert all("u" not in point for point in item["collocation_points"])
