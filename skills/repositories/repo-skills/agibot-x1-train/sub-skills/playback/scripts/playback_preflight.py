#!/usr/bin/env python3
"""Static, non-interactive preflight for AgiBot X1 Isaac Gym playback.

This helper never imports Isaac Gym, initializes pygame, opens a viewer,
deserializes a checkpoint, or starts humanoid/scripts/play.py.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
from typing import Any

CANONICAL_TASK = "x1_dh_stand"
CANONICAL_EXPERIMENT = "x1_dh_stand"
MODEL_RE = re.compile(r"^model_(\d+)\.pt$")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Safely resolve an X1 playback checkpoint and audit modules, CUDA "
            "metadata, display variables, and joystick device nodes. Nothing "
            "interactive is launched and checkpoints are never deserialized."
        )
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        required=True,
        help="AgiBot X1 training repository root containing humanoid/ and logs/.",
    )
    parser.add_argument(
        "--task",
        default=CANONICAL_TASK,
        help=f"Playback task (only {CANONICAL_TASK!r} is supported here).",
    )
    parser.add_argument(
        "--experiment-name",
        default=CANONICAL_EXPERIMENT,
        help="Experiment directory below logs/ (default: x1_dh_stand).",
    )
    parser.add_argument(
        "--run-name",
        default=None,
        help="Optional playback run label; does NOT select the trained run.",
    )
    parser.add_argument(
        "--load-run",
        default=None,
        help=(
            "Exact trained run directory below exported_data. Omit for the "
            "configured latest-run behavior; do not pass literal -1."
        ),
    )
    parser.add_argument(
        "--checkpoint",
        type=int,
        default=-1,
        help="Checkpoint suffix N for model_N.pt; -1 selects latest (default: -1).",
    )
    parser.add_argument(
        "--num-envs",
        type=int,
        default=1,
        help="Requested playback environment count (safe initial default: 1).",
    )
    parser.add_argument(
        "--rl-device",
        default="cuda:0",
        help="Inference-policy device passed as --rl_device (default: cuda:0).",
    )
    parser.add_argument(
        "--sim-device",
        default="cuda:0",
        help="Simulator device passed as --sim_device (default: cuda:0).",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Audit a requested headless flag; rejected for this interactive route.",
    )
    parser.add_argument(
        "--require-joystick",
        action="store_true",
        help="Fail if no Linux /dev/input/js* joystick node is visible.",
    )
    parser.add_argument(
        "--joystick-device",
        type=Path,
        default=None,
        help="Specific joystick device node to require instead of scanning js*.",
    )
    parser.add_argument(
        "--skip-backend-check",
        action="store_true",
        help="Skip module/CUDA/display probes for a filesystem-only audit.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit one JSON object instead of the human-readable report.",
    )
    return parser


def add_issue(report: dict[str, Any], level: str, code: str, message: str) -> None:
    report["issues"].append({"level": level, "code": code, "message": message})


def module_present(name: str) -> tuple[bool, str | None]:
    """Find a module without importing it."""
    try:
        spec = importlib.util.find_spec(name)
    except Exception as exc:  # defensive: parent-package discovery can raise
        return False, f"{type(exc).__name__}: {exc}"
    if spec is None:
        return False, None
    return True, spec.origin


def torch_probe() -> dict[str, Any]:
    """Probe torch in a child process; never load a checkpoint."""
    code = (
        "import json, torch; "
        "print(json.dumps({'version': torch.__version__, "
        "'cuda_built': torch.version.cuda, "
        "'cuda_available': torch.cuda.is_available(), "
        "'device_count': torch.cuda.device_count()}))"
    )
    try:
        proc = subprocess.run(
            [sys.executable, "-c", code],
            text=True,
            capture_output=True,
            timeout=20,
            check=False,
        )
    except Exception as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
    if proc.returncode != 0:
        return {
            "ok": False,
            "error": (proc.stderr or proc.stdout).strip() or f"exit {proc.returncode}",
        }
    try:
        data = json.loads(proc.stdout.strip().splitlines()[-1])
    except Exception as exc:
        return {"ok": False, "error": f"invalid torch probe output: {exc}"}
    data["ok"] = True
    return data


def safe_run_component(value: str) -> bool:
    candidate = Path(value)
    return (
        value not in {"", ".", ".."}
        and not candidate.is_absolute()
        and len(candidate.parts) == 1
        and candidate.parts[0] not in {".", ".."}
    )


def repository_sort_key(name: str) -> str:
    """Mirror get_load_path's zero-left-padded, width-15 name sorting."""
    return name.rjust(15, "0")


def resolve_model(report: dict[str, Any], log_root: Path, load_run: str | None, checkpoint: int) -> None:
    if not log_root.is_dir():
        add_issue(
            report,
            "ERROR",
            "missing-log-root",
            f"Checkpoint log root is not a directory: {log_root}",
        )
        return

    selected_run: Path | None = None
    if load_run is None:
        try:
            names = sorted(entry.name for entry in log_root.iterdir())
        except OSError as exc:
            add_issue(report, "ERROR", "list-runs-failed", str(exc))
            return
        if "exported" in names:
            names.remove("exported")
        report["run_candidates"] = names
        if not names:
            add_issue(report, "ERROR", "no-runs", f"No runs in {log_root}")
            return
        selected_run = log_root / names[-1]
        add_issue(
            report,
            "WARNING",
            "implicit-latest-run",
            "Latest run is selected lexicographically; pin --load-run before launch.",
        )
    else:
        if load_run == "-1":
            add_issue(
                report,
                "ERROR",
                "string-minus-one-run",
                "Do not pass --load-run=-1; omit --load-run to preserve integer -1 latest selection.",
            )
            return
        if not safe_run_component(load_run):
            add_issue(
                report,
                "ERROR",
                "unsafe-run-name",
                "--load-run must be one direct child directory name (no absolute path or traversal).",
            )
            return
        selected_run = log_root / load_run

    report["selected_run"] = str(selected_run)
    if not selected_run.is_dir():
        add_issue(
            report,
            "ERROR",
            "missing-run",
            f"Selected run is not a directory: {selected_run}",
        )
        return

    selected_model: Path
    if checkpoint == -1:
        try:
            model_names = [entry.name for entry in selected_run.iterdir() if "model" in entry.name]
        except OSError as exc:
            add_issue(report, "ERROR", "list-models-failed", str(exc))
            return
        model_names.sort(key=repository_sort_key)
        report["model_candidates"] = model_names
        if not model_names:
            add_issue(
                report,
                "ERROR",
                "no-models",
                f"No filename containing 'model' exists in {selected_run}",
            )
            return
        selected_model = selected_run / model_names[-1]
        add_issue(
            report,
            "WARNING",
            "implicit-latest-model",
            "Latest model uses repository filename sorting; pin --checkpoint before launch.",
        )
        noncanonical = [name for name in model_names if MODEL_RE.fullmatch(name) is None]
        if noncanonical:
            add_issue(
                report,
                "WARNING",
                "noncanonical-model-candidates",
                "Repository latest selection includes noncanonical names: " + ", ".join(noncanonical),
            )
    elif checkpoint < -1:
        add_issue(
            report,
            "ERROR",
            "invalid-checkpoint",
            "--checkpoint must be -1 or a nonnegative integer suffix.",
        )
        return
    else:
        selected_model = selected_run / f"model_{checkpoint}.pt"

    report["selected_model"] = str(selected_model)
    if not selected_model.is_file():
        add_issue(
            report,
            "ERROR",
            "missing-model",
            f"Selected checkpoint is not a regular file: {selected_model}",
        )
        return
    try:
        size = selected_model.stat().st_size
    except OSError as exc:
        add_issue(report, "ERROR", "stat-model-failed", str(exc))
        return
    report["selected_model_bytes"] = size
    if size <= 0:
        add_issue(report, "ERROR", "empty-model", "Selected checkpoint is empty.")
    if MODEL_RE.fullmatch(selected_model.name) is None:
        add_issue(
            report,
            "ERROR",
            "noncanonical-selected-model",
            "Selected file is not canonical model_<integer>.pt; select an explicit canonical checkpoint.",
        )
    if not os.access(selected_model, os.R_OK):
        add_issue(report, "ERROR", "unreadable-model", "Selected checkpoint is not readable.")


def build_command(args: argparse.Namespace, root: Path) -> list[str]:
    command = [
        sys.executable,
        str(root / "humanoid" / "scripts" / "play.py"),
        f"--task={args.task}",
        f"--experiment_name={args.experiment_name}",
        f"--num_envs={args.num_envs}",
        f"--rl_device={args.rl_device}",
        f"--sim_device={args.sim_device}",
    ]
    if args.load_run is not None:
        command.append(f"--load_run={args.load_run}")
    if args.checkpoint != -1:
        command.append(f"--checkpoint={args.checkpoint}")
    if args.run_name is not None:
        command.append(f"--run_name={args.run_name}")
    if args.headless:
        command.append("--headless")
    return command


def audit(args: argparse.Namespace) -> dict[str, Any]:
    root = args.repo_root.expanduser().resolve()
    report: dict[str, Any] = {
        "status": "UNKNOWN",
        "interactive_launched": False,
        "checkpoint_deserialized": False,
        "repo_root": str(root),
        "task": args.task,
        "experiment_name": args.experiment_name,
        "issues": [],
    }

    if args.task != CANONICAL_TASK:
        add_issue(
            report,
            "ERROR",
            "unsupported-task",
            f"Only registered playback task {CANONICAL_TASK!r} is supported.",
        )
    if args.num_envs < 1:
        add_issue(report, "ERROR", "invalid-num-envs", "--num-envs must be at least 1.")
    elif args.num_envs > 10:
        add_issue(
            report,
            "WARNING",
            "large-num-envs",
            "Explicit --num_envs is applied after play.py's ten-env cap; start with 1.",
        )
    if args.headless:
        add_issue(
            report,
            "ERROR",
            "headless-interactive-conflict",
            "This route requires a viewer, and play.py calls camera setup unconditionally.",
        )
    if args.run_name is not None:
        add_issue(
            report,
            "WARNING",
            "run-name-not-selector",
            "--run_name labels a new playback log/video path; only --load_run selects training output.",
        )

    expected_paths = {
        "play_script": root / "humanoid" / "scripts" / "play.py",
        "package": root / "humanoid" / "__init__.py",
        "x1_urdf": root / "resources" / "robots" / "x1" / "urdf" / "x1.urdf",
    }
    report["paths"] = {name: str(path) for name, path in expected_paths.items()}
    for name, path in expected_paths.items():
        if not path.is_file():
            add_issue(report, "ERROR", f"missing-{name}", f"Required file is missing: {path}")

    log_root = root / "logs" / args.experiment_name / "exported_data"
    report["log_root"] = str(log_root)
    resolve_model(report, log_root, args.load_run, args.checkpoint)

    if args.skip_backend_check:
        report["backend_check"] = "SKIPPED"
        add_issue(
            report,
            "WARNING",
            "backend-check-skipped",
            "Filesystem-only audit cannot clear BLOCKED_REQUIRED_BACKEND.",
        )
    else:
        report["backend_check"] = "STATIC_ONLY"
        modules: dict[str, Any] = {}
        for module in (
            "isaacgym",
            "torch",
            "humanoid",
            "pygame",
            "cv2",
            "wandb",
            "tensorboard",
            "numpy",
            "scipy",
            "matplotlib",
        ):
            present, origin = module_present(module)
            modules[module] = {"present": present, "origin": origin}
            if not present:
                add_issue(
                    report,
                    "ERROR",
                    f"missing-module-{module}",
                    f"Module spec not found without import: {module}",
                )
        report["modules"] = modules
        humanoid_origin = modules.get("humanoid", {}).get("origin")
        if humanoid_origin:
            try:
                origin_path = Path(humanoid_origin).resolve()
                package_root = (root / "humanoid").resolve()
                if package_root not in origin_path.parents and origin_path != package_root:
                    add_issue(
                        report,
                        "ERROR",
                        "wrong-humanoid-package",
                        f"Installed humanoid resolves outside --repo-root: {origin_path}",
                    )
            except OSError as exc:
                add_issue(report, "ERROR", "humanoid-origin-check-failed", str(exc))

        torch_info = torch_probe() if modules.get("torch", {}).get("present") else {"ok": False, "error": "torch spec absent"}
        report["torch_probe"] = torch_info
        if not torch_info.get("ok"):
            add_issue(report, "ERROR", "torch-probe-failed", str(torch_info.get("error")))
        elif not torch_info.get("cuda_available"):
            add_issue(report, "ERROR", "cuda-unavailable", "torch.cuda.is_available() is false.")
        if torch_info.get("version") and not str(torch_info["version"]).startswith("1.13"):
            add_issue(
                report,
                "WARNING",
                "torch-version-drift",
                f"Documented stack uses PyTorch 1.13.1; found {torch_info['version']}.",
            )
        if torch_info.get("cuda_built") and str(torch_info["cuda_built"]) != "11.7":
            add_issue(
                report,
                "WARNING",
                "cuda-build-drift",
                f"Documented stack uses CUDA 11.7; torch reports {torch_info['cuda_built']}.",
            )

        display = {
            "DISPLAY": os.environ.get("DISPLAY"),
            "WAYLAND_DISPLAY": os.environ.get("WAYLAND_DISPLAY"),
        }
        report["display"] = display
        if not any(display.values()):
            add_issue(
                report,
                "ERROR",
                "missing-display",
                "Neither DISPLAY nor WAYLAND_DISPLAY is set for interactive viewer playback.",
            )

    if args.joystick_device is not None:
        joystick_nodes = [args.joystick_device.expanduser()]
    else:
        joystick_nodes = sorted(Path("/dev/input").glob("js*")) if Path("/dev/input").is_dir() else []
    report["joystick_nodes"] = [str(path) for path in joystick_nodes]
    available_joysticks = [path for path in joystick_nodes if path.exists() and os.access(path, os.R_OK)]
    if args.require_joystick and not available_joysticks:
        add_issue(
            report,
            "ERROR",
            "joystick-unavailable",
            "No readable requested Linux joystick node is visible; pygame index/axes remain unverified.",
        )
    elif not available_joysticks:
        add_issue(
            report,
            "WARNING",
            "joystick-not-observed",
            "No readable Linux js* node observed; zero-command fallback may occur.",
        )

    command = build_command(args, root)
    report["playback_command_argv"] = command
    report["playback_command"] = shlex.join(command)

    errors = sum(issue["level"] == "ERROR" for issue in report["issues"])
    warnings = sum(issue["level"] == "WARNING" for issue in report["issues"])
    report["error_count"] = errors
    report["warning_count"] = warnings
    if errors:
        report["status"] = "BLOCKED"
        report["note"] = "Resolve every ERROR before any interactive launch."
    elif args.skip_backend_check:
        report["status"] = "FILESYSTEM_ONLY"
        report["note"] = (
            "Filesystem-only audit passed; backend and display checks were skipped "
            "and native playback remains BLOCKED_REQUIRED_BACKEND until verified."
        )
    else:
        report["status"] = "READY_STATIC"
        report["note"] = (
            "READY_STATIC means only that this non-interactive audit passed; native "
            "Isaac Gym viewer playback still requires an explicit human-run check."
        )
    return report


def print_human(report: dict[str, Any]) -> None:
    print(f"status: {report['status']}")
    print(f"task: {report['task']}")
    print(f"log_root: {report.get('log_root')}")
    print(f"selected_run: {report.get('selected_run', '<unresolved>')}")
    print(f"selected_model: {report.get('selected_model', '<unresolved>')}")
    for issue in report["issues"]:
        print(f"{issue['level']} [{issue['code']}]: {issue['message']}")
    print("playback_command (NOT executed):")
    print(report["playback_command"])
    print(report["note"])


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = audit(args)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_human(report)
    return 0 if report["status"] != "BLOCKED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
