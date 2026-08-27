#!/usr/bin/env python3
"""Smoke-test Mesa core modeling, activation, and scheduling APIs."""

from __future__ import annotations

import argparse
import json
import sys

import mesa
from mesa.time import Priority, Schedule


class CounterAgent(mesa.Agent):
    def __init__(self, model, tag):
        super().__init__(model)
        self.tag = int(tag)
        self.step_calls = 0

    def step(self):
        self.step_calls += 1


class SmokeModel(mesa.Model):
    def __init__(self, n_agents: int, steps: int, rng=None):
        super().__init__(rng=rng)
        self.step_calls = 0
        self.one_off_calls = 0
        self.recurring_calls = 0
        self.removal_event_calls = 0
        self.removals = 0

        self.expected_tags = [int(self.rng.integers(0, 10_000)) for _ in range(n_agents)]
        created = CounterAgent.create_agents(self, n_agents, tag=self.expected_tags)

        if len(created) != n_agents:
            raise RuntimeError(f"expected {n_agents} agents, created {len(created)}")

        created_tags = [agent.tag for agent in created.to_list()]
        if created_tags != self.expected_tags:
            raise RuntimeError("create_agents did not assign per-agent values correctly")

        self.victim = self.agents.to_list()[0] if len(self.agents) else None

        self.schedule_event(
            self._remove_victim,
            after=0.25,
            priority=Priority.HIGH,
        )
        self.schedule_event(self._one_off, at=0.5)
        self.schedule_recurring(
            self._recurring_tick,
            Schedule(interval=1.0, start=1.0, count=steps),
        )

    def _remove_victim(self):
        self.removal_event_calls += 1
        if self.victim is not None and self.victim in self.agents:
            self.victim.remove()
            self.removals += 1

    def _one_off(self):
        self.one_off_calls += 1

    def _recurring_tick(self):
        self.recurring_calls += 1

    def step(self):
        self.step_calls += 1
        self.agents.shuffle_do("step")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Smoke-test Mesa model, agent, AgentSet, and event scheduling behavior.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--agents", type=int, default=5, help="Number of agents to create.")
    parser.add_argument("--steps", type=int, default=3, help="Number of simulated time units to run.")
    parser.add_argument("--seed", type=int, default=42, help="Seed passed to mesa.Model(rng=...).")
    args = parser.parse_args(argv)

    if args.agents < 0:
        parser.error("--agents must be >= 0")
    if args.steps < 1:
        parser.error("--steps must be >= 1")

    return args


def validate_model(
    model: SmokeModel, requested_agents: int, requested_steps: int, seed: int
) -> dict[str, object]:
    expected_removed = 1 if requested_agents > 0 else 0
    expected_remaining = requested_agents - expected_removed

    if model.time != float(requested_steps):
        raise SystemExit(f"expected model.time={requested_steps!r}, got {model.time!r}")
    if model.step_calls != requested_steps:
        raise SystemExit(f"expected {requested_steps} model step calls, got {model.step_calls}")
    if model.recurring_calls != requested_steps:
        raise SystemExit(
            f"expected {requested_steps} recurring calls, got {model.recurring_calls}"
        )
    if model.one_off_calls != 1:
        raise SystemExit(f"expected one one-off event, got {model.one_off_calls}")
    if model.removal_event_calls != 1:
        raise SystemExit(
            f"expected one removal event, got {model.removal_event_calls}"
        )
    if model.removals != expected_removed:
        raise SystemExit(f"expected {expected_removed} removals, got {model.removals}")
    if len(model.agents) != expected_remaining:
        raise SystemExit(
            f"expected {expected_remaining} live agents, got {len(model.agents)}"
        )

    typed = model.agents_by_type.get(CounterAgent)
    if requested_agents == 0:
        if typed is not None:
            raise SystemExit("expected no CounterAgent registry for an empty model")
    else:
        if typed is None:
            raise SystemExit("CounterAgent registry was not created")
        if len(typed) != expected_remaining:
            raise SystemExit(
                f"expected {expected_remaining} CounterAgent entries, got {len(typed)}"
            )

    survivor_tags = [agent.tag for agent in model.agents.to_list()]
    expected_survivor_tags = model.expected_tags[expected_removed:]
    if survivor_tags != expected_survivor_tags:
        raise SystemExit(
            "survivor tags do not match expected sequence from create_agents"
        )

    survivor_step_calls = [agent.step_calls for agent in model.agents.to_list()]
    if any(count != requested_steps for count in survivor_step_calls):
        raise SystemExit(
            "surviving agents did not receive the expected number of step calls"
        )

    return {
        "mesa_version": getattr(mesa, "__version__", "unknown"),
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "requested_agents": requested_agents,
        "requested_steps": requested_steps,
        "model_time": model.time,
        "model_step_calls": model.step_calls,
        "one_off_calls": model.one_off_calls,
        "recurring_calls": model.recurring_calls,
        "removal_event_calls": model.removal_event_calls,
        "removals": model.removals,
        "remaining_agents": len(model.agents),
        "agent_types": [cls.__name__ for cls in model.agent_types],
        "survivor_tags": survivor_tags,
        "survivor_step_calls": survivor_step_calls,
        "seed": seed,
    }


def main(argv: list[str] | None = None) -> int:
    if sys.version_info < (3, 12):
        raise SystemExit("Python 3.12 or newer is required.")

    args = parse_args(sys.argv[1:] if argv is None else argv)
    model = SmokeModel(args.agents, args.steps, rng=args.seed)
    model.run_for(args.steps)

    payload = validate_model(model, args.agents, args.steps, args.seed)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
