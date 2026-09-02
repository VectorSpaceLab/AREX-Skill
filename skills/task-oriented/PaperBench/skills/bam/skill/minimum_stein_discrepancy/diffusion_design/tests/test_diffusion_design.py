from diffusion_design import evaluate_diffusion, make_diffusion


def test_student_t_diffusion_is_positive_and_larger_far_away():
    result = evaluate_diffusion([0.0, 1.0, 4.0], theta=1.0, kind="student_t_heavy_tail", nu=5.0)
    assert result["finite"] is True
    assert result["positive"] is True
    assert result["far_value"] > result["near_value"]


def test_robust_decay_gets_smaller_for_outlier():
    diffusion = make_diffusion("robust_decay", alpha=2.0)
    assert diffusion(0.0, 10.0) < diffusion(0.0, 0.5)
    assert diffusion(0.0, 10.0) > 0.0


def test_ordinary_diffusion_is_constant():
    result = evaluate_diffusion([-2.0, 0.0, 3.0], theta=0.0, kind="ordinary")
    assert result["min"] == 1.0
    assert result["max"] == 1.0
