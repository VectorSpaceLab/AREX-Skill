from sequential_loop import run_rounds

def test_loop_accumulates_and_moves():
    out=run_rounds(rounds=2,sims_per_round=4,observation=2.0)
    assert len(out["data"])==8
    assert out["proposal"]["mean"]>0.0
    assert out["logs"][1]["proposal_mean_after"]>out["logs"][0]["proposal_mean_after"]
