from stein_kernel_loss import dksd_u_statistic, stein_kernel


def test_stein_kernel_is_symmetric_and_finite():
    x = -0.5
    y = 1.25
    forward = stein_kernel(0.0, x, y)
    reverse = stein_kernel(0.0, y, x)
    assert abs(forward - reverse) < 1e-10
    assert abs(forward) < 100.0


def test_dksd_loss_is_finite_and_uses_pairs():
    samples = [-1.0, -0.25, 0.2, 1.0, 2.5]
    result = dksd_u_statistic(samples, theta=0.1)
    assert result["finite"] is True
    assert result["pair_count"] == 20
    assert result["score_only"] is True


def test_loss_changes_with_theta_on_student_t_sample():
    samples = [-0.1, 0.6, 1.1, 1.4, 1.9, 2.7]
    near = dksd_u_statistic(samples, theta=1.2)["loss"]
    far = dksd_u_statistic(samples, theta=-2.5)["loss"]
    assert near < far
