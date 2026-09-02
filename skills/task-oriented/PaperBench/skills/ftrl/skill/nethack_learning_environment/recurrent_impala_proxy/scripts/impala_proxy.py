import math

def policy_logit(params, features, hidden=0.0):
    return params.get('bias', 0.0) + params.get('distance_weight', 0.0) * features.get('distance_delta', 0.0) + 0.1 * hidden

def sigmoid(x):
    return 1.0 / (1.0 + math.exp(-max(-30.0, min(30.0, x))))

def loss(params, features, label):
    p = sigmoid(policy_logit(params, features))
    return -(label * math.log(p + 1e-9) + (1-label) * math.log(1-p + 1e-9))

def optimizer_step(params, features, label, lr=0.2):
    p = sigmoid(policy_logit(params, features))
    grad = p - label
    updated = dict(params)
    updated['bias'] = updated.get('bias', 0.0) - lr * grad
    updated['distance_weight'] = updated.get('distance_weight', 0.0) - lr * grad * features.get('distance_delta', 0.0)
    return updated

def train_one_step(params, features, label=1, lr=0.2):
    before = loss(params, features, label)
    updated = optimizer_step(params, features, label, lr)
    after = loss(updated, features, label)
    return {'loss_before': before, 'loss_after': after, 'params_before': params, 'params_after': updated}
