from predictor_corrector_sampling import run_pc

def test_pc_moves_toward_zero():
    out = run_pc(2.0, [1.0, 0.5, 0.1], corrector_step=0.2)
    assert abs(out["final"]) < 2.0

def test_pc_logs_both_phases():
    out = run_pc(1.0, [1.0, 0.6, 0.2])
    phases = [item["phase"] for item in out["trajectory"]]
    assert "predictor" in phases
    assert "corrector" in phases
