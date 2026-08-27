#!/usr/bin/env python3
"""
Standalone MiroFish-compatible action JSONL helper.

The helper preserves the runtime action-log shape used by MiroFish OASIS
launchers while avoiding any dependency on Flask, OASIS, Zep, or repository
imports. Use it to create tiny fixtures or to verify that a local filesystem can
write and parse platform `actions.jsonl` files.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, Optional


class PlatformActionLogger:
    """Write action/event rows for one platform under `<base_dir>/<platform>/`."""

    def __init__(self, platform: str, base_dir: str | os.PathLike[str]):
        if platform not in {"twitter", "reddit"}:
            raise ValueError("platform must be 'twitter' or 'reddit'")
        self.platform = platform
        self.base_dir = Path(base_dir)
        self.log_dir = self.base_dir / platform
        self.log_path = self.log_dir / "actions.jsonl"
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def _write(self, entry: Dict[str, Any]) -> None:
        with self.log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def log_action(
        self,
        round_num: int,
        agent_id: int,
        agent_name: str,
        action_type: str,
        action_args: Optional[Dict[str, Any]] = None,
        result: Optional[str] = None,
        success: bool = True,
    ) -> None:
        """Append a standard agent action row."""
        self._write(
            {
                "round": round_num,
                "timestamp": datetime.now().isoformat(),
                "agent_id": agent_id,
                "agent_name": agent_name,
                "action_type": action_type,
                "action_args": action_args or {},
                "result": result,
                "success": success,
            }
        )

    def log_round_start(self, round_num: int, simulated_hour: int) -> None:
        self._write(
            {
                "round": round_num,
                "timestamp": datetime.now().isoformat(),
                "event_type": "round_start",
                "simulated_hour": simulated_hour,
            }
        )

    def log_round_end(
        self, round_num: int, actions_count: int, simulated_hours: Optional[int] = None
    ) -> None:
        entry = {
            "round": round_num,
            "timestamp": datetime.now().isoformat(),
            "event_type": "round_end",
            "actions_count": actions_count,
        }
        if simulated_hours is not None:
            entry["simulated_hours"] = simulated_hours
        self._write(entry)

    def log_simulation_start(self, config: Dict[str, Any]) -> None:
        time_config = config.get("time_config", {}) if isinstance(config, dict) else {}
        self._write(
            {
                "timestamp": datetime.now().isoformat(),
                "event_type": "simulation_start",
                "platform": self.platform,
                "total_rounds": time_config.get("total_simulation_hours", 72) * 2,
                "agents_count": len(config.get("agent_configs", []))
                if isinstance(config, dict)
                else 0,
            }
        )

    def log_simulation_end(self, total_rounds: int, total_actions: int) -> None:
        self._write(
            {
                "timestamp": datetime.now().isoformat(),
                "event_type": "simulation_end",
                "platform": self.platform,
                "total_rounds": total_rounds,
                "total_actions": total_actions,
            }
        )


class SimulationLogManager:
    """Manage a main simulation log plus lazy per-platform action loggers."""

    def __init__(self, simulation_dir: str | os.PathLike[str]):
        self.simulation_dir = Path(simulation_dir)
        self.simulation_dir.mkdir(parents=True, exist_ok=True)
        self.twitter_logger: Optional[PlatformActionLogger] = None
        self.reddit_logger: Optional[PlatformActionLogger] = None
        self._main_logger = self._setup_main_logger()

    def _setup_main_logger(self) -> logging.Logger:
        logger = logging.getLogger(f"mirofish_simulation_fixture.{id(self)}")
        logger.setLevel(logging.INFO)
        logger.handlers.clear()
        logger.propagate = False

        handler = logging.FileHandler(
            self.simulation_dir / "simulation.log", encoding="utf-8", mode="w"
        )
        handler.setLevel(logging.INFO)
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s - %(levelname)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        logger.addHandler(handler)
        return logger

    def get_twitter_logger(self) -> PlatformActionLogger:
        if self.twitter_logger is None:
            self.twitter_logger = PlatformActionLogger("twitter", self.simulation_dir)
        return self.twitter_logger

    def get_reddit_logger(self) -> PlatformActionLogger:
        if self.reddit_logger is None:
            self.reddit_logger = PlatformActionLogger("reddit", self.simulation_dir)
        return self.reddit_logger

    def log(self, message: str, level: str = "info") -> None:
        method = getattr(self._main_logger, level.lower(), self._main_logger.info)
        method(message)

    def info(self, message: str) -> None:
        self.log(message, "info")

    def warning(self, message: str) -> None:
        self.log(message, "warning")

    def error(self, message: str) -> None:
        self.log(message, "error")


class ActionLogger:
    """Compatibility writer for the legacy single-file `actions.jsonl` shape."""

    def __init__(self, log_path: str | os.PathLike[str]):
        self.log_path = Path(log_path)
        if self.log_path.parent != Path(""):
            self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def _write(self, entry: Dict[str, Any]) -> None:
        with self.log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def log_action(
        self,
        round_num: int,
        platform: str,
        agent_id: int,
        agent_name: str,
        action_type: str,
        action_args: Optional[Dict[str, Any]] = None,
        result: Optional[str] = None,
        success: bool = True,
    ) -> None:
        self._write(
            {
                "round": round_num,
                "timestamp": datetime.now().isoformat(),
                "platform": platform,
                "agent_id": agent_id,
                "agent_name": agent_name,
                "action_type": action_type,
                "action_args": action_args or {},
                "result": result,
                "success": success,
            }
        )

    def log_round_start(self, round_num: int, simulated_hour: int, platform: str) -> None:
        self._write(
            {
                "round": round_num,
                "timestamp": datetime.now().isoformat(),
                "platform": platform,
                "event_type": "round_start",
                "simulated_hour": simulated_hour,
            }
        )

    def log_round_end(self, round_num: int, actions_count: int, platform: str) -> None:
        self._write(
            {
                "round": round_num,
                "timestamp": datetime.now().isoformat(),
                "platform": platform,
                "event_type": "round_end",
                "actions_count": actions_count,
            }
        )

    def log_simulation_start(self, platform: str, config: Dict[str, Any]) -> None:
        time_config = config.get("time_config", {}) if isinstance(config, dict) else {}
        self._write(
            {
                "timestamp": datetime.now().isoformat(),
                "platform": platform,
                "event_type": "simulation_start",
                "total_rounds": time_config.get("total_simulation_hours", 72) * 2,
                "agents_count": len(config.get("agent_configs", []))
                if isinstance(config, dict)
                else 0,
            }
        )

    def log_simulation_end(self, platform: str, total_rounds: int, total_actions: int) -> None:
        self._write(
            {
                "timestamp": datetime.now().isoformat(),
                "platform": platform,
                "event_type": "simulation_end",
                "total_rounds": total_rounds,
                "total_actions": total_actions,
            }
        )


def iter_jsonl(path: str | os.PathLike[str]) -> Iterable[Dict[str, Any]]:
    """Yield parsed JSON objects from a JSONL file, ignoring blank lines."""
    with Path(path).open("r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if stripped:
                yield json.loads(stripped)


def _parse_action_args(text: Optional[str]) -> Dict[str, Any]:
    if not text:
        return {}
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as error:
        raise argparse.ArgumentTypeError(f"invalid JSON object: {error}") from error
    if not isinstance(parsed, dict):
        raise argparse.ArgumentTypeError("action args must decode to a JSON object")
    return parsed


def _self_test() -> None:
    with tempfile.TemporaryDirectory(prefix="mirofish-action-logger-") as tmp:
        manager = SimulationLogManager(tmp)
        twitter = manager.get_twitter_logger()
        config = {
            "time_config": {"total_simulation_hours": 1},
            "agent_configs": [{"agent_id": 0}],
        }
        twitter.log_simulation_start(config)
        twitter.log_round_start(round_num=1, simulated_hour=0)
        twitter.log_action(
            round_num=1,
            agent_id=0,
            agent_name="Fixture Agent",
            action_type="CREATE_POST",
            action_args={"content": "hello"},
            result="ok",
        )
        twitter.log_round_end(round_num=1, actions_count=1, simulated_hours=1)
        twitter.log_simulation_end(total_rounds=1, total_actions=1)
        manager.info("fixture run complete")

        action_path = Path(tmp) / "twitter" / "actions.jsonl"
        rows = list(iter_jsonl(action_path))
        assert rows[0]["event_type"] == "simulation_start"
        assert rows[2]["agent_id"] == 0
        assert rows[2]["action_type"] == "CREATE_POST"
        assert rows[-1]["event_type"] == "simulation_end"
        assert (Path(tmp) / "simulation.log").read_text(encoding="utf-8")
        print(f"self-test ok: wrote {len(rows)} rows under a temporary directory")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Write a small MiroFish-compatible platform actions.jsonl row."
    )
    parser.add_argument("--self-test", action="store_true", help="run a temp-file smoke check and exit")
    parser.add_argument("--simulation-dir", help="simulation directory to write under")
    parser.add_argument("--platform", choices=["twitter", "reddit"], default="twitter")
    parser.add_argument(
        "--event",
        choices=["action", "round-start", "round-end", "simulation-start", "simulation-end"],
        default="action",
        help="row type to write",
    )
    parser.add_argument("--round", dest="round_num", type=int, default=1, help="round number")
    parser.add_argument("--simulated-hour", type=int, default=0, help="simulated hour for round-start")
    parser.add_argument("--actions-count", type=int, default=1, help="round-end action count")
    parser.add_argument("--total-rounds", type=int, default=1, help="simulation-end total rounds")
    parser.add_argument("--total-actions", type=int, default=1, help="simulation-end total actions")
    parser.add_argument("--agent-id", type=int, default=0)
    parser.add_argument("--agent-name", default="Fixture Agent")
    parser.add_argument("--action-type", default="CREATE_POST")
    parser.add_argument(
        "--action-args",
        type=_parse_action_args,
        default={},
        help='JSON object for action_args, for example \'{"content":"hello"}\'',
    )
    parser.add_argument("--result", default=None)
    parser.add_argument("--failure", action="store_true", help="write success=false for action rows")
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.self_test:
        _self_test()
        return 0

    if not args.simulation_dir:
        parser.error("--simulation-dir is required unless --self-test is used")

    logger = PlatformActionLogger(args.platform, args.simulation_dir)
    if args.event == "action":
        logger.log_action(
            round_num=args.round_num,
            agent_id=args.agent_id,
            agent_name=args.agent_name,
            action_type=args.action_type,
            action_args=args.action_args,
            result=args.result,
            success=not args.failure,
        )
    elif args.event == "round-start":
        logger.log_round_start(args.round_num, args.simulated_hour)
    elif args.event == "round-end":
        logger.log_round_end(args.round_num, args.actions_count)
    elif args.event == "simulation-start":
        logger.log_simulation_start(
            {
                "time_config": {"total_simulation_hours": max(args.total_rounds // 2, 1)},
                "agent_configs": [{} for _ in range(max(args.agent_id + 1, 1))],
            }
        )
    elif args.event == "simulation-end":
        logger.log_simulation_end(args.total_rounds, args.total_actions)
    else:  # pragma: no cover - argparse constrains this
        parser.error(f"unsupported event: {args.event}")

    print(str(logger.log_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
