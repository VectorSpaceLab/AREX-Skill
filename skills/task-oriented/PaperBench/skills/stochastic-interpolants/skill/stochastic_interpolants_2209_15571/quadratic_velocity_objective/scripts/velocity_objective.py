import math

def gaussian_translation_velocity(x, t, shift):
    denom = math.cos(0.5 * math.pi * t) + math.sin(0.5 * math.pi * t)
    return 0.5 * math.pi * shift * math.cos(0.5 * math.pi * t) / denom

def linear_velocity(params, x, t):
    return params[0] + params[1] * x + params[2] * t

def objective_and_gradient(params, xs, ts, dts):
    n = float(len(xs))
    loss = 0.0
    grad = [0.0, 0.0, 0.0]
    for x,t,dt in zip(xs,ts,dts):
        features = [1.0, x, t]
        pred = sum(p*f for p,f in zip(params, features))
        loss += pred*pred - 2.0*dt*pred
        for i,f in enumerate(features):
            grad[i] += (2.0*pred - 2.0*dt) * f
    return loss/n, [g/n for g in grad]

def gradient_step(params, xs, ts, dts, lr=0.05):
    loss, grad = objective_and_gradient(params, xs, ts, dts)
    return [p - lr*g for p,g in zip(params, grad)], loss, grad
