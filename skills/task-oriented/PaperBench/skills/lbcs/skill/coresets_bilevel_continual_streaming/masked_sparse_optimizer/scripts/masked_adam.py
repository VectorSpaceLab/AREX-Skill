from __future__ import annotations

import copy
import json
import math


def masked_adam_step(weights, gradients, state=None, lr=0.1, beta1=0.9, beta2=0.999, eps=1e-8):
    state = copy.deepcopy(state or {'m': {}, 'v': {}, 't': {}})
    updated = dict(weights)
    diagnostics = []
    for item_id, grad in gradients.items():
        grad = float(grad)
        t = int(state['t'].get(item_id, 0)) + 1
        m = beta1 * float(state['m'].get(item_id, 0.0)) + (1.0 - beta1) * grad
        v = beta2 * float(state['v'].get(item_id, 0.0)) + (1.0 - beta2) * grad * grad
        m_hat = m / (1.0 - beta1 ** t)
        v_hat = v / (1.0 - beta2 ** t)
        before = float(updated[item_id])
        after = max(0.0, before - lr * m_hat / (math.sqrt(v_hat) + eps))
        updated[item_id] = after
        state['m'][item_id] = m
        state['v'][item_id] = v
        state['t'][item_id] = t
        diagnostics.append({'id': item_id, 'before': before, 'after': after, 'grad': grad, 't': t})
    return updated, state, diagnostics


if __name__ == '__main__':
    weights, state, diagnostics = masked_adam_step({'u0': 0.5, 'u1': 0.5}, {'u0': 1.0})
    print(json.dumps({'weights': weights, 'state': state, 'diagnostics': diagnostics}, indent=2))
