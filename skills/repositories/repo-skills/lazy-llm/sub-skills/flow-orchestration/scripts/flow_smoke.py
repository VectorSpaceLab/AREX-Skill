#!/usr/bin/env python3
"""Safe LazyLLM flow primitive smoke check."""
from __future__ import annotations

import argparse
import json
from typing import Dict


def run() -> Dict[str, object]:
    from lazyllm import bind, diverter, ifs, loop, parallel, pipeline, switch

    add_one = lambda x: x + 1
    pipe_result = pipeline(add_one, add_one)(1)
    assert pipe_result == 3

    with pipeline() as p:
        p.f1 = add_one
        p.f2 = add_one
        p.f3 = (lambda x, y, z=0: x + y + 2 * z) | bind(y=p.input, z=p.f1)
    bind_result = p(2)
    assert bind_result == 12

    par = parallel(lambda x: x + 1, lambda x: x * 2)
    parallel_result = par(3)
    assert parallel_result == (4, 6)

    with parallel() as named:
        named.a = lambda x: x + 1
        named.b = lambda x: x + 2
        named.c = lambda x: x + 3
    kept_result = named(0, _kept_items=["a", "c"])
    assert kept_result == (1, 3)

    div_result = diverter(lambda x: x + 1, lambda x: x * 2, lambda x: -x)(1, 2, 3)
    assert div_result == (2, 4, -3)

    is_one = lambda x: x == 1
    is_two = lambda x: x == 2
    sw = switch({is_one: lambda x: x * 2, is_two: lambda x: x * 3, "default": lambda x: x}, judge_on_full_input=True)
    switch_result = sw(2)
    assert switch_result == 6

    ifs_result = ifs(lambda x: x > 0, lambda x: x, lambda x: -x)(2)
    assert ifs_result == 2

    loop_result = loop(add_one, count=2)(0)
    assert loop_result == 2

    return {
        "pipeline": pipe_result,
        "bind_pipeline": bind_result,
        "parallel": parallel_result,
        "kept_items": kept_result,
        "diverter": div_result,
        "switch": switch_result,
        "ifs": ifs_result,
        "loop": loop_result,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run safe LazyLLM flow smoke checks.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text.")
    args = parser.parse_args()
    result = run()
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        for key, value in result.items():
            print(f"{key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
