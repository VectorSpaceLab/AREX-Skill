import importlib.util
from pathlib import Path
spec=importlib.util.spec_from_file_location('cfm', Path(__file__).resolve().parents[1]/'scripts'/'cfm_train.py'); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
def test_loss_zero_for_exact_constant_predictor():
    params=[[2]+[0]*5,[-1]+[0]*5]; assert m.mse_loss(params,[0,.5],[[1],[2]],[[2,-1],[2,-1]])==0.0
def test_training_decreases_loss_and_changes_params():
    tr=m.train_linear_cfm([0,.25,.5,.75],[[0,0],[.2,.3],[.4,-.2],[.8,.1]],[[1,-1],[.8,-.5],[.2,.1],[-.3,.6]],80,.05); assert tr['optimizer_step_executed'] and tr['params_before']!=tr['params_after'] and tr['loss_after']<tr['loss_before']
def test_gradient_has_expected_shape():
    grad=m.gradient([[0]*6,[0]*6],[.5],[[1]],[[1,2]]); assert len(grad)==2 and all(len(r)==6 for r in grad)
