from __future__ import annotations

import json


def influence_hypergradients(validation_gradient, unsupervised_gradients, hessian_diag, damping=1e-3):
    inv = [1.0 / (float(v) + damping) for v in hessian_diag]
    result = []
    for grad in unsupervised_gradients:
        score = -sum(float(vg) * inv_i * float(ug) for vg, inv_i, ug in zip(validation_gradient, inv, grad))
        result.append(score)
    return result


def update_weights(weights, selected_ids, hypergradients, lr=0.1):
    updated = dict(weights)
    diagnostics = []
    for item_id, grad in zip(selected_ids, hypergradients):
        before = float(updated[item_id])
        after = max(0.0, before - lr * float(grad))
        updated[item_id] = after
        diagnostics.append({'id': item_id, 'gradient': float(grad), 'before': before, 'after': after, 'delta': after - before})
    return updated, diagnostics


if __name__ == '__main__':
    validation_gradient = [0.5, -0.25]
    unsupervised_gradients = [[-1.0, 0.0], [1.0, 0.5]]
    weights = {'u0': 0.5, 'u1': 0.5}
    hyper = influence_hypergradients(validation_gradient, unsupervised_gradients, [1.0, 1.0])
    updated, diagnostics = update_weights(weights, ['u0', 'u1'], hyper)
    print(json.dumps({'hypergradients': hyper, 'weights': updated, 'diagnostics': diagnostics}, indent=2))
