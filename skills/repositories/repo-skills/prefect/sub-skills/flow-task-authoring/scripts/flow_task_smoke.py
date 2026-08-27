#!/usr/bin/env python3
"""Deterministic Prefect flow/task authoring smoke checks.

This script is bundled with the Prefect repo skill and avoids network calls,
credentials, long-running services, and dependencies on the original checkout.
"""

from __future__ import annotations

import argparse
import json
import re
from html.parser import HTMLParser
from typing import Any

from prefect import flow, task
from prefect.cache_policies import INPUTS
from prefect.states import Failed
from prefect.task_runners import ThreadPoolTaskRunner


SAMPLE_HTML = """
<html>
  <body>
    <main>
      <h1>Prefect Smoke</h1>
      <p>Flows compose tasks.</p>
      <pre>ignored code block</pre>
      <p>Retries, futures, and cache policies stay regular Python.</p>
    </main>
  </body>
</html>
"""


class ArticleTextParser(HTMLParser):
    """Small standard-library parser for deterministic local HTML extraction."""

    def __init__(self) -> None:
        super().__init__()
        self._ignored_depth = 0
        self._capture = False
        self._parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"main", "article"}:
            self._capture = True
        if tag in {"pre", "code", "script", "style"}:
            self._ignored_depth += 1
        if self._capture and tag in {"h1", "h2", "h3", "p", "li"}:
            self._parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"pre", "code", "script", "style"} and self._ignored_depth:
            self._ignored_depth -= 1
        if tag in {"main", "article"}:
            self._capture = False

    def handle_data(self, data: str) -> None:
        if self._capture and not self._ignored_depth:
            text = data.strip()
            if text:
                self._parts.append(text)

    def text(self) -> str:
        compact = " ".join(part.strip() for part in self._parts if part.strip())
        return re.sub(r"\s+", " ", compact).strip()


@task(log_prints=True)
def greet(name: str) -> str:
    print(f"Greeting {name}")
    return f"Hello, {name.title()}!"


@task(retries=1, retry_delay_seconds=0, cache_policy=INPUTS, persist_result=True)
def parse_article(html: str) -> dict[str, Any]:
    parser = ArticleTextParser()
    parser.feed(html)
    text = parser.text()
    return {"text": text, "word_count": len(text.split())}


@task
def word_lengths(words: list[str]) -> list[int]:
    return [len(word) for word in words]


@task
def fail_deliberately() -> Failed:
    return Failed(message="intentional smoke failure")


@flow(name="flow-task-basic-smoke", log_prints=True)
def basic_flow(name: str) -> dict[str, Any]:
    greeting = greet(name)
    parsed = parse_article(SAMPLE_HTML)
    return {"greeting": greeting, "parsed": parsed}


@flow(
    name="flow-task-futures-smoke",
    task_runner=ThreadPoolTaskRunner(max_workers=4),
    log_prints=True,
)
def futures_flow(words: list[str]) -> dict[str, Any]:
    greeting_future = greet.submit("prefect")
    lengths_future = word_lengths.submit(words, wait_for=[greeting_future])
    mapped = greet.map(words)
    return {
        "greeting": greeting_future.result(),
        "lengths": lengths_future.result(),
        "mapped": mapped.result(),
    }


@flow(name="flow-task-state-smoke")
def state_flow() -> Any:
    return fail_deliberately(return_state=True)


@flow(name="flow-task-cache-smoke")
def cache_flow() -> dict[str, Any]:
    first = parse_article(SAMPLE_HTML)
    second = parse_article(SAMPLE_HTML)
    return {
        "first_word_count": first["word_count"],
        "second_word_count": second["word_count"],
        "same_text": first["text"] == second["text"],
    }


def run_mode(mode: str) -> dict[str, Any]:
    report: dict[str, Any] = {"mode": mode}

    if mode in {"basic", "all"}:
        report["basic"] = basic_flow("marvin")

    if mode in {"futures", "all"}:
        report["futures"] = futures_flow(["flow", "task", "future"])

    if mode in {"state", "all"}:
        state = state_flow(return_state=True)
        report["state"] = {
            "name": state.name,
            "is_failed": state.is_failed(),
            "message": state.message,
            "data": str(state.result(raise_on_failure=False)),
        }

    if mode in {"cache", "all"}:
        report["cache"] = cache_flow()

    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run deterministic Prefect flow/task authoring smoke checks."
    )
    parser.add_argument(
        "--mode",
        choices=["basic", "futures", "state", "cache", "all"],
        default="all",
        help="Smoke scenario to run. Defaults to all.",
    )
    parser.add_argument(
        "--indent",
        type=int,
        default=2,
        help="JSON indentation for stdout. Use 0 for compact output.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    indent = None if args.indent == 0 else args.indent
    print(json.dumps(run_mode(args.mode), indent=indent, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
