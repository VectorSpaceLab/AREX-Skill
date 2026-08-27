#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from typing import Any

BACKENDS = {
    'core': [
        ('Memory', 'upsonic.storage.memory.memory'),
        ('InMemoryStorage', 'upsonic.storage.memory.memory'),
        ('JSONStorage', 'upsonic.storage.json'),
    ],
    'optional': [
        ('SqliteStorage', 'upsonic.storage.sqlite.sqlite'),
        ('RedisStorage', 'upsonic.storage.redis.redis'),
        ('PostgresStorage', 'upsonic.storage.postgres.postgres'),
        ('MongoStorage', 'upsonic.storage.mongo.mongo'),
        ('Mem0Storage', 'upsonic.storage.mem0.mem0'),
    ],
}


def is_available(module_name: str) -> bool:
    return importlib.util.find_spec(module_name) is not None


def main() -> int:
    from upsonic.storage import InMemoryStorage, JSONStorage, Memory

    print('core_imports:')
    print(f'  Memory={Memory.__module__}.{Memory.__name__}')
    print(f'  InMemoryStorage={InMemoryStorage.__module__}.{InMemoryStorage.__name__}')
    print(f'  JSONStorage={JSONStorage.__module__}.{JSONStorage.__name__}')
    print('optional_backend_modules:')
    for name, module in BACKENDS['optional']:
        print(f'  {name}: {is_available(module)}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
