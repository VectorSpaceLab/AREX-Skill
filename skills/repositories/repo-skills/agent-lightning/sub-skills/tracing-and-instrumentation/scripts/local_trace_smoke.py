#!/usr/bin/env python3
"""Run a local Agent Lightning tracing smoke test.

This script uses an in-memory store and OtelTracer to emit message, object,
operation, linked/tagged reward spans, then verifies the final reward.

Example:
    python scripts/local_trace_smoke.py
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path
from typing import Sequence


def _configure_path(repo_root: str | None) -> None:
    if repo_root:
        sys.path.insert(0, str(Path(repo_root)))


async def _run(verbose: bool = False) -> None:
    import agentlightning as agl
    from agentlightning.semconv import AGL_ANNOTATION, AGL_MESSAGE, AGL_OBJECT, AGL_OPERATION
    from agentlightning.utils.otel import extract_links_from_attributes, extract_tags_from_attributes
    from agentlightning.utils.otel import make_link_attributes, make_tag_attributes, query_linked_spans

    store = agl.InMemoryLightningStore()
    tracer = agl.OtelTracer()
    rollout = await store.start_rollout(input={"origin": "local_trace_smoke"})
    operation_id = "local-op-1"
    tags: Sequence[str] = ("smoke", "final")

    with tracer.lifespan(store):
        async with tracer.trace_context(
            "local-trace-smoke",
            store=store,
            rollout_id=rollout.rollout_id,
            attempt_id=rollout.attempt.attempt_id,
        ):
            agl.emit_message("starting local trace smoke")
            agl.emit_object({"operation_id": operation_id, "step": 1})
            with agl.operation(name="local-operation", operation_id=operation_id) as op:
                op.set_input(task="synthetic")
                op.set_output({"ok": True})
            agl.emit_reward(
                1.0,
                attributes={
                    **make_tag_attributes(list(tags)),
                    **make_link_attributes({"operation_id": operation_id}),
                },
            )

    spans = list(await store.query_spans(rollout.rollout_id))
    names = [span.name for span in spans]
    assert AGL_MESSAGE in names, names
    assert AGL_OBJECT in names, names
    assert AGL_OPERATION in names or "local-operation" in names, names
    assert AGL_ANNOTATION in names, names
    assert agl.find_final_reward(spans) == 1.0

    reward_span = [span for span in spans if span.name == AGL_ANNOTATION][-1]
    extracted_tags = extract_tags_from_attributes(dict(reward_span.attributes or {}))
    extracted_links = extract_links_from_attributes(dict(reward_span.attributes or {}))
    assert set(tags).issubset(set(extracted_tags)), extracted_tags
    linked = query_linked_spans(spans, extracted_links)
    assert linked, "expected at least one span linked by operation_id"

    if verbose:
        for span in spans:
            print(f"span name={span.name} seq={span.sequence_id} keys={sorted((span.attributes or {}).keys())}")
    print(f"PASS rollout_id={rollout.rollout_id} spans={len(spans)} reward=1.0 tags={','.join(extracted_tags)}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a local Agent Lightning trace smoke test.")
    parser.add_argument("--repo-root", help="Optional checkout root to prepend to sys.path before import.")
    parser.add_argument("--verbose", action="store_true", help="Print recorded span names and attribute keys.")
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
