
import math

def gradient_norm(grads):
    return math.sqrt(sum(g*g for g in grads.values()))

def first_step(params, grads, rho=0.05):
    norm = gradient_norm(grads)
    scale = rho / (norm + 1e-12)
    return {k: params[k] + grads.get(k, 0.0) * scale for k in params}

def second_step(original_params, second_grads, lr=0.1):
    return {k: original_params[k] - lr * second_grads.get(k, 0.0) for k in original_params}

def sam_update(params, first_grads, second_grads, rho=0.05, lr=0.1):
    perturbed = first_step(params, first_grads, rho)
    updated = second_step(params, second_grads, lr)
    return {'params_before': dict(params), 'params_perturbed': perturbed, 'params_after': updated, 'perturbation_norm': gradient_norm({k: perturbed[k]-params[k] for k in params})}
