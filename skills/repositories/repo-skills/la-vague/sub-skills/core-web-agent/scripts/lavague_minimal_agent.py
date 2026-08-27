#!/usr/bin/env python3
"""Safe LaVague WebAgent template/probe.

Default behavior is dry-run only: validate imports and print a runnable template.
Use --run-live only when browser automation, provider API calls, network access,
and any resulting logs/telemetry are explicitly permitted.
"""

from __future__ import annotations

import argparse
import os
import sys
from textwrap import dedent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Probe LaVague core imports and print/run a minimal WebAgent template.")
    parser.add_argument("--dry-run", action="store_true", default=True, help="Validate imports and print a template without live browser/model calls (default).")
    parser.add_argument("--run-live", action="store_true", help="Actually construct a browser and run the objective. Requires browser + model credentials + permission.")
    parser.add_argument("--driver", choices=["selenium", "none"], default="selenium", help="Driver template to use. 'none' only validates core imports.")
    parser.add_argument("--url", default="https://example.com", help="Starting URL for the printed template or live run.")
    parser.add_argument("--objective", default="Summarize the visible page", help="Objective for the printed template or live run.")
    parser.add_argument("--headless", action=argparse.BooleanOptionalAction, default=True, help="Whether the live Selenium template uses headless mode.")
    parser.add_argument("--steps", type=int, default=5, help="Maximum WebAgent steps in the template/live run.")
    parser.add_argument("--disable-telemetry", action="store_true", help="Set LAVAGUE_TELEMETRY=NONE in this process before imports.")
    return parser.parse_args()


def import_core() -> tuple[bool, str]:
    try:
        from lavague.core import ActionEngine, WorldModel  # noqa: F401
        from lavague.core.agents import WebAgent  # noqa: F401
        from lavague.core.token_counter import TokenCounter  # noqa: F401
        return True, "core imports ok"
    except Exception as exc:  # pragma: no cover - diagnostic path
        return False, f"core import failed: {type(exc).__name__}: {exc}"


def import_selenium() -> tuple[bool, str]:
    try:
        from lavague.drivers.selenium import SeleniumDriver  # noqa: F401
        return True, "selenium driver import ok"
    except Exception as exc:  # pragma: no cover - diagnostic path
        return False, f"selenium import failed: {type(exc).__name__}: {exc}"


def print_template(args: argparse.Namespace) -> None:
    telemetry = "\n# Optional privacy control before importing/running LaVague:\n# import os; os.environ['LAVAGUE_TELEMETRY'] = 'NONE'\n"
    if args.driver == "none":
        print("Core imports were checked. Choose a driver before building a live WebAgent.")
        return
    print(dedent(f"""
    {telemetry}
    from lavague.core import WorldModel, ActionEngine
    from lavague.core.agents import WebAgent
    from lavague.drivers.selenium import SeleniumDriver

    driver = SeleniumDriver(headless={args.headless!r})
    action_engine = ActionEngine(driver)
    world_model = WorldModel()
    agent = WebAgent(world_model, action_engine, n_steps={args.steps})
    agent.get({args.url!r})
    result = agent.run({args.objective!r})
    print(result.success)
    print(result.output)
    """).strip())


def run_live(args: argparse.Namespace) -> int:
    if args.driver == "none":
        print("--run-live requires a real driver; choose --driver selenium", file=sys.stderr)
        return 2
    if not os.environ.get("OPENAI_API_KEY"):
        print("OPENAI_API_KEY is not set. Default LaVague contexts normally require it; aborting live run.", file=sys.stderr)
        return 3
    from lavague.core import ActionEngine, WorldModel
    from lavague.core.agents import WebAgent
    from lavague.drivers.selenium import SeleniumDriver

    driver = SeleniumDriver(headless=args.headless)
    action_engine = ActionEngine(driver)
    world_model = WorldModel()
    agent = WebAgent(world_model, action_engine, n_steps=args.steps)
    agent.get(args.url)
    result = agent.run(args.objective)
    print("success:", result.success)
    print("output:", result.output)
    print("generated_code:\n", result.code)
    return 0


def main() -> int:
    args = parse_args()
    if args.disable_telemetry:
        os.environ["LAVAGUE_TELEMETRY"] = "NONE"
    ok, message = import_core()
    print(message)
    if not ok:
        return 1
    if args.driver == "selenium":
        ok, message = import_selenium()
        print(message)
        if not ok:
            return 1
    if args.run_live:
        print("LIVE RUN REQUESTED: this may launch a browser, contact model providers, browse the web, and create logs.")
        return run_live(args)
    print_template(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
