from math import sqrt

def dot(a, b): return sum(x*y for x, y in zip(a, b))
def axpy(a, x, y): return [a*xi + yi for xi, yi in zip(x, y)]
def normalize(v):
    n = sqrt(max(dot(v, v), 0.0))
    if n <= 1e-12: raise ValueError('zero vector')
    return [x/n for x in v]

def lanczos_tridiagonal(hvp, initial, steps):
    q_prev = [0.0 for _ in initial]
    q = normalize(initial)
    alphas, betas = [], []
    beta_prev = 0.0
    for _ in range(steps):
        z = hvp(q)
        alpha = dot(q, z)
        z = [zi - alpha*qi - beta_prev*qpi for zi, qi, qpi in zip(z, q, q_prev)]
        beta = sqrt(max(dot(z, z), 0.0))
        alphas.append(alpha)
        if beta <= 1e-10: break
        betas.append(beta)
        q_prev, q = q, [zi/beta for zi in z]
        beta_prev = beta
    return {'alpha': alphas, 'beta': betas}

def two_by_two_density(tridiagonal):
    a = tridiagonal['alpha']
    b = tridiagonal['beta']
    if len(a) == 1:
        return {'eigenvalues': [a[0]], 'weights': [1.0]}
    off = b[0] if b else 0.0
    trace = a[0] + a[1]
    disc = sqrt((a[0]-a[1])**2 + 4*off*off)
    vals = [(trace-disc)/2.0, (trace+disc)/2.0]
    # normalized quadrature weights for first basis vector
    weights = []
    for lam in vals:
        if abs(off) <= 1e-12:
            weights.append(1.0 if abs(lam-a[0]) <= 1e-9 else 0.0)
        else:
            r = off / (lam - a[0]) if abs(lam-a[0]) > 1e-12 else 1e12
            weights.append(1.0/(1.0+r*r))
    s = sum(weights)
    return {'eigenvalues': vals, 'weights': [w/s for w in weights]}

def density_contract(density):
    return bool(density.get('eigenvalues')) and abs(sum(density.get('weights', [])) - 1.0) < 1e-6
