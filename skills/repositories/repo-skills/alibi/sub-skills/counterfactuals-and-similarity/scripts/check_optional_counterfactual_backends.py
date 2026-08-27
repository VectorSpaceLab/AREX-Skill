#!/usr/bin/env python3
"""Check whether Alibi's counterfactual and similarity exports are placeholders.

This helper is diagnostic-only and never imports TensorFlow or Torch directly.
"""
from __future__ import annotations

import argparse
import importlib
import sys

from alibi.utils.missing_optional_dependency import MissingDependency


EXPORTS = [
    ('alibi.explainers', 'Counterfactual', 'alibi[tensorflow]'),
    ('alibi.explainers', 'CEM', 'alibi[tensorflow]'),
    ('alibi.explainers', 'CounterfactualProto', 'alibi[tensorflow]'),
    ('alibi.explainers', 'CounterfactualRL', 'alibi[tensorflow] or alibi[torch]'),
    ('alibi.explainers', 'CounterfactualRLTabular', 'alibi[tensorflow] or alibi[torch]'),
    ('alibi.explainers', 'GradientSimilarity', 'alibi[tensorflow] or alibi[torch]'),
]


def _status(module_name: str, attr: str) -> str:
    module = importlib.import_module(module_name)
    obj = getattr(module, attr)
    return 'missing' if isinstance(obj, MissingDependency) else 'present'


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--strict', action='store_true', help='return non-zero when any export is missing')
    args = parser.parse_args()

    missing = 0
    print('Alibi counterfactual / similarity backend status')
    for module_name, attr, extra in EXPORTS:
        try:
            status = _status(module_name, attr)
        except Exception as exc:  # pragma: no cover - diagnostic helper
            status = 'error:%s' % exc.__class__.__name__
        if status != 'present':
            missing += 1
        print('%-28s %-10s %s' % (attr, status, extra))

    print('missing optional exports: %d' % missing)
    if args.strict and missing:
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
