import math


def clipped_loss(param, old_log_probs, advantages, clip_epsilon=0.2):
    values = []
    for old, adv in zip(old_log_probs, advantages):
        ratio = math.exp((old + param) - old)
        clipped = max(1.0 - clip_epsilon, min(1.0 + clip_epsilon, ratio))
        values.append(min(ratio * adv, clipped * adv))
    return -sum(values) / len(values)


def ppo_scalar_update(param, old_log_probs, advantages, clip_epsilon=0.2, learning_rate=0.05):
    before = clipped_loss(param, old_log_probs, advantages, clip_epsilon)
    eps = 1e-5
    grad = (clipped_loss(param + eps, old_log_probs, advantages, clip_epsilon) - clipped_loss(param - eps, old_log_probs, advantages, clip_epsilon)) / (2 * eps)
    after_param = param - learning_rate * grad
    after = clipped_loss(after_param, old_log_probs, advantages, clip_epsilon)
    return {'loss_before': before, 'loss_after': after, 'params_before': {'policy_shift': param}, 'params_after': {'policy_shift': after_param}, 'gradient': grad, 'optimizer_state_changed': after_param != param}
