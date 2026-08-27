#!/usr/bin/env python3
"""Validate Flower app wiring and run a tiny runtime smoke.

The validator is intentionally conservative:
- it checks ``pyproject.toml`` with Flower's own configuration validator
- it does not import the target app module to validate the component strings
- it then exercises only in-memory Flower app objects and a tiny app harness
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import tomllib

from flwr.app import ArrayRecord, ConfigRecord, Context, Message, MetricRecord, RecordDict
from flwr.clientapp import ClientApp
from flwr.common.config import validate_config
from flwr.serverapp import Grid, ServerApp
from flwr.serverapp.strategy import FedAvg


class DummyGrid(Grid):
    """Tiny Grid stub used only for the local smoke."""

    def __init__(self) -> None:
        self._run: Any = None

    def set_run(self, run: Any) -> None:
        self._run = run

    @property
    def run(self) -> Any:
        return self._run

    def create_message(  # pylint: disable=too-many-arguments
        self,
        content: RecordDict,
        message_type: str,
        dst_node_id: int,
        group_id: str,
        ttl: float | None = None,
    ) -> Message:
        raise AssertionError("DummyGrid.create_message() should not be called")

    def get_node_ids(self) -> list[int]:
        return []

    def push_messages(self, messages: Any) -> list[str]:
        return []

    def pull_messages(self, message_ids: Any) -> list[Message]:
        return []

    def send_and_receive(
        self, messages: Any, *, timeout: float | None = None
    ) -> list[Message]:
        return []


def load_pyproject(pyproject: Path) -> dict[str, Any]:
    """Load a pyproject.toml file."""
    with pyproject.open("rb") as file:
        try:
            return tomllib.load(file)
        except tomllib.TOMLDecodeError as err:
            raise ValueError(f"Invalid TOML in {pyproject}: {err}") from err


def validate_pyproject(pyproject: Path) -> None:
    """Validate Flower app metadata and component wiring."""
    config = load_pyproject(pyproject)
    is_valid, errors, warnings = validate_config(
        config,
        check_module=True,
        project_dir=pyproject.parent,
    )

    for warning in warnings:
        print(f"WARN: {warning}")

    if not is_valid:
        joined = "\n".join(f"- {error}" for error in errors)
        raise ValueError(f"Invalid Flower App configuration in '{pyproject}':\n{joined}")


def run_smoke() -> None:
    """Run a tiny in-memory app smoke for core Flower app objects."""
    import numpy as np

    # Shared app state used by the smoke
    client_context = Context(
        run_id=1,
        node_id=7,
        node_config={"partition-id": 7, "num-partitions": 2},
        state=RecordDict(),
        run_config={"num-server-rounds": 3, "learning-rate": 0.5},
    )
    server_context = Context(
        run_id=2,
        node_id=0,
        node_config={},
        state=RecordDict(),
        run_config={"num-server-rounds": 3},
    )

    train_message = Message(
        RecordDict(
            {
                "arrays": ArrayRecord([np.array([1.0, 2.0], dtype=np.float32)]),
                "config": ConfigRecord({"lr": 0.5}),
            }
        ),
        dst_node_id=7,
        message_type="train",
    )
    evaluate_message = Message(
        RecordDict(
            {
                "arrays": ArrayRecord([np.array([3.0], dtype=np.float32)]),
            }
        ),
        dst_node_id=7,
        message_type="evaluate",
    )

    client_seen = {"train": 0, "evaluate": 0, "lifespan_enter": 0, "lifespan_exit": 0}
    client_app = ClientApp()

    @client_app.lifespan()
    def client_lifespan(_: Context):
        client_seen["lifespan_enter"] += 1
        yield
        client_seen["lifespan_exit"] += 1

    @client_app.train()
    def train(msg: Message, context: Context) -> Message:
        client_seen["train"] += 1
        arrays = msg.content.array_records["arrays"].to_numpy_ndarrays()
        lr = float(msg.content.config_records["config"]["lr"])
        if "history" not in context.state.metric_records:
            context.state.metric_records["history"] = MetricRecord({"count": 0})
        context.state.metric_records["history"]["count"] += 1
        updated = [arr + lr for arr in arrays]
        return Message(
            RecordDict(
                {
                    "arrays": ArrayRecord(updated),
                    "metrics": MetricRecord({"loss": 0.1, "num-examples": 2}),
                }
            ),
            reply_to=msg,
        )

    @client_app.evaluate()
    def evaluate(msg: Message, context: Context) -> Message:
        client_seen["evaluate"] += 1
        _ = msg.content.array_records["arrays"].to_numpy_ndarrays()
        if "evaluations" not in context.state.metric_records:
            context.state.metric_records["evaluations"] = MetricRecord({"count": 0})
        context.state.metric_records["evaluations"]["count"] += 1
        return Message(
            RecordDict(
                {"metrics": MetricRecord({"accuracy": 1.0, "num-examples": 2})}
            ),
            reply_to=msg,
        )

    train_reply_1 = client_app(train_message, client_context)
    train_reply_2 = client_app(train_message, client_context)
    evaluate_reply = client_app(evaluate_message, client_context)

    assert client_seen == {"train": 2, "evaluate": 1, "lifespan_enter": 3, "lifespan_exit": 3}
    assert client_context.state.metric_records["history"]["count"] == 2
    assert train_reply_1.content.array_records["arrays"].to_numpy_ndarrays()[0].tolist() == [
        1.5,
        2.5,
    ]
    assert train_reply_2.content.array_records["arrays"].to_numpy_ndarrays()[0].tolist() == [
        1.5,
        2.5,
    ]
    assert evaluate_reply.content.metric_records["metrics"]["accuracy"] == 1.0
    assert evaluate_reply.content.metric_records["metrics"]["num-examples"] == 2

    server_seen = {"called": 0, "lifespan_enter": 0, "lifespan_exit": 0}
    server_app = ServerApp()

    @server_app.lifespan()
    def server_lifespan(_: Context):
        server_seen["lifespan_enter"] += 1
        yield
        server_seen["lifespan_exit"] += 1

    @server_app.main()
    def main(grid: Grid, context: Context) -> None:
        server_seen["called"] += 1
        assert isinstance(grid, DummyGrid)
        assert context.run_config["num-server-rounds"] == 3
        assert FedAvg().__class__.__name__ == "FedAvg"

    server_app(DummyGrid(), server_context)

    assert server_seen == {"called": 1, "lifespan_enter": 1, "lifespan_exit": 1}


def main(argv: list[str] | None = None) -> int:
    """Entry point."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--pyproject",
        type=Path,
        default=Path("pyproject.toml"),
        help="Path to the Flower app pyproject.toml file.",
    )
    parser.add_argument(
        "--skip-smoke",
        action="store_true",
        help="Only validate pyproject.toml wiring and skip the in-memory smoke.",
    )
    args = parser.parse_args(argv)

    pyproject = args.pyproject.expanduser().resolve()
    if not pyproject.is_file():
        print(f"ERROR: Cannot find {pyproject}", file=sys.stderr)
        return 1

    try:
        validate_pyproject(pyproject)
        if not args.skip_smoke:
            run_smoke()
    except Exception as err:  # pylint: disable=broad-exception-caught
        print(f"ERROR: {err}", file=sys.stderr)
        return 1

    print("OK: Flower app wiring and smoke checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
