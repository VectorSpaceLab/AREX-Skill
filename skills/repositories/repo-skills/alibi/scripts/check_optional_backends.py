#!/usr/bin/env python3
"""Report which Alibi optional exports are placeholders and which extras enable them.

This helper is diagnostic-only. It does not import heavy optional backends.
Use --strict to return a non-zero exit code if any requested export is missing.
"""
from __future__ import annotations

import argparse
import importlib
import sys

try:
    import alibi
    from alibi.utils.missing_optional_dependency import MissingDependency
except Exception as exc:  # pragma: no cover - import guard
    print(f'failed to import alibi for optional-backend inspection: {exc}', file=sys.stderr)
    raise SystemExit(2)


OPTIONAL_EXPORTS = [
    ('alibi.explainers', 'DistributedAnchorTabular', 'alibi[ray]', 'distributed anchor tabular'),
    ('alibi.explainers', 'CEM', 'alibi[tensorflow]', 'contrastive explanation method'),
    ('alibi.explainers', 'Counterfactual', 'alibi[tensorflow]', 'basic counterfactual search'),
    ('alibi.explainers', 'CounterfactualProto', 'alibi[tensorflow]', 'prototype-guided counterfactuals'),
    ('alibi.explainers', 'CounterfactualRL', 'alibi[tensorflow] or alibi[torch]', 'counterfactual RL backend'),
    ('alibi.explainers', 'CounterfactualRLTabular', 'alibi[tensorflow] or alibi[torch]', 'tabular counterfactual RL backend'),
    ('alibi.explainers', 'IntegratedGradients', 'alibi[tensorflow]', 'gradient attribution'),
    ('alibi.explainers', 'KernelShap', 'alibi[shap]', 'Kernel SHAP wrapper'),
    ('alibi.explainers', 'TreeShap', 'alibi[shap]', 'Tree SHAP wrapper'),
    ('alibi.explainers', 'GradientSimilarity', 'alibi[tensorflow] or alibi[torch]', 'gradient similarity backend'),
    ('alibi.utils', 'DistributedExplainer', 'alibi[ray]', 'distributed utility helpers'),
    ('alibi.utils', 'LanguageModel', 'alibi[tensorflow]', 'AnchorText language-model sampling'),
    ('alibi.utils', 'DistilbertBaseUncased', 'alibi[tensorflow]', 'language model helper'),
    ('alibi.utils', 'BertBaseUncased', 'alibi[tensorflow]', 'language model helper'),
    ('alibi.utils', 'RobertaBase', 'alibi[tensorflow]', 'language model helper'),
    ('alibi.datasets', 'fetch_fashion_mnist', 'alibi[tensorflow]', 'TensorFlow dataset helper'),
]


def _status(module_name: str, attr: str) -> str:
    module = importlib.import_module(module_name)
    obj = getattr(module, attr)
    return 'missing' if isinstance(obj, MissingDependency) else 'present'


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--strict', action='store_true', help='return non-zero when any optional export is missing')
    args = parser.parse_args()

    missing = 0
    print('alibi %s optional-backend status' % getattr(alibi, '__version__', 'unknown'))
    for module_name, attr, extra, note in OPTIONAL_EXPORTS:
        try:
            status = _status(module_name, attr)
        except Exception as exc:  # pragma: no cover - diagnostic helper
            status = 'error:%s' % exc.__class__.__name__
        if status != 'present':
            missing += 1
        print('%-28s %-12s %-28s %s' % (attr, status, extra, note))

    print('missing optional exports: %d' % missing)
    if args.strict and missing:
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
