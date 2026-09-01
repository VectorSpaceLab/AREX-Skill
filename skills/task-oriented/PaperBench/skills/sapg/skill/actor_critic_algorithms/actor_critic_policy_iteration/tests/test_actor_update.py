import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'finite_mdp_policy_gradient' / 'scripts'))
from policy_gradient import demo_mdp, theorem_gradient, build_policy, evaluate_mdp
from actor_update import apply_actor_update, improvement_record

def test_actor_update_improves_objective():
    tr,r,g,st,feat,theta=demo_mdp()
    grad,ev,_=theorem_gradient(theta,tr,r,g,st,feat)
    new_theta=apply_actor_update(theta, grad, 0.05)
    new_ev=evaluate_mdp(tr,r,g,st,build_policy(new_theta,feat))
    rec=improvement_record(theta,new_theta,ev['objective'],new_ev['objective'],grad)
    assert rec['improvement'] > 0
    assert rec['params_before'] != rec['params_after']


def test_negative_actor_step_reduces_objective():
    tr,r,g,st,feat,theta=demo_mdp()
    grad,ev,_=theorem_gradient(theta,tr,r,g,st,feat)
    new_theta=apply_actor_update(theta, grad, -0.05)
    new_ev=evaluate_mdp(tr,r,g,st,build_policy(new_theta,feat))
    rec=improvement_record(theta,new_theta,ev['objective'],new_ev['objective'],grad)
    assert rec['improvement'] < 0
