#!/usr/bin/env python3
"""Check whether Alibi's attribution exports are real classes or placeholders.

This helper is diagnostic-only and never imports heavy SHAP or TensorFlow backends.
"""
from __future__ import annotations

import argparse
import importlib
import sys

from alibi.utils.missing_optional_dependency import MissingDependency


EXPORTS = [
    ('alibi.explainers', 'KernelShap', 'alibi[shap]'),
    ('alibi.explainers', 'TreeShap', 'alibi[shap]'),
    ('alibi.explainers', 'IntegratedGradients', 'alibi[tensorflow]'),
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
    print('Alibi attribution backend status')
    for module_name, attr, extra in EXPORTS:
        try:
            status = _status(module_name, attr)
        except Exception as exc:  # pragma: no cover - diagnostic helper
            status = 'error:%s' % exc.__class__.__name__
        if status != 'present':
            missing += 1
        print('%-24s %-10s %s' % (attr, status, extra))

    print('missing optional exports: %d' % missing)
    if args.strict and missing:
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
