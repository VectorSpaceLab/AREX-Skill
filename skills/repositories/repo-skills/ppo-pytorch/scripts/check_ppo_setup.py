#!/usr/bin/env python3
"""Safe PPO-PyTorch setup check.

This helper verifies that the bundled PPO core module imports, reports the
shared class signatures, and can optionally inspect a trusted checkpoint state
for shape hints. It does not run Gym rollouts.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Optional

import torch

from ppo_core import DEVICE, ActorCritic, PPO, RolloutBuffer


@dataclass
class SetupReport:
    torch_version: str
    cuda_available: bool
    device: str
    rollouts: str
    actor_critic_signature: str
    ppo_signature: str
    checkpoint_path: Optional[str] = None
    checkpoint_exists: Optional[bool] = None
    checkpoint_summary: Optional[Dict[str, Any]] = None


def _inspect_checkpoint(path: Path) -> Dict[str, Any]:
    try:
        state = torch.load(path, map_location=lambda storage, loc: storage, weights_only=False)
    except TypeError:
        state = torch.load(path, map_location=lambda storage, loc: storage)
    if not isinstance(state, dict):
        return {"path": str(path), "type": type(state).__name__}

    summary: Dict[str, Any] = {"path": str(path), "key_count": len(state), "keys": sorted(state.keys())[:12]}
    actor0 = state.get("actor.0.weight")
    actor4 = state.get("actor.4.weight")
    critic0 = state.get("critic.0.weight")
    if actor0 is not None:
        summary["state_dim"] = int(actor0.shape[1])
    if actor4 is not None:
        summary["action_dim"] = int(actor4.shape[0])
    if critic0 is not None:
        summary["critic_state_dim"] = int(critic0.shape[1])
    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a safe PPO-PyTorch setup check.")
    parser.add_argument("--checkpoint-path", help="Trusted checkpoint path to inspect with torch.load.")
    parser.add_argument("--json", action="store_true", help="Emit JSON only.")
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    report = SetupReport(
        torch_version=torch.__version__,
        cuda_available=torch.cuda.is_available(),
        device=str(DEVICE),
        rollouts=RolloutBuffer.__name__,
        actor_critic_signature="(state_dim, action_dim, has_continuous_action_space, action_std_init)",
        ppo_signature="(state_dim, action_dim, lr_actor, lr_critic, gamma, K_epochs, eps_clip, has_continuous_action_space, action_std_init=0.6)",
    )

    if args.checkpoint_path:
        path = Path(args.checkpoint_path)
        report.checkpoint_path = str(path)
        report.checkpoint_exists = path.is_file()
        if path.is_file():
            report.checkpoint_summary = _inspect_checkpoint(path)

    payload = asdict(report)
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print("PPO-PyTorch setup check")
        print("=" * 79)
        print(f"torch_version: {report.torch_version}")
        print(f"cuda_available: {report.cuda_available}")
        print(f"device: {report.device}")
        print(f"rollout_buffer: {report.rollouts}")
        print(f"actor_critic_signature: {report.actor_critic_signature}")
        print(f"ppo_signature: {report.ppo_signature}")
        if report.checkpoint_path:
            print(f"checkpoint_path: {report.checkpoint_path}")
            print(f"checkpoint_exists: {report.checkpoint_exists}")
        if report.checkpoint_summary is not None:
            print("checkpoint_summary:")
            for key, value in report.checkpoint_summary.items():
                print(f"  {key}: {value}")
        print("=" * 79)
        print("This helper does not run training or evaluation rollouts.")

    if args.checkpoint_path and not report.checkpoint_exists:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
