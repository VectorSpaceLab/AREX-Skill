#!/usr/bin/env python3
"""Build a bounded lerobot-eval command without executing it."""
from __future__ import annotations

import argparse
import shlex
import shutil
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", required=True, help="local policy directory or approved Hub identifier")
    parser.add_argument("--env", required=True, help="registered environment type")
    parser.add_argument("--device", default="cpu", help="cpu, cuda[:N], mps, or xpu")
    parser.add_argument("--episodes", type=int, default=2)
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--async-envs", action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument("--recording", action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument("--recording-repo-id", help="approved Hub repo for recordings")
    parser.add_argument("--trust-remote-code", action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument("--output-dir", default="outputs/eval/policy_smoke")
    args = parser.parse_args()
    if args.episodes < 1:
        parser.error("--episodes must be >= 1")
    if args.batch_size < 1:
        parser.error("--batch-size must be >= 1")
    if args.recording_repo_id and not args.recording:
        parser.error("--recording-repo-id requires --recording")
    command = [
        "lerobot-eval",
        f"--policy.path={args.checkpoint}",
        f"--env.type={args.env}",
        f"--policy.device={args.device}",
        f"--eval.n_episodes={args.episodes}",
        f"--eval.batch_size={args.batch_size}",
        f"--eval.use_async_envs={'true' if args.async_envs else 'false'}",
        f"--eval.recording={'true' if args.recording else 'false'}",
        f"--trust_remote_code={'true' if args.trust_remote_code else 'false'}",
        f"--output_dir={args.output_dir}",
    ]
    if args.recording_repo_id:
        command.append(f"--eval.recording_repo_id={args.recording_repo_id}")
    print("Command (not executed):")
    print(shlex.join(command))
    print("\nValidation:")
    print("- bounded episode count and conservative synchronous vector-env defaults selected")
    print("- checkpoint must contain config/weights plus matching policy processor files")
    print("- environment owner must verify action/observation feature contract")
    print(f"- requested device {args.device!r} must be probed in the target environment")
    if args.recording:
        print("- recording is enabled: approve local writes and any Hub upload separately")
    else:
        print("- recording is disabled for this smoke")
    if args.trust_remote_code:
        print("- remote code consent is enabled: review the environment source before launch")
    else:
        print("- remote code consent is disabled")
    if shutil.which("lerobot-eval") is None:
        print("- note: lerobot-eval is not on PATH; install/activate the intended LeRobot environment")
    print("\nThis script never launches evaluation, environments, downloads, or hardware.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
