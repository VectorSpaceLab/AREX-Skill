from dpo_loss import dpo_example, dpo_batch

def test_loss_decreases_when_chosen_logratio_improves():
    low = dpo_example(-3.0, -1.0, -2.0, -2.0, beta=0.5)["loss"]
    high = dpo_example(-1.0, -3.0, -2.0, -2.0, beta=0.5)["loss"]
    assert high < low

def test_implicit_rewards_and_logits():
    out = dpo_example(-1.0, -4.0, -2.0, -3.0, beta=0.2)
    assert abs(out["chosen_reward"] - 0.2) < 1e-12
    assert abs(out["rejected_reward"] - (-0.2)) < 1e-12
    assert abs(out["logit"] - 2.0) < 1e-12

def test_reference_free_sets_reference_logratio_to_zero():
    out = dpo_example(-1, -2, 10, -10, beta=1, reference_free=True)
    assert out["reference_logratio"] == 0.0

def test_batch_mean_loss():
    out = dpo_batch([-1, -2], [-2, -1], [-1, -1], [-1, -1], beta=0.1)
    assert len(out["examples"]) == 2
    assert out["mean_loss"] > 0


def test_rejects_nonpositive_beta():
    try:
        dpo_example(-1, -2, -1, -1, beta=0)
        assert False, "expected beta failure"
    except ValueError as exc:
        assert "beta" in str(exc)
