#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter


def main() -> int:
    parser = argparse.ArgumentParser(description='Summarize the Upsonic model registry without making model calls.')
    parser.add_argument('--limit', type=int, default=20, help='Maximum number of model ids to print.')
    parser.add_argument('--prefix', default=None, help='Only show model ids that start with this prefix.')
    args = parser.parse_args()

    from upsonic.models.model_registry import MODEL_REGISTRY

    names = sorted(MODEL_REGISTRY)
    if args.prefix:
        names = [name for name in names if name.startswith(args.prefix)]

    prefixes = Counter(name.split('/', 1)[0] for name in names)
    print(f'model_count: {len(names)}')
    print('provider_prefixes:')
    for provider, count in prefixes.most_common():
        print(f'  {provider}: {count}')
    print('sample_models:')
    for name in names[: args.limit]:
        meta = MODEL_REGISTRY[name]
        provider = getattr(meta, 'provider', None) or name.split('/', 1)[0]
        print(f'  - {name} (provider={provider})')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
