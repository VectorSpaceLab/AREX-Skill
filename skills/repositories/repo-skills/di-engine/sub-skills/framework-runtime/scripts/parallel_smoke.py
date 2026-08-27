#!/usr/bin/env python3
"""Small Parallel smoke for DI-engine.

This script verifies that the multi-process router can start, exchange a simple
message, and shut down cleanly.
"""

from __future__ import annotations

import time

from ding.framework import Parallel


def main() -> None:
    router = Parallel()
    if router.node_id == 0:
        got = []
        router.on('ping', lambda msg: got.append(msg))
        for _ in range(40):
            if got:
                break
            time.sleep(0.1)
        assert got == ['pong'], got
        print('received', got[0])
    else:
        time.sleep(0.5)
        router.emit('ping', 'pong')


if __name__ == '__main__':
    Parallel.runner(n_parallel_workers=2, protocol='tcp', topology='mesh', startup_interval=0.1)(main)
