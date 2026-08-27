#!/usr/bin/env python3
"""Inspect RL Baselines3 Zoo Hub-related local layout without side effects.

This helper is deterministic and deliberately offline: it does not import
rl_zoo3, Hugging Face, W&B, Stable-Baselines3, or torch; it opens no network
connections; it reads no credentials; it loads no model weights; and it never
starts training or video recording. It only checks local file names/layout and
prints commands that a user may choose to run later.
"""

from __future__ import annotations

import argparse
import json
import re
import shlex
import sys
from pathlib import Path
from typing import Any

ALGOS = (
    "a2c",
    "ars",
    "crossq",
    "ddpg",
    "dqn",
    "ppo",
    "ppo_lstm",
    "qrdqn",
    "sac",
    "td3",
    "tqc",
    "trpo",
)


def shell_join(parts: list[str]) -> str:
    return " ".join(shlex.quote(str(part)) for part in parts)


def add_finding(report: dict[str, Any], severity: str, path: Path | None, message: str, hint: str = "") -> None:
    item = {"severity": severity, "message": message}
    if path is not None:
        item["path"] = str(path)
    if hint:
        item["hint"] = hint
    report["findings"].append(item)


def latest_run_id(folder: Path, algo: str, env: str) -> int:
    algo_dir = folder / algo
    if not algo_dir.is_dir():
        return 0
    pattern = re.compile(rf"^{re.escape(env)}_(\d+)$")
    latest = 0
    for child in algo_dir.iterdir():
        if not child.is_dir():
            continue
        match = pattern.match(child.name)
        if match:
            latest = max(latest, int(match.group(1)))
    return latest


def run_path_for_existing(folder: Path, algo: str, env: str, exp_id: int) -> tuple[Path, int]:
    """Match RL Zoo existing-model selection semantics used by enjoy/push."""
    effective = exp_id
    if exp_id == 0:
        effective = latest_run_id(folder, algo, env)
    if effective > 0:
        return folder / algo / f"{env}_{effective}", effective
    return folder / algo, effective


def run_path_for_download_target(folder: Path, algo: str, env: str, exp_id: int) -> tuple[Path, int]:
    """Match rl_zoo3.load_from_hub destination semantics."""
    effective = exp_id
    if exp_id == 0:
        effective = latest_run_id(folder, algo, env) + 1
    if effective > 0:
        return folder / algo / f"{env}_{effective}", effective
    return folder / algo, effective


def select_model_path(log_path: Path, env: str, args: argparse.Namespace, report: dict[str, Any]) -> tuple[Path, str]:
    if args.load_best:
        return log_path / "best_model.zip", "best model (--load-best)"
    if args.load_checkpoint is not None:
        return log_path / f"rl_model_{args.load_checkpoint}_steps.zip", f"checkpoint {args.load_checkpoint}"
    if args.load_last_checkpoint:
        pattern = re.compile(r"^rl_model_(\d+)_steps\.zip$")
        checkpoints: list[tuple[int, Path]] = []
        if log_path.is_dir():
            for child in log_path.iterdir():
                match = pattern.match(child.name)
                if match and child.is_file():
                    checkpoints.append((int(match.group(1)), child))
        if checkpoints:
            checkpoints.sort(key=lambda item: item[0])
            return checkpoints[-1][1], f"latest checkpoint ({checkpoints[-1][0]} steps)"
        placeholder = log_path / "rl_model_<steps>_steps.zip"
        add_finding(
            report,
            "error",
            log_path,
            "No checkpoint matching rl_model_<steps>_steps.zip was found for --load-last-checkpoint.",
            "Train with checkpoint saving enabled or choose a different selector.",
        )
        return placeholder, "latest checkpoint"
    return log_path / f"{env}.zip", "final model"


def config_mentions_normalize(config_path: Path) -> bool | None:
    if not config_path.is_file():
        return None
    try:
        text = config_path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return None
    # Conservative text heuristic; avoids a PyYAML dependency.
    for line in text.splitlines():
        stripped = line.split("#", 1)[0].strip().lower()
        if not stripped.startswith("normalize"):
            continue
        if re.search(r"normalize\s*:\s*(false|none|null|0)\b", stripped):
            return False
        if re.search(r"normalize\s*:\s*(true|1|\{|\[|dict\(|'|\")", stripped):
            return True
    return None


def require_file(report: dict[str, Any], path: Path, role: str, hint: str = "") -> bool:
    if path.is_file():
        add_finding(report, "ok", path, f"Found {role}.")
        return True
    add_finding(report, "error", path, f"Missing {role}.", hint)
    return False


def warn_file(report: dict[str, Any], path: Path, role: str, hint: str = "") -> bool:
    if path.is_file():
        add_finding(report, "ok", path, f"Found {role}.")
        return True
    add_finding(report, "warning", path, f"Missing optional {role}.", hint)
    return False


def check_push_layout(args: argparse.Namespace, report: dict[str, Any]) -> None:
    folder = Path(args.folder)
    log_path, effective_exp_id = run_path_for_existing(folder, args.algo, args.env, args.exp_id)
    model_path, selector_label = select_model_path(log_path, args.env, args, report)
    stats_dir = log_path / args.env
    config_path = stats_dir / "config.yml"
    args_path = stats_dir / "args.yml"
    env_kwargs_path = stats_dir / "env_kwargs.yml"
    vecnormalize_path = stats_dir / "vecnormalize.pkl"

    report["derived"]["push"] = {
        "effectiveExpId": effective_exp_id,
        "logPath": str(log_path),
        "selector": selector_label,
        "selectedModelPath": str(model_path),
        "hubModelFilename": f"{args.algo}-{args.env}.zip",
        "repoId": f"{args.organization}/{args.repo_name or f'{args.algo}-{args.env}'}",
    }

    if log_path.is_dir():
        add_finding(report, "ok", log_path, "Found selected RL Zoo run folder.")
    else:
        add_finding(
            report,
            "error",
            log_path,
            "Selected RL Zoo run folder is missing.",
            "Create/train/download the model first or choose a different --folder/--exp-id.",
        )

    require_file(report, model_path, f"selected {selector_label} zip", "Use the training or evaluation sub-skill to locate/create this artifact.")
    if stats_dir.is_dir():
        add_finding(report, "ok", stats_dir, "Found environment metadata subfolder.")
    else:
        add_finding(
            report,
            "error",
            stats_dir,
            "Missing environment metadata subfolder.",
            "Hub upload packaging expects saved args/config under <run>/<env>/.",
        )

    require_file(report, args_path, "saved args.yml", "Recreate artifacts from a proper RL Zoo training/download run.")
    require_file(report, config_path, "saved config.yml", "Recreate artifacts from a proper RL Zoo training/download run.")
    warn_file(report, env_kwargs_path, "env_kwargs.yml", "Upload can regenerate env kwargs, but an explicit file makes staging easier to audit.")

    normalize_state = config_mentions_normalize(config_path)
    if args.expect_vecnormalize == "yes" or (args.expect_vecnormalize == "auto" and normalize_state is True):
        require_file(
            report,
            vecnormalize_path,
            "VecNormalize stats vecnormalize.pkl",
            "The saved config appears to require normalization stats.",
        )
    elif args.expect_vecnormalize == "no":
        if vecnormalize_path.is_file():
            add_finding(report, "warning", vecnormalize_path, "VecNormalize stats exist although --expect-vecnormalize no was passed.")
    else:
        warn_file(report, vecnormalize_path, "VecNormalize stats vecnormalize.pkl", "Safe to omit only when the model was not normalized.")

    metrics = list(log_path.glob("*.csv")) + list(log_path.glob("*.monitor.csv"))
    if (log_path / "evaluations.npz").is_file():
        metrics.append(log_path / "evaluations.npz")
    if metrics:
        add_finding(report, "ok", log_path, f"Found {len(metrics)} metrics file(s) that can be packaged.")
    else:
        add_finding(report, "warning", log_path, "No evaluation/monitor metrics were found to package into train_eval_metrics.zip.")

    command = [
        "python",
        "-m",
        "rl_zoo3.push_to_hub",
        "--algo",
        args.algo,
        "--env",
        args.env,
        "-f",
        args.folder,
        "--exp-id",
        str(args.exp_id),
        "-orga",
        args.organization,
    ]
    if args.repo_name:
        command.extend(["-name", args.repo_name])
    if args.load_best:
        command.append("--load-best")
    if args.load_checkpoint is not None:
        command.extend(["--load-checkpoint", str(args.load_checkpoint)])
    if args.load_last_checkpoint:
        command.append("--load-last-checkpoint")
    if args.no_render_upload:
        command.append("--no-render")
    if args.commit_message:
        command.extend(["-m", args.commit_message])
    report["commands"].append(
        {
            "label": "planned upload command (network/upload if executed)",
            "command": shell_join(command),
        }
    )


def check_load_target(args: argparse.Namespace, report: dict[str, Any]) -> None:
    folder = Path(args.folder)
    target_path, effective_exp_id = run_path_for_download_target(folder, args.algo, args.env, args.exp_id)
    repo_name = args.repo_name or f"{args.algo}-{args.env}"
    report["derived"]["loadTarget"] = {
        "effectiveExpId": effective_exp_id,
        "targetPath": str(target_path),
        "repoId": f"{args.organization}/{repo_name}",
        "expectedHubModelFilename": f"{args.algo}-{args.env}.zip",
    }

    if target_path.exists():
        if args.force:
            add_finding(
                report,
                "warning",
                target_path,
                "Download target already exists and --force was provided.",
                "rl_zoo3.load_from_hub will overwrite this destination after downloading.",
            )
        else:
            add_finding(
                report,
                "error",
                target_path,
                "Download target already exists and --force was not provided.",
                "Use a fresh --exp-id/log folder or pass --force only if deletion is intended.",
            )
    else:
        add_finding(report, "ok", target_path, "Download target is currently free.")

    if not target_path.parent.exists():
        add_finding(report, "warning", target_path.parent, "Download target parent does not exist yet; the Hub command will create folders.")

    command = [
        "python",
        "-m",
        "rl_zoo3.load_from_hub",
        "--algo",
        args.algo,
        "--env",
        args.env,
        "-f",
        args.folder,
        "--exp-id",
        str(args.exp_id),
        "-orga",
        args.organization,
    ]
    if args.repo_name:
        command.extend(["-name", args.repo_name])
    if args.force:
        command.append("--force")
    report["commands"].append(
        {
            "label": "planned download command (network/download if executed)",
            "command": shell_join(command),
        }
    )


def check_staged_hub(args: argparse.Namespace, report: dict[str, Any]) -> None:
    if args.staged_hub_dir is None:
        add_finding(
            report,
            "warning",
            None,
            "No --staged-hub-dir was provided; skipped local Hub repository file-set checks.",
        )
        return

    staged = Path(args.staged_hub_dir)
    report["derived"]["stagedHub"] = {
        "path": str(staged),
        "expectedModelFilename": f"{args.algo}-{args.env}.zip",
    }
    if staged.is_dir():
        add_finding(report, "ok", staged, "Found staged/local Hub repository directory.")
    else:
        add_finding(report, "error", staged, "Staged/local Hub repository directory is missing.")
        return

    require_file(report, staged / f"{args.algo}-{args.env}.zip", "Hub model zip")
    require_file(report, staged / "config.yml", "Hub config.yml")
    require_file(report, staged / "args.yml", "Hub args.yml")
    require_file(report, staged / "env_kwargs.yml", "Hub env_kwargs.yml")
    require_file(report, staged / "train_eval_metrics.zip", "Hub train_eval_metrics.zip")
    warn_file(report, staged / "README.md", "Hub README.md model card", "Expected after RL Zoo upload packaging.")

    hub_norm = staged / "vec_normalize.pkl"
    local_norm_name = staged / "vecnormalize.pkl"
    if args.expect_vecnormalize == "yes":
        require_file(report, hub_norm, "Hub VecNormalize stats vec_normalize.pkl")
    else:
        warn_file(report, hub_norm, "Hub VecNormalize stats vec_normalize.pkl", "Safe to omit only when the model was not normalized.")
    if local_norm_name.is_file():
        add_finding(
            report,
            "warning",
            local_norm_name,
            "Found local-layout vecnormalize.pkl in the staged Hub directory; Hub download expects vec_normalize.pkl.",
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Offline RL Zoo Hub layout checker. Validates local files and prints planned commands only."
    )
    parser.add_argument("--mode", choices=("push", "load-target", "staged-hub", "all"), default="all")
    parser.add_argument("--folder", default="logs", help="RL Zoo log folder root, for example logs or rl-trained-agents")
    parser.add_argument("--algo", required=True, choices=ALGOS, help="RL Zoo algorithm alias")
    parser.add_argument("--env", required=True, help="Gymnasium environment id, for example CartPole-v1")
    parser.add_argument("--exp-id", type=int, default=0, help="Experiment id. For load-target, 0 means next numeric run.")
    parser.add_argument("-orga", "--organization", default="sb3", help="Hub organization/user name")
    parser.add_argument("-name", "--repo-name", help="Hub repository name; defaults to {algo}-{env}")
    parser.add_argument("--force", action="store_true", help="Plan load_from_hub overwrite behavior; never deletes files here")
    selector = parser.add_mutually_exclusive_group()
    selector.add_argument("--load-best", action="store_true", help="Check selected best_model.zip for upload planning")
    selector.add_argument("--load-checkpoint", type=int, help="Check selected rl_model_<steps>_steps.zip for upload planning")
    selector.add_argument("--load-last-checkpoint", action="store_true", help="Check the latest checkpoint for upload planning")
    parser.add_argument(
        "--expect-vecnormalize",
        choices=("auto", "yes", "no"),
        default="auto",
        help="Whether missing VecNormalize stats should be an error. auto inspects config.yml heuristically.",
    )
    parser.add_argument("--staged-hub-dir", help="Optional local Hub repo/staging directory to validate without network")
    parser.add_argument(
        "--no-render-upload",
        action="store_true",
        default=True,
        help="Include --no-render in the planned push_to_hub command; default true for safe headless planning.",
    )
    parser.add_argument(
        "--render-upload",
        dest="no_render_upload",
        action="store_false",
        help="Omit --no-render from the planned upload command. This may require display/video support if executed.",
    )
    parser.add_argument("--commit-message", default="Initial commit", help="Commit message to include in planned upload command")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of human-readable text")
    return parser


def human_print(report: dict[str, Any]) -> None:
    print("RL Zoo Hub layout checker (offline/no credentials/no training)")
    print(f"Mode: {report['inputs']['mode']}")
    for key, value in report["derived"].items():
        print(f"\n[{key}]")
        for subkey, subvalue in value.items():
            print(f"  {subkey}: {subvalue}")
    print("\nFindings:")
    for item in report["findings"]:
        path = f" ({item['path']})" if "path" in item else ""
        print(f"  [{item['severity']}] {item['message']}{path}")
        if item.get("hint"):
            print(f"        hint: {item['hint']}")
    if report["commands"]:
        print("\nPlanned commands (not executed):")
        for item in report["commands"]:
            print(f"  # {item['label']}")
            print(f"  {item['command']}")
    print(f"\nResult: {'FAILED' if report['hasErrors'] else 'OK'}")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    report: dict[str, Any] = {
        "inputs": {
            "mode": args.mode,
            "folder": args.folder,
            "algo": args.algo,
            "env": args.env,
            "expId": args.exp_id,
            "organization": args.organization,
            "repoName": args.repo_name,
            "force": args.force,
            "stagedHubDir": args.staged_hub_dir,
        },
        "networkBehavior": "no network, no credentials, no model loading, no training, no upload/download",
        "derived": {},
        "findings": [],
        "commands": [],
        "hasErrors": False,
    }

    if args.mode in ("push", "all"):
        check_push_layout(args, report)
    if args.mode in ("load-target", "all"):
        check_load_target(args, report)
    if args.mode in ("staged-hub", "all"):
        check_staged_hub(args, report)

    report["hasErrors"] = any(item["severity"] == "error" for item in report["findings"])
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        human_print(report)
    return 1 if report["hasErrors"] else 0


if __name__ == "__main__":
    sys.exit(main())
