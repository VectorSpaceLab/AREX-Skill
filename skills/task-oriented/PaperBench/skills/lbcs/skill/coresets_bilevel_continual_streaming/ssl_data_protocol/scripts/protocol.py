from __future__ import annotations

import json
import math
from typing import Iterable


def _label_from_score(features, params):
    score = sum(float(a) * float(b) for a, b in zip(features, params))
    return 1 if score >= 0 else 0


def build_protocol(labeled, validation, unlabeled, params=None, initial_weight=1.0):
    if not labeled or not validation or not unlabeled:
        raise ValueError('labeled, validation, and unlabeled splits must be non-empty')
    if initial_weight < 0 or not math.isfinite(initial_weight):
        raise ValueError('initial_weight must be finite and non-negative')
    params = params or [1.0 for _ in unlabeled[0]['x']]
    seen = set()
    normalized_unlabeled = []
    for item in unlabeled:
        item_id = str(item['id'])
        if item_id in seen:
            raise ValueError(f'duplicate unlabeled id: {item_id}')
        seen.add(item_id)
        normalized_unlabeled.append({
            'id': item_id,
            'x': [float(v) for v in item['x']],
            'pseudo_label': int(item.get('pseudo_label', _label_from_score(item['x'], params))),
            'weight': float(initial_weight),
        })
    return {
        'labeled': [{'x': [float(v) for v in item['x']], 'y': int(item['y'])} for item in labeled],
        'validation': [{'x': [float(v) for v in item['x']], 'y': int(item['y'])} for item in validation],
        'unlabeled': normalized_unlabeled,
        'weight_state': {item['id']: item['weight'] for item in normalized_unlabeled},
    }


def deterministic_toy_protocol():
    labeled = [{'x': [-2.0, -1.0], 'y': 0}, {'x': [-1.0, -1.5], 'y': 0}, {'x': [1.2, 1.0], 'y': 1}, {'x': [2.0, 1.4], 'y': 1}]
    validation = [{'x': [-1.7, -0.8], 'y': 0}, {'x': [-0.8, -1.2], 'y': 0}, {'x': [1.1, 0.9], 'y': 1}, {'x': [1.8, 1.1], 'y': 1}]
    unlabeled = [{'id': f'u{i}', 'x': x} for i, x in enumerate([[-2.2, -0.7], [-1.2, -1.0], [-0.2, 1.5], [0.3, -1.7], [1.0, 1.3], [2.2, 0.9], [0.5, 0.6], [-0.7, -0.4]])]
    return build_protocol(labeled, validation, unlabeled, params=[1.0, 1.0], initial_weight=0.5)


if __name__ == '__main__':
    print(json.dumps(deterministic_toy_protocol(), indent=2))
