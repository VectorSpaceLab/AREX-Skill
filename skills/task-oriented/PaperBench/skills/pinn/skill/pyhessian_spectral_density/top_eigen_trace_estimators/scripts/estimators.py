from math import sqrt

def dot(a, b): return sum(x*y for x, y in zip(a, b))
def normalize(v):
    n = sqrt(max(dot(v, v), 0.0))
    if n <= 1e-12: raise ValueError('zero vector')
    return [x/n for x in v]

def power_iteration(hvp, dim, max_iter=50, tol=1e-9, initial=None):
    v = normalize(initial or [1.0 for _ in range(dim)])
    eig = None
    history = []
    for _ in range(max_iter):
        hv = hvp(v)
        new_eig = dot(v, hv)
        history.append(new_eig)
        v = normalize(hv)
        if eig is not None and abs(new_eig - eig) / (abs(eig) + 1e-12) < tol:
            eig = new_eig
            break
        eig = new_eig
    return {'eigenvalue': eig, 'eigenvector': v, 'history': history}

def hutchinson_trace(hvp, dim, probes=None):
    probes = probes or [[1.0 if (i+j) % 2 == 0 else -1.0 for i in range(dim)] for j in range(dim)]
    vals = [dot(v, hvp(v)) for v in probes]
    return {'trace_estimate': sum(vals)/len(vals), 'probe_values': vals}

def estimator_contract():
    return {'requires_hvp': True, 'outputs_numeric_trace': True, 'outputs_top_eigenvalue': True}
