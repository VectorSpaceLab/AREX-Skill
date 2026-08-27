#!/usr/bin/env python3
"""Run a tiny Agent Lightning @rollout smoke test.

The test uses only CPU-local components: InMemoryLightningStore, OtelTracer, and
LitAgentRunner.step. It proves that a function-based agent can receive a
PromptTemplate resource and produce a final reward span.

Example:
    python scripts/agent_rollout_smoke.py
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path
from typing import Dict


def _configure_path(repo_root: str | None) -> None:
    if repo_root:
        sys.path.insert(0, str(Path(repo_root)))


async def _run(verbose: bool = False) -> None:
    import agentlightning as agl

    @agl.rollout
    def keyword_agent(task: Dict[str, str], prompt_template: agl.PromptTemplate) -> float:
        rendered = prompt_template.format(question=task["question"])
        if verbose:
            print("rendered_prompt=", rendered)
        return 1.0 if "Agent Lightning" in rendered else 0.0

    store = agl.InMemoryLightningStore()
    runner = agl.LitAgentRunner[Dict[str, str]](tracer=agl.OtelTracer(), poll_interval=0.01, heartbeat_interval=0.5)
    resources = {
        "prompt_template": agl.PromptTemplate(
            template="Answer this Agent Lightning question: {question}",
            engine="f-string",
        )
    }

    with runner.run_context(agent=keyword_agent, store=store):
        rollout = await runner.step({"question": "does resource injection work?"}, resources=resources)

    spans = await store.query_spans(rollout.rollout_id)
    final_reward = agl.find_final_reward(spans)
    assert rollout.status == "succeeded", rollout.status
    assert final_reward == 1.0, final_reward
    assert spans, "expected at least one span"
    print(f"PASS rollout_id={rollout.rollout_id} status={rollout.status} spans={len(spans)} reward={final_reward}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a minimal Agent Lightning rollout smoke test.")
    parser.add_argument("--repo-root", help="Optional checkout root to prepend to sys.path before import.")
    parser.add_argument("--verbose", action="store_true", help="Print the rendered prompt.")
    args = parser.parse_args()
    _configure_path(args.repo_root)
    try:
        asyncio.run(_run(verbose=args.verbose))
    except Exception as exc:  # pragma: no cover - diagnostic helper
        print(f"FAIL {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
