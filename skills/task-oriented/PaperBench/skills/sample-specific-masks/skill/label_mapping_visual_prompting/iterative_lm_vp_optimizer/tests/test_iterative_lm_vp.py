from ilm_vp import synthetic_problem, run_ilm_vp

def test_optimizer_updates_prompt_and_logs_mapping():
    xs,ys,w,b=synthetic_problem()
    out=run_ilm_vp(xs,ys,w,b,epochs=5)
    assert out['mechanism_checks']['optimizer_step_executed']
    assert len(out['mapping_history']) == 5
    assert out['loss_after'] <= out['loss_before'] + 1e-9
