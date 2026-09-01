
from __future__ import annotations

def warmup_target(step, warmup_steps, final_target):
    if warmup_steps <= 0:
        return float(final_target)
    ratio=max(0.0, min(1.0, float(step)/float(warmup_steps)))
    return float(final_target)*ratio

def lagrangian_penalty(expected_sparsity, target_sparsity, lambda_1=1.0, lambda_2=0.0):
    gap=float(expected_sparsity)-float(target_sparsity)
    return float(lambda_1)*gap + float(lambda_2)*gap*gap

def update_lambda(lambda_1, expected_sparsity, target_sparsity, lr=0.1):
    return float(lambda_1) + float(lr)*(float(expected_sparsity)-float(target_sparsity))

def expected_sparsity(active_parameters, total_parameters):
    if total_parameters <= 0:
        raise ValueError('total_parameters must be positive')
    return 1.0 - float(active_parameters)/float(total_parameters)
