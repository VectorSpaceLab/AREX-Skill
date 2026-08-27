#!/usr/bin/env python3
"""Smoke-test rLLM AgentFlow/Evaluator contracts without provider calls."""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from rllm import Task, Trajectory, Step, rollout, evaluator
from rllm.eval.types import EvalOutput
from rllm.types import AgentConfig, run_agent_flow


@rollout(name="toy")
def toy_rollout(task: Task, config: AgentConfig) -> Trajectory:  # noqa: ARG001
    return Trajectory(
        name="toy",
        steps=[Step(input=task.instruction, output="42", reward=0.0, metadata={"source": "smoke"})],
    )


@evaluator
def toy_evaluator(task: Task, episode) -> EvalOutput:
    answer = episode.trajectories[0].steps[0].output
    return EvalOutput(reward=1.0 if answer == "42" else 0.0, is_correct=answer == "42", metadata={"task_id": task.id})


async def _run() -> dict:
    task = Task(id="toy-1", instruction="What is 6 * 7?", metadata={"answer": "42"}, dataset_dir=Path("."))
    config = AgentConfig(base_url="http://example.invalid/v1", model="dummy", session_uid="smoke-session")
    episode = await run_agent_flow(toy_rollout, task, config)
    result = toy_evaluator.evaluate(task, episode)
    return {
        "episode_type": type(episode).__name__,
        "trajectory_count": len(episode.trajectories),
        "step_count": len(episode.trajectories[0].steps),
        "reward": result.reward,
        "is_correct": result.is_correct,
        "ok": result.is_correct and result.reward == 1.0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Emit JSON only")
    args = parser.parse_args()
    report = asyncio.run(_run())
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("rLLM AgentFlow/Evaluator smoke")
        for key, value in report.items():
            print(f"{key}: {value}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
