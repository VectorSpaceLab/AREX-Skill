from vtrace import compute_vtrace

def test_on_policy_reduces_to_n_step_return():
    out=compute_vtrace([1.0,2.0],[0.9,0.9],[0.5,0.3,0.2],[1,1],[1,1],1,1)
    expected=1.0+0.9*2.0+0.9*0.9*0.2
    assert abs(out["targets"][0]-expected) < 1e-9

def test_off_policy_clips_ratio():
    out=compute_vtrace([1.0],[0.9],[0.0,0.0],[0.9],[0.1],rho_bar=1.0,c_bar=0.5)
    assert out["ratios"][0] == 9.0
    assert out["rhos"][0] == 1.0
    assert out["cs"][0] == 0.5

def test_extreme_policy_lag_remains_finite_and_clipped():
    out=compute_vtrace([1.0,0.0],[0.9,0.0],[0.0,0.2,0.0],[0.99,0.5],[0.01,0.5],rho_bar=1.0,c_bar=0.5)
    assert out["rhos"][0] == 1.0
    assert out["cs"][0] == 0.5
    assert all(abs(x) < 10 for x in out["targets"])

def test_three_step_on_policy_return():
    out=compute_vtrace([1.0,2.0,3.0],[0.5,0.5,0.0],[0.0,0.0,0.0,0.0],[1,1,1],[1,1,1],rho_bar=1.0,c_bar=1.0)
    assert abs(out["targets"][0] - (1.0 + 0.5*2.0 + 0.25*3.0)) < 1e-9
