import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'finite_mdp_policy_gradient' / 'scripts'))
from policy_gradient import demo_mdp, theorem_gradient, gradient_error
from compatible_critic import fit_compatible_critic

def test_compatible_critic_gradient_agrees():
    tr,r,g,st,feat,theta=demo_mdp()
    grad,ev,scores=theorem_gradient(theta,tr,r,g,st,feat)
    fit=fit_compatible_critic(ev['policy'], ev['q'], ev['occupancy'], scores)
    assert fit['orthogonality_norm'] < 1e-9
    assert gradient_error(grad, fit['critic_gradient']) < 1e-9


def test_state_baseline_does_not_change_compatible_gradient():
    tr,r,g,st,feat,theta=demo_mdp()
    grad,ev,scores=theorem_gradient(theta,tr,r,g,st,feat)
    shifted=[[ev['q'][s][a] + (2.0 if s == 0 else -1.0) for a in range(len(ev['q'][s]))] for s in range(len(ev['q']))]
    fit=fit_compatible_critic(ev['policy'], shifted, ev['occupancy'], scores)
    assert fit['orthogonality_norm'] < 1e-9
    assert gradient_error(grad, fit['critic_gradient']) < 1e-9
