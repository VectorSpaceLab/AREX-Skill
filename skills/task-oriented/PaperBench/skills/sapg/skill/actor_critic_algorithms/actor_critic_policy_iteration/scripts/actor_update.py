from __future__ import annotations

def apply_actor_update(theta, gradient, step_size):
    return [t + step_size*g for t,g in zip(theta, gradient)]

def improvement_record(theta_before, theta_after, objective_before, objective_after, gradient):
    return {'params_before':theta_before,'params_after':theta_after,'loss_before':-objective_before,'loss_after':-objective_after,'objective_before':objective_before,'objective_after':objective_after,'improvement':objective_after-objective_before,'gradient_norm':sum(g*g for g in gradient) ** 0.5,'optimizer_state_changed':theta_before != theta_after}
