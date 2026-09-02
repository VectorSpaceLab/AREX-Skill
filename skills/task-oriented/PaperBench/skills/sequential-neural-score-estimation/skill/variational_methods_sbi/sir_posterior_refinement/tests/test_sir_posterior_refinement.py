from sir import sir_resample

def test_high_weight_particle_dominates():
    out=sir_resample([0,1,2],[-5,0,-2],[0,0,0],[0,0,0],n=20,seed=1)
    assert abs(sum(out["weights"])-1.0)<1e-12
    assert out["samples"].count(1)>out["samples"].count(0)


def test_equal_weights_remain_normalized():
    out=sir_resample([0,1], [0,0], [0,0], [0,0], n=4, seed=2)
    assert abs(sum(out['weights'])-1.0)<1e-12
    assert all(abs(w-0.5)<1e-12 for w in out['weights'])
