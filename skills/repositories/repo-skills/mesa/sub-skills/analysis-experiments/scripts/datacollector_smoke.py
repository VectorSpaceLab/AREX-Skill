#!/usr/bin/env python3
"""Installed-package smoke test for Mesa DataCollector workflows.

Creates a tiny model, collects model / agent / agent-type / table data, and
prints a JSON payload. It is safe to run from any working directory as long as
Mesa and pandas are importable in the active Python environment.
"""

from __future__ import annotations

import json
from typing import Any


def _json_default(value: Any) -> Any:
    """Convert common NumPy/pandas scalar values to JSON primitives."""
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:  # pragma: no cover - defensive conversion
            pass
    return str(value)


def _fail(stage: str, exc: BaseException) -> int:
    print(
        json.dumps(
            {
                "ok": False,
                "stage": stage,
                "error": type(exc).__name__,
                "message": str(exc),
            },
            sort_keys=True,
        )
    )
    return 1


def main() -> int:
    try:
        import mesa
        from mesa import Agent, Model
        from mesa.datacollection import DataCollector
    except Exception as exc:  # pragma: no cover - import guard
        return _fail("import", exc)

    class TinyAgent(Agent):
        def __init__(self, model: Model, kind: str, value: int):
            super().__init__(model)
            self.kind = kind
            self.value = value

        def step(self) -> None:
            self.value += 1

        def doubled(self) -> int:
            return self.value * 2

    class TinyModel(Model):
        def __init__(self):
            super().__init__(rng=42)
            TinyAgent.create_agents(self, 3, ["alpha", "beta", "alpha"], [1, 2, 3])
            self.datacollector = DataCollector(
                model_reporters={
                    "agent_count": self.agent_count,
                    "total_value": self.total_value,
                    "alpha_count": lambda model: sum(
                        1 for agent in model.agents if agent.kind == "alpha"
                    ),
                },
                agent_reporters={
                    "kind": "kind",
                    "value": "value",
                    "doubled": TinyAgent.doubled,
                },
                agenttype_reporters={TinyAgent: {"value": "value"}},
                tables={"events": ["time", "event", "agent_count", "total_value"]},
            )
            self.record("initial")

        def agent_count(self) -> int:
            return len(self.agents)

        def total_value(self) -> int:
            return sum(agent.value for agent in self.agents)

        def record(self, event: str) -> None:
            self.datacollector.collect(self)
            self.datacollector.add_table_row(
                "events",
                {
                    "time": self.time,
                    "event": event,
                    "agent_count": self.agent_count(),
                    "total_value": self.total_value(),
                },
            )

        def step(self) -> None:
            self.agents.do("step")
            self.record("step")

    try:
        model = TinyModel()
        model.run_for(3)

        model_df = model.datacollector.get_model_vars_dataframe()
        agent_df = model.datacollector.get_agent_vars_dataframe().reset_index()
        agenttype_df = (
            model.datacollector.get_agenttype_vars_dataframe(TinyAgent).reset_index()
        )
        table_df = model.datacollector.get_table_dataframe("events")
    except Exception as exc:  # pragma: no cover - runtime guard
        return _fail("collect", exc)

    payload = {
        "ok": True,
        "mesa_version": getattr(mesa, "__version__", None),
        "model": {
            "rows": int(len(model_df)),
            "columns": list(model_df.columns),
            "records": model_df.reset_index(drop=True).to_dict(orient="records"),
        },
        "agent": {
            "rows": int(len(agent_df)),
            "columns": list(agent_df.columns),
            "records": agent_df.to_dict(orient="records"),
        },
        "agenttype": {
            "rows": int(len(agenttype_df)),
            "columns": list(agenttype_df.columns),
            "records": agenttype_df.to_dict(orient="records"),
        },
        "table": {
            "rows": int(len(table_df)),
            "columns": list(table_df.columns),
            "records": table_df.to_dict(orient="records"),
        },
    }

    print(json.dumps(payload, indent=2, sort_keys=True, default=_json_default))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
