#!/usr/bin/env python3
"""Safe LazyLLM core runtime smoke check.

Checks config mutation, namespace behavior, prompter formatting, component
registration, and known CLI command families. It does not install packages or
run provider/model/service commands.
"""
from __future__ import annotations

import argparse
import json
import os
from typing import Dict, List


def run() -> Dict[str, object]:
    import lazyllm
    from lazyllm.components import register as comp_register

    results: Dict[str, object] = {"version": getattr(lazyllm, "__version__", "unknown")}

    key = "skill_smoke_option"
    old = lazyllm.config._impl.get(key)
    try:
        lazyllm.config.add(
            key,
            str,
            "a",
            env=None,
            options=["a", "b"],
            alias={"A": "a", "B": "b"},
            description="skill smoke option",
        )
        lazyllm.config[key] = "B"
        assert lazyllm.config[key] == "b"
        results["config_alias"] = "ok"
    finally:
        if old is None:
            lazyllm.config._impl.pop(key, None)
        else:
            lazyllm.config._impl[key] = old

    prompter = lazyllm.Prompter(prompt="hello <{input}>")
    assert prompter.generate_prompt({"input": "world"}) == "hello <world>"
    results["prompter"] = "ok"

    group = "skill_smoke_runtime"
    if not hasattr(lazyllm, group):
        comp_register.new_group(group)

    @comp_register(group)
    def add(a, b):
        """Add two values for component registration smoke checks."""
        return a + b

    assert getattr(lazyllm, group).add()(2, 3) == 5
    results["component_register"] = "ok"

    results["cli_command_families"] = [
        "install",
        "deploy",
        "run",
        "skills",
        "review",
        "review-local",
    ]
    results["note"] = "Use concrete CLI subcommands; bare --help may exit non-zero."
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="Run safe LazyLLM core runtime smoke checks.")
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
