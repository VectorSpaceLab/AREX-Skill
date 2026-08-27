#!/usr/bin/env python3
"""Run a CPU-local LightningStore lifecycle smoke test.

This checks resources, enqueue/dequeue, span sequence IDs, span persistence, and
terminal status updates in an InMemoryLightningStore. It does not start servers
or require external services.

Example:
    python scripts/store_status_smoke.py
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path


def _configure_path(repo_root: str | None) -> None:
    if repo_root:
        sys.path.insert(0, str(Path(repo_root)))


async def _run(verbose: bool = False) -> None:
    import agentlightning as agl

    store = agl.InMemoryLightningStore()
    resources_update = await store.add_resources(
        {"prompt_template": agl.PromptTemplate(template="Task: {task}", engine="f-string")}
    )
    assert resources_update.resources_id
    assert resources_update.version == 1

    cfg = agl.RolloutConfig(timeout_seconds=30.0, unresponsive_seconds=10.0, max_attempts=2, retry_condition=["failed"])
    queued = await store.enqueue_rollout(
        input={"task": "store smoke"},
        mode="train",
        resources_id=resources_update.resources_id,
        config=cfg,
        metadata={"origin": "store_status_smoke"},
    )
    assert queued.status == "queuing"

    attempted = await store.dequeue_rollout(worker_id="smoke-worker")
    assert attempted is not None
    assert attempted.status == "preparing"
    assert attempted.attempt.status == "preparing"
    assert attempted.attempt.worker_id == "smoke-worker"

    seq = await store.get_next_span_sequence_id(attempted.rollout_id, attempted.attempt.attempt_id)
    span = agl.Span.from_attributes(
        rollout_id=attempted.rollout_id,
        attempt_id=attempted.attempt.attempt_id,
        sequence_id=seq,
        name="store-smoke-span",
        attributes={"smoke": "true"},
    )
    stored_span = await store.add_span(span)
    assert stored_span is not None

    running = await store.query_rollouts(status_in=["running"])
    assert any(item.rollout_id == attempted.rollout_id for item in running)

    await store.update_attempt(attempted.rollout_id, attempted.attempt.attempt_id, status="succeeded")
    finished = await store.query_rollouts(rollout_id_in=[attempted.rollout_id])
    assert len(finished) == 1
    assert finished[0].status == "succeeded", finished[0].status

    spans = await store.query_spans(attempted.rollout_id)
    assert len(spans) == 1
    assert spans[0].name == "store-smoke-span"

    if verbose:
        print("resources_id=", resources_update.resources_id)
        print("rollout_id=", attempted.rollout_id)
        print("attempt_id=", attempted.attempt.attempt_id)
        print("capabilities=", dict(store.capabilities))
    print(f"PASS rollout_id={attempted.rollout_id} status={finished[0].status} spans={len(spans)}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a local LightningStore lifecycle smoke test.")
    parser.add_argument("--repo-root", help="Optional checkout root to prepend to sys.path before import.")
    parser.add_argument("--verbose", action="store_true", help="Print resource and rollout identifiers.")
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
