def mse(values, targets):
    return sum((v-t)**2 for v,t in zip(values, targets)) / len(values)

def train_projection_step(visual, target, params=None, lr=0.1, steps=1):
    if len(visual) != len(target):
        raise ValueError("visual and target lengths must match")
    if params is None:
        params = [0.0 for _ in visual]
    params = [float(p) for p in params]
    before = list(params)
    def project(ps):
        return [p*x for p,x in zip(ps, visual)]
    loss_before = mse(project(params), target)
    for _ in range(steps):
        preds = project(params)
        grads = [2.0 * (pred-target_i) * x / len(visual) for pred, target_i, x in zip(preds, target, visual)]
        params = [p - lr*g for p,g in zip(params, grads)]
    loss_after = mse(project(params), target)
    return {"loss_before": loss_before, "loss_after": loss_after, "params_before": before, "params_after": params, "optimizer_state_changed": before != params}
