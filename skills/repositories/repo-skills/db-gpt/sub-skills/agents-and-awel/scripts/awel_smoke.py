#!/usr/bin/env python3
"""Run a deterministic, no-model AWEL topology and execution smoke check.

This helper only builds an in-memory DAG, registers its route on a plain FastAPI
router, validates a pydantic request body, and executes a tiny local MapOperator. It
never starts a web server, contacts a provider, or reads a checkout-relative file.
"""

from __future__ import annotations

import argparse
import asyncio
import inspect
import json
from typing import Any

from fastapi import APIRouter

from dbgpt._private.pydantic import BaseModel, Field, ValidationError
from dbgpt.core.awel import DAG, HttpTrigger, MapOperator


class SmokeRequest(BaseModel):
    """Small request body used by the local smoke graph."""

    name: str = Field(..., min_length=1, description="Name to greet")
    age: int = Field(18, ge=0, description="Non-negative age")


class GreetingOperator(MapOperator[SmokeRequest, dict[str, Any]]):
    """Return a deterministic JSON-compatible greeting."""

    async def map(self, input_value: SmokeRequest) -> dict[str, Any]:
        return {"message": f"Hello, {input_value.name}", "age": input_value.age}


def build_graph() -> tuple[DAG, HttpTrigger, GreetingOperator]:
    """Build a two-node graph without starting an application."""

    with DAG("agents_awel_smoke") as dag:
        trigger = HttpTrigger(
            "/examples/smoke/{dag_id}",
            methods="POST",
            request_body=SmokeRequest,
            task_name="smoke-trigger",
        )
        leaf = GreetingOperator(task_id="smoke-leaf-id", task_name="smoke-leaf")
        trigger >> leaf
    return dag, trigger, leaf


def validate_topology(dag: DAG, trigger: HttpTrigger, leaf: GreetingOperator) -> dict[str, Any]:
    """Validate graph identity and HTTP route metadata without network I/O."""

    if len(dag.root_nodes) != 1:
        raise AssertionError(f"expected one root, got {len(dag.root_nodes)}")
    if len(dag.leaf_nodes) != 1 or dag.leaf_nodes[0] is not leaf:
        raise AssertionError("expected the greeting operator to be the only leaf")
    if len(dag.trigger_nodes) != 1 or dag.trigger_nodes[0] is not trigger:
        raise AssertionError("expected one HTTP trigger")
    if trigger._resolved_endpoint() != "/examples/smoke/agents_awel_smoke":
        raise AssertionError(f"unexpected resolved endpoint: {trigger._resolved_endpoint()}")

    router = APIRouter()
    metadata = trigger.mount_to_router(
        router, global_prefix="/api/v1/awel/trigger"
    )
    if metadata.path != "/api/v1/awel/trigger/examples/smoke/agents_awel_smoke":
        raise AssertionError(f"unexpected mounted path: {metadata.path}")
    if metadata.methods != ["POST"]:
        raise AssertionError(f"unexpected methods: {metadata.methods}")
    if len(router.routes) != 1:
        raise AssertionError(f"expected one router route, got {len(router.routes)}")

    endpoint = router.routes[0].endpoint
    endpoint_signature = str(inspect.signature(endpoint))
    return {
        "dag_id": dag.dag_id,
        "node_ids": sorted(dag.node_map),
        "root_names": [node.node_name for node in dag.root_nodes],
        "leaf_names": [node.node_name for node in dag.leaf_nodes],
        "trigger_path": metadata.path,
        "methods": metadata.methods,
        "route_signature": endpoint_signature,
    }


async def run_fixture(leaf: GreetingOperator, payload: dict[str, Any]) -> dict[str, Any]:
    """Validate a request model and execute the leaf through the local runner."""

    body = SmokeRequest.model_validate(payload)
    result = await leaf.call(body)
    expected = {"message": f"Hello, {body.name}", "age": body.age}
    if result != expected:
        raise AssertionError(f"unexpected local result: {result!r}")
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check a tiny DB-GPT AWEL DAG locally (no server, model, or network)."
    )
    parser.add_argument(
        "--payload",
        default='{"name":"Ada","age":36}',
        help="JSON object validated by the pydantic HTTP body (default: Ada, age 36).",
    )
    parser.add_argument(
        "--check-invalid",
        action="store_true",
        help="Also assert that a missing required name is rejected by pydantic.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        payload = json.loads(args.payload)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"--payload must be a JSON object: {exc}") from exc
    if not isinstance(payload, dict):
        raise SystemExit("--payload must decode to a JSON object")

    dag, trigger, leaf = build_graph()
    topology = validate_topology(dag, trigger, leaf)
    result = asyncio.run(run_fixture(leaf, payload))

    invalid_check = False
    if args.check_invalid:
        try:
            SmokeRequest.model_validate({"age": 1})
        except ValidationError:
            invalid_check = True
        else:
            raise AssertionError("missing required name was accepted")

    print(json.dumps({"topology": topology, "result": result, "invalid_check": invalid_check}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
