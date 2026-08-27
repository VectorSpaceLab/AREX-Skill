#!/usr/bin/env python3
from __future__ import annotations

import inspect
from typing import Any


def main() -> int:
    from upsonic import Agent, Direct, Graph, Task

    report: dict[str, Any] = {
        'Task': str(inspect.signature(Task.__init__)),
        'Agent': str(inspect.signature(Agent.__init__)),
        'Agent.do': str(inspect.signature(Agent.do)),
        'Agent.do_async': str(inspect.signature(Agent.do_async)),
        'Direct': str(inspect.signature(Direct.__init__)),
        'Direct.do': str(inspect.signature(Direct.do)),
        'Graph': Graph.__module__ + '.' + Graph.__name__,
    }

    for key, value in report.items():
        print(f'{key}: {value}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
