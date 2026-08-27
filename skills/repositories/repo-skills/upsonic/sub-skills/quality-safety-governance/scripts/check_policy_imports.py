#!/usr/bin/env python3
from __future__ import annotations

import importlib.util

MODULES = [
    'upsonic.safety_engine',
    'upsonic.reflection.models',
    'upsonic.reflection.processor',
    'upsonic.reliability_layer.reliability_layer',
    'upsonic.integrations.tracing',
    'upsonic.integrations.promptlayer',
]


def main() -> int:
    for module in MODULES:
        print(f'{module}: {importlib.util.find_spec(module) is not None}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
