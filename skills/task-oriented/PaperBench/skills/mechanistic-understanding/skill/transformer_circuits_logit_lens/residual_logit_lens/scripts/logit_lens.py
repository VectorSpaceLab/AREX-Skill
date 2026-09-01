#!/usr/bin/env python3
"""Tiny logit-lens utilities using only the Python standard library."""
from __future__ import annotations
import argparse, json
from pathlib import Path


def matmul(a, b):
    if not a or not b or len(a[0]) != len(b):
        raise ValueError('incompatible matrix shapes')
    return [[sum(row[k] * b[k][j] for k in range(len(b))) for j in range(len(b[0]))] for row in a]


def add_mats(mats):
    first = mats[0]
    return [[sum(m[i][j] for m in mats) for j in range(len(first[0]))] for i in range(len(first))]


def max_abs_diff(a, b):
    return max(abs(a[i][j] - b[i][j]) for i in range(len(a)) for j in range(len(a[0]))) if a else 0.0


def analyze(residual, unembedding, components=None):
    logits = matmul(residual, unembedding)
    out = {'logits': logits, 'component_logits': {}, 'max_reconstruction_error': None}
    if components:
        comp_logits = {name: matmul(value, unembedding) for name, value in components.items()}
        summed = add_mats(list(comp_logits.values()))
        out['component_logits'] = comp_logits
        out['summed_component_logits'] = summed
        out['max_reconstruction_error'] = max_abs_diff(logits, summed)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--input', required=True)
    ap.add_argument('--output', required=True)
    args = ap.parse_args()
    data = json.loads(Path(args.input).read_text())
    result = analyze(data['residual'], data['unembedding'], data.get('components'))
    Path(args.output).write_text(json.dumps(result, indent=2) + '\n')

if __name__ == '__main__':
    main()
