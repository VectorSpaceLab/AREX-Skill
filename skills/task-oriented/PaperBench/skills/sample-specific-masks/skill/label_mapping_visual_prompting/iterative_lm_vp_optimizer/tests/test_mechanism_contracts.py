from ilm_vp import synthetic_problem, run_ilm_vp

def test_mechanism_contract_source_frozen_and_remapping_flag():
    xs,ys,w,b=synthetic_problem()
    out=run_ilm_vp(xs,ys,w,b,epochs=3,iterative=True)
    assert out['mechanism_checks']['source_model_frozen'] is True
    assert out['mechanism_checks']['label_mapping_recomputed'] is True
    assert out['mechanism_checks']['optimizer_step_executed'] is True
