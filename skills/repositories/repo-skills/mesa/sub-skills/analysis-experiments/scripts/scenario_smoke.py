#!/usr/bin/env python3
"""Installed-package smoke test for Mesa experimental scenarios.

Runs a tiny sequential scenario sweep with one successful run and one planned
failure. Prints JSON covering Scenario metadata, run_scenarios status, store
success/failure partitions, and failure-origin reporting.
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
        import pandas as pd
        from mesa import Agent, Model
        from mesa.experimental.scenarios import (
            RunConfiguration,
            Scenario,
            ScenarioFailedException,
            run_scenarios,
        )
        from mesa.experimental.scenarios.store import RunId
    except Exception as exc:  # pragma: no cover - import guard
        return _fail("import", exc)

    class TinyScenario(Scenario):
        n_agents: int = 3
        start_value: int = 0
        should_fail: bool = False

    class TinyAgent(Agent):
        def __init__(self, model: Model, value: int):
            super().__init__(model)
            self.value = value

        def step(self) -> None:
            self.value += 1

    class TinyModel(Model):
        def __init__(self, scenario=TinyScenario):
            super().__init__(scenario=scenario)
            TinyAgent.create_agents(
                self,
                scenario.n_agents,
                [scenario.start_value + i for i in range(scenario.n_agents)],
            )

        def total_value(self) -> int:
            return sum(agent.value for agent in self.agents)

        def step(self) -> None:
            self.agents.do("step")

    class TinyRunConfiguration(RunConfiguration):
        def run_model(self, model: Model) -> None:
            if model.scenario.should_fail:
                raise RuntimeError("planned failure for scenario smoke test")
            model.run_until(self.until)

        def extract_output(self, model: Model) -> dict[str, pd.DataFrame]:
            return {
                "summary": pd.DataFrame(
                    [
                        {
                            "time": model.time,
                            "agent_count": len(model.agents),
                            "total_value": model.total_value(),
                        }
                    ]
                )
            }

    try:
        scenarios = [
            TinyScenario(rng=42, scenario_id=0, should_fail=False),
            TinyScenario(rng=43, scenario_id=1, should_fail=True),
        ]

        store = run_scenarios(
            scenarios,
            TinyRunConfiguration(TinyModel, until=3),
            progress=False,
        )

        status_df = store.status().reset_index()
        success_id = RunId(scenarios[0].scenario_id, scenarios[0].replication_id)
        failure_id = RunId(scenarios[1].scenario_id, scenarios[1].replication_id)

        success_output = store.retrieve_output(success_id)["summary"].to_dict(
            orient="records"
        )

        failure_exception = None
        try:
            store.retrieve_output(failure_id)
        except ScenarioFailedException as exc:
            failure_exception = {
                "type": type(exc).__name__,
                "message": str(exc),
                "origin": exc.failure.origin.value if exc.failure else None,
                "exception_type": exc.failure.exception_type if exc.failure else None,
            }
    except Exception as exc:  # pragma: no cover - runtime guard
        return _fail("run", exc)

    def scenario_summary(scenario: Scenario) -> dict[str, Any]:
        return {
            "scenario_id": scenario.scenario_id,
            "replication_id": scenario.replication_id,
            "n_agents": scenario.n_agents,
            "start_value": scenario.start_value,
            "should_fail": scenario.should_fail,
            "seed_sequence_entropy": scenario.seed_sequence.entropy,
            "seed_sequence_spawn_key": list(scenario.seed_sequence.spawn_key),
            "stdlib_seed": scenario._stdlib_seed,
        }

    payload = {
        "ok": True,
        "mesa_version": getattr(mesa, "__version__", None),
        "scenarios": [scenario_summary(scenario) for scenario in scenarios],
        "status": status_df.to_dict(orient="records"),
        "succeeded": [
            {
                "scenario_id": run_id.scenario_id,
                "replication_id": run_id.replication_id,
                "rows": int(len(record.output["summary"])),
            }
            for run_id, record in store.succeeded().items()
        ],
        "failed": [
            {
                "scenario_id": run_id.scenario_id,
                "replication_id": run_id.replication_id,
                "origin": record.failure.origin.value if record.failure else None,
                "exception_type": record.failure.exception_type if record.failure else None,
                "message": record.failure.message if record.failure else None,
            }
            for run_id, record in store.failed().items()
        ],
        "pending_count": int(len(store.pending())),
        "aborted_count": int(len(store.aborted())),
        "success_output": success_output,
        "failure_exception": failure_exception,
    }

    print(json.dumps(payload, indent=2, sort_keys=True, default=_json_default))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
