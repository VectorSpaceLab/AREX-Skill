#!/usr/bin/env python3
"""CPU-only Towhee data utilities smoke test.

This script validates DataCollection conversion, Entity.combine semantics, and
DataLoader batching with a tiny in-process pipeline. It performs no network
access, model download, service startup, or GPU work.
"""

from __future__ import annotations

import argparse
import sys
from typing import Any


def _fail(message: str) -> None:
    raise AssertionError(message)


def _assert_equal(actual: Any, expected: Any, label: str) -> None:
    if actual != expected:
        _fail(f'{label}: expected {expected!r}, got {actual!r}')


def run(verbose: bool = False) -> int:
    try:
        import towhee
        from towhee.datacollection import DataCollection as DataCollectionClass
        from towhee.datacollection import Entity
    except Exception as exc:  # pragma: no cover - environment diagnostic path
        print(f'FAILED import Towhee data utilities: {exc}', file=sys.stderr)
        print('Install Towhee with its base runtime dependencies before running this smoke test.', file=sys.stderr)
        return 2

    runtime_pipeline = (
        towhee.pipe.input('num')
            .map('num', 'double', lambda x: x * 2)
            .output('num', 'double')
    )

    result_queue = runtime_pipeline(3)
    _assert_equal(result_queue.schema, ['num', 'double'], 'runtime result schema')

    dc = towhee.DataCollection(result_queue)
    if not isinstance(dc, DataCollectionClass):
        _fail(f'towhee.DataCollection returned {type(dc)!r}, not DataCollection')

    rows = dc.to_list()
    _assert_equal(len(rows), 1, 'DataCollection row count')
    _assert_equal(rows[0].num, 3, 'Entity attribute read')
    _assert_equal(rows[0]['double'], 6, 'Entity item read')
    if verbose:
        print(f'[data-smoke] DataCollection rows OK: {rows!r}')

    dc_dict = dc.to_dict()
    _assert_equal(dc_dict['schema'], ['num', 'double'], 'to_dict schema')
    _assert_equal(dc_dict['type_schema'], ['SCALAR', 'SCALAR'], 'to_dict type schema')
    _assert_equal(dc_dict['iterable'], [[3, 6]], 'to_dict iterable')

    restored = DataCollectionClass.from_dict(dc_dict)
    _assert_equal(restored.to_dict(), dc_dict, 'from_dict round trip')

    restored_via_public_wrapper = towhee.DataCollection(dc_dict)
    _assert_equal(restored_via_public_wrapper.to_dict(), dc_dict, 'public wrapper dict round trip')
    if verbose:
        print('[data-smoke] DataCollection serialization round trip OK')

    entity = Entity(a=1)
    combine_ret = entity.combine(Entity(b=2), Entity(c=3))
    if combine_ret is not None:
        _fail('Entity.combine should mutate in place and return None')
    _assert_equal(entity.__dict__, {'a': 1, 'b': 2, 'c': 3}, 'Entity.combine mutation')
    if verbose:
        print(f'[data-smoke] Entity.combine mutation OK: {entity.__dict__!r}')

    batches = list(
        towhee.DataLoader(
            [{'value': 0}, {'value': 1}, {'value': 2}, {'value': 3}, {'value': 4}],
            parser=lambda item: item['value'] + 10,
            batch_size=2,
        )
    )
    _assert_equal(batches, [[10, 11], [12, 13], [14]], 'DataLoader parsed batches')

    callable_source_items = list(
        towhee.DataLoader(
            lambda: iter([1, 2, 3]),
            parser=lambda item: item * 5,
        )
    )
    _assert_equal(callable_source_items, [5, 10, 15], 'DataLoader callable source')
    if verbose:
        print('[data-smoke] DataLoader iterable/callable sources OK')

    print('Towhee data utilities smoke test passed.')
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Run a safe Towhee DataCollection/DataLoader smoke test.')
    parser.add_argument('--verbose', action='store_true', help='Print successful checkpoints.')
    args = parser.parse_args(argv)
    return run(verbose=args.verbose)


if __name__ == '__main__':
    raise SystemExit(main())
