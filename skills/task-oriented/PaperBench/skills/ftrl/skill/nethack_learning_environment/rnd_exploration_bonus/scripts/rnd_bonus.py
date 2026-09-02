def dot(weights, features):
    return sum(weights.get(k, 0.0) * float(v) for k, v in features.items())

def novelty_loss(features, target, predictor):
    error = dot(target, features) - dot(predictor, features)
    return error * error

def update_predictor(features, target, predictor, lr=0.1):
    prediction = dot(predictor, features)
    target_value = dot(target, features)
    error = prediction - target_value
    updated = dict(predictor)
    for k, v in features.items():
        updated[k] = updated.get(k, 0.0) - lr * 2.0 * error * float(v)
    return updated

def intrinsic_reward(loss, scale=0.01):
    return float(loss) * scale

def combined_reward(extrinsic, intrinsic):
    return float(extrinsic) + float(intrinsic)
