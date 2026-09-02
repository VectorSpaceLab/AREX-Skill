from policy_gradient import demo_mdp, theorem_gradient, finite_difference_gradient, gradient_error

def test_theorem_matches_finite_difference():
    tr,r,g,st,feat,theta=demo_mdp()
    analytic,_,_=theorem_gradient(theta,tr,r,g,st,feat)
    numeric=finite_difference_gradient(theta,tr,r,g,st,feat)
    assert gradient_error(analytic,numeric) < 1e-5


def test_theorem_stress_second_theta():
    tr,r,g,st,feat,theta=demo_mdp()
    theta=[-0.7,0.35]
    analytic,_,_=theorem_gradient(theta,tr,r,g,st,feat)
    numeric=finite_difference_gradient(theta,tr,r,g,st,feat)
    assert gradient_error(analytic,numeric) < 1e-5
