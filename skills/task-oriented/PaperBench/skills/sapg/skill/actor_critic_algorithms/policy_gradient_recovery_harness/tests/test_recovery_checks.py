from recovery_checks import validate_result

def test_validate_result_accepts_mechanism():
    result={'metrics':{'max_gradient_error':1e-7,'objective_improvement':0.01},'mechanism_checks':{'policy_gradient_theorem_checked':True,'compatible_critic_orthogonality_checked':True,'optimizer_step_executed':True}}
    assert validate_result(result)
