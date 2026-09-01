import math

def true_noise(target, timestep):
    return math.sin(float(target) + float(timestep))

def predict_noise(pair, noisy, timestep, weight):
    return float(weight) * (float(noisy) - float(pair['condition']) + 0.1 * float(timestep))

def loss(pair, timestep, beta, weight):
    noise = true_noise(pair['target'], timestep)
    noisy = ((1.0 - beta) ** 0.5) * pair['target'] + (beta ** 0.5) * noise
    pred = predict_noise(pair, noisy, timestep, weight)
    return {'noisy': noisy, 'true_noise': noise, 'predicted_noise': pred, 'loss': (pred - noise) ** 2}

def optimizer_step(pair, timestep=0.6, beta=0.25, weight=0.1, lr=0.5):
    before = loss(pair, timestep, beta, weight)
    feature = before['noisy'] - pair['condition'] + 0.1 * timestep
    grad = 2.0 * (before['predicted_noise'] - before['true_noise']) * feature
    new_weight = weight - lr * grad
    after = loss(pair, timestep, beta, new_weight)
    return {'params_before': {'weight': weight}, 'params_after': {'weight': new_weight}, 'loss_before': before['loss'], 'loss_after': after['loss'], 'noisy': before['noisy'], 'true_noise': before['true_noise']}
