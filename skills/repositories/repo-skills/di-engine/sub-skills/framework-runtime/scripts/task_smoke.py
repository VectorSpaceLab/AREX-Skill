#!/usr/bin/env python3
"""Small task-runtime smoke for DI-engine.

This script exercises the task context, middleware registration, and the
single-process runner without starting a full training job.
"""

from __future__ import annotations

from dataclasses import field, make_dataclass

from ding.framework import Context, task


def main() -> None:
    ctx_type = make_dataclass('SmokeContext', [('steps', list, field(default_factory=list))], bases=(Context,))
    with task.start(ctx=ctx_type()):
        task.use(lambda ctx: ctx.steps.append('a'))
        task.use(lambda ctx: ctx.steps.append('b'))
        task.run(2)
        print(task.ctx.steps)


if __name__ == '__main__':
    main()
