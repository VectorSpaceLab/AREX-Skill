from reprogramming_evaluation import evaluate_reprogramming_evidence

def test_accepts_complete_proxy_evidence():
    checks={'universal_program_reused':True,'frozen_model_unchanged':True,'output_remapping_used':True,'optimizer_step_executed':True,'reduced_training_executed':True}
    r=evaluate_reprogramming_evidence({'metrics':{'accuracy':1.0},'mechanism_checks':checks},{'loss_before':1,'loss_after':0.5,'params_before':{'p':0},'params_after':{'p':1}},[])
    assert r['ok'] is True
