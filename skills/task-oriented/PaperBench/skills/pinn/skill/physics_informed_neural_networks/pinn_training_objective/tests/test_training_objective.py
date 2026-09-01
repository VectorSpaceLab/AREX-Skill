import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, os.path.join(ROOT, "pde_problem_specification", "scripts"))
sys.path.insert(0, os.path.join(ROOT, "autodiff_pde_residual", "scripts"))

from problem_spec import build_burgers_problem
from pinn_objective import train_steps


def test_train_steps_changes_params_and_logs_losses():
    problem = build_burgers_problem(observation_count=4, collocation_count=5)
    params = {"bias": 0.2, "t_weight": 0.0, "x_weight": 0.0, "tx_weight": 0.0, "xx_weight": 0.0}
    trace = train_steps(problem, params, learning_rate=0.01, steps=1)
    assert trace["params_before"] != trace["params_after"]
    assert isinstance(trace["loss_before"], float)
    assert isinstance(trace["loss_after"], float)
    assert trace["optimizer_state_changed"] is True
