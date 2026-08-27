#!/usr/bin/env python3
"""Smoke-test a pre-built SMARTS scenario with a bounded headless run.

Prerequisites: install the SMARTS package (and its core runtime dependencies)
into the Python interpreter used to run this script, and provide a generated
scenario directory compatible with that installation.  The helper never builds
scenario assets, installs packages, starts services, uses the network, or
assumes the current working directory is a source checkout.

Example::

    python /path/to/smoke_env.py --scenario /data/scenarios/straight

Use ``--self-test`` to exercise the parser and active-agent lifecycle logic
without importing SMARTS or requiring a scenario.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any


class _LifecycleFailure(Exception):
    """Carry a user-facing lifecycle stage and its original exception."""

    def __init__(self, stage: str, error: Exception) -> None:
        super().__init__(str(error))
        self.stage = stage
        self.error = error


def _positive_int(value: str) -> int:
    """Parse a strictly positive integer for an argparse option."""
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be an integer") from exc
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return parsed


def _build_parser(*, require_scenario: bool = True) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run a bounded, headless SMARTS HiWayEnvV1 smoke on a "
            "pre-built scenario."
        )
    )
    parser.add_argument(
        "--scenario",
        required=require_scenario,
        help="Path to an existing generated SMARTS scenario directory.",
    )
    parser.add_argument(
        "--max-steps",
        type=_positive_int,
        default=8,
        help="Maximum number of step calls (default: 8; must be positive).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="SMARTS/Gymnasium seed (default: 42).",
    )
    parser.add_argument(
        "--agent-id",
        default="ego",
        help="Configured agent id (default: ego).",
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Check parser and lifecycle logic without importing SMARTS.",
    )
    return parser


def _active_agent_ids(observations: Any) -> list[str]:
    if not isinstance(observations, Mapping):
        raise TypeError(
            "expected reset/step observations to be a mapping of active agent ids"
        )
    return list(observations)


def _sample_actions(env: Any, observations: Mapping[str, Any]) -> dict[str, Any]:
    """Sample actions only for ids present in the current observation mapping."""
    actions: dict[str, Any] = {}
    for agent_id in observations:
        try:
            space = env.action_space[agent_id]
        except Exception as exc:
            raise KeyError(
                f"active agent {agent_id!r} has no matching action space"
            ) from exc
        actions[agent_id] = space.sample()
    return actions


def _all_done(statuses: Any, name: str) -> bool:
    if not isinstance(statuses, Mapping):
        raise TypeError(f"{name} must be a mapping containing the __all__ flag")
    return bool(statuses.get("__all__", False))


def _run_lifecycle(env: Any, *, max_steps: int, seed: int, label: str) -> int:
    """Run reset and active-only steps, raising a labelled failure on errors."""
    try:
        observations, _infos = env.reset(seed=seed)
    except Exception as exc:
        raise _LifecycleFailure("reset", exc) from exc

    try:
        active_ids = _active_agent_ids(observations)
    except Exception as exc:
        raise _LifecycleFailure("reset result", exc) from exc
    print(f"reset scenario={label} active_agents={active_ids}")

    steps = 0
    for step_number in range(1, max_steps + 1):
        try:
            actions = _sample_actions(env, observations)
        except Exception as exc:
            raise _LifecycleFailure("action sampling", exc) from exc

        try:
            observations, rewards, terminateds, truncateds, _infos = env.step(actions)
        except Exception as exc:
            raise _LifecycleFailure("step", exc) from exc

        steps = step_number
        try:
            active_ids = _active_agent_ids(observations)
            terminated_all = _all_done(terminateds, "terminateds")
            truncated_all = _all_done(truncateds, "truncateds")
            reward_keys = list(rewards) if isinstance(rewards, Mapping) else []
        except Exception as exc:
            raise _LifecycleFailure("step result", exc) from exc
        print(
            f"step={steps} active_agents={active_ids} reward_keys={reward_keys} "
            f"terminated_all={terminated_all} truncated_all={truncated_all}"
        )
        if terminated_all or truncated_all:
            break

    print(f"smoke passed steps={steps} scenario={label}")
    return steps


def _error_detail(error: Exception) -> str:
    detail = str(error).strip()
    return f"{type(error).__name__}: {detail}" if detail else type(error).__name__


def _report_failure(stage: str, error: Exception) -> None:
    guidance = {
        "import": "install SMARTS in this interpreter and verify `python -m pip show smarts`",
        "invalid scenario": "pass an existing generated scenario directory",
        "construction": "check the installed SMARTS version and the Laner interface configuration",
        "reset": "verify the scenario contains generated map and traffic artifacts",
        "reset result": "check the installed SMARTS reset return contract",
        "action sampling": "inspect the configured agent id and formatted action space",
        "step": "check scenario compatibility, mission placement, and SMARTS step diagnostics",
        "step result": "check the installed SMARTS five-value step return contract",
        "close": "inspect SMARTS cleanup diagnostics for resources that may remain open",
    }.get(stage, "inspect the original exception and installed SMARTS configuration")
    print(
        f"smoke_env: {stage} failed: {_error_detail(error)}; {guidance}",
        file=sys.stderr,
    )


class _SelfTestSpace:
    def sample(self) -> int:
        return 0


class _SelfTestEnv:
    def __init__(self) -> None:
        self.action_space = {"ego": _SelfTestSpace()}
        self.actions_seen: list[dict[str, Any]] = []
        self.closed = False

    def reset(self, *, seed: int) -> tuple[dict[str, str], dict[str, Any]]:
        assert seed == 42
        return {"ego": "observation"}, {}

    def step(
        self, actions: dict[str, Any]
    ) -> tuple[dict[str, Any], dict[str, float], dict[str, bool], dict[str, bool], dict[str, Any]]:
        self.actions_seen.append(dict(actions))
        if len(self.actions_seen) == 1:
            assert set(actions) == {"ego"}
            return {}, {}, {"__all__": False}, {"__all__": False}, {}
        assert len(self.actions_seen) == 2
        assert actions == {}
        return {}, {}, {"__all__": True}, {"__all__": False}, {}

    def close(self) -> None:
        self.closed = True


def _self_test() -> int:
    """Exercise parser defaults and the active-agent/done lifecycle offline."""
    try:
        args = _build_parser(require_scenario=False).parse_args(["--self-test"])
        assert args.self_test is True
        assert args.max_steps == 8
        assert args.seed == 42
        assert args.agent_id == "ego"

        env = _SelfTestEnv()
        try:
            steps = _run_lifecycle(env, max_steps=2, seed=42, label="<self-test>")
        finally:
            env.close()
        assert steps == 2
        assert env.closed
        assert [set(actions) for actions in env.actions_seen] == [{"ego"}, set()]
    except Exception as exc:
        _report_failure("self-test", exc)
        return 1
    print("self-test passed")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    raw_args = list(sys.argv[1:] if argv is None else argv)
    parser = _build_parser(require_scenario="--self-test" not in raw_args)
    args = parser.parse_args(raw_args)
    if args.self_test:
        return _self_test()

    try:
        scenario = Path(args.scenario).expanduser()
        if not scenario.is_dir():
            raise ValueError(f"{scenario} is not an existing directory")
        scenario = scenario.resolve()
    except Exception as exc:
        _report_failure("invalid scenario", exc)
        return 1

    try:
        from smarts.core.agent_interface import AgentInterface, AgentType
        from smarts.env.gymnasium.hiway_env_v1 import HiWayEnvV1
    except Exception as exc:
        _report_failure("import", exc)
        return 1

    env: Any | None = None
    status = 1
    try:
        try:
            interface = AgentInterface.from_type(
                AgentType.Laner, max_episode_steps=args.max_steps
            )
            env = HiWayEnvV1(
                scenarios=[str(scenario)],
                agent_interfaces={args.agent_id: interface},
                headless=True,
                seed=args.seed,
            )
        except Exception as exc:
            _report_failure("construction", exc)
        else:
            try:
                _run_lifecycle(
                    env,
                    max_steps=args.max_steps,
                    seed=args.seed,
                    label=str(scenario),
                )
            except _LifecycleFailure as failure:
                _report_failure(failure.stage, failure.error)
            else:
                status = 0
    finally:
        if env is not None:
            try:
                env.close()
            except Exception as exc:
                _report_failure("close", exc)
                status = 1
    return status


if __name__ == "__main__":
    raise SystemExit(main())
