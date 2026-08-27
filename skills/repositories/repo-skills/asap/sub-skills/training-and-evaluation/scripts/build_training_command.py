#!/usr/bin/env python3
"""Build safe HumanoidVerse training/evaluation commands for this repo skill.

The builder prints shell commands only. It does not import HumanoidVerse, Hydra,
Torch, simulator packages, or execute training/evaluation. Use --cfg-job on the
printed command for Hydra composition smoke checks before a long run.
"""

from __future__ import annotations

import argparse
import shlex
import sys
from pathlib import Path
from typing import List, Optional, Sequence, Tuple


DEFAULT_ROBOT = "g1/g1_29dof_anneal_23dof"
DEFAULT_TERRAIN = "terrain_locomotion_plane"
DEFAULT_SIMULATOR = "isaacgym"

WORKFLOWS = {
    "locomotion-smoke",
    "locomotion-train",
    "motion-tracking",
    "delta-a-open-loop",
    "delta-a-finetune",
    "eval",
    "export-onnx",
    "eval-record-motion",
}

ANALYSIS_OPTS = {
    "motion_tracking": "eval_analysis_plot_motion_tracking",
    "locomotion": "eval_analysis_plot_locomotion",
}


class BuildError(Exception):
    pass


def parse_bool(value: str) -> bool:
    lowered = value.lower()
    if lowered in {"1", "true", "yes", "y", "on"}:
        return True
    if lowered in {"0", "false", "no", "n", "off"}:
        return False
    raise argparse.ArgumentTypeError("expected true/false")


def hydra_bool(value: bool) -> str:
    return "True" if value else "False"


def repo_root(path: str) -> Path:
    root = Path(path).expanduser().resolve()
    if not (root / "humanoidverse" / "train_agent.py").is_file():
        raise argparse.ArgumentTypeError(
            "--repo-root must point to an ASAP/HumanoidVerse checkout containing humanoidverse/train_agent.py"
        )
    return root


def group_file(root: Path, group: str, value: str) -> Path:
    return root / "humanoidverse" / "config" / group / (value + ".yaml")


def validate_group(root: Path, group: str, value: str, errors: List[str]) -> None:
    path = group_file(root, group, value)
    if not path.is_file():
        errors.append(f"Hydra group +{group}={value!r} does not exist at {path}")


def append_group(argv: List[str], root: Path, group: str, value: str, errors: List[str]) -> None:
    validate_group(root, group, value, errors)
    argv.append(f"+{group}={value}")


def append_common_train(
    argv: List[str],
    root: Path,
    errors: List[str],
    args: argparse.Namespace,
    *,
    exp: str,
    domain_rand: str,
    rewards: str,
    obs: str,
    default_num_envs: int,
    default_project: str,
    default_experiment: str,
    default_headless: bool,
) -> None:
    simulator = args.simulator or DEFAULT_SIMULATOR
    robot = args.robot or DEFAULT_ROBOT
    terrain = args.terrain or DEFAULT_TERRAIN
    append_group(argv, root, "simulator", simulator, errors)
    append_group(argv, root, "exp", exp, errors)
    append_group(argv, root, "domain_rand", domain_rand, errors)
    append_group(argv, root, "rewards", rewards, errors)
    append_group(argv, root, "robot", robot, errors)
    append_group(argv, root, "terrain", terrain, errors)
    append_group(argv, root, "obs", obs, errors)

    num_envs = args.num_envs if args.num_envs is not None else default_num_envs
    project = args.project_name or default_project
    experiment = args.experiment_name or default_experiment
    headless = args.headless if args.headless is not None else default_headless
    argv.extend([
        f"num_envs={num_envs}",
        f"project_name={project}",
        f"experiment_name={experiment}",
        f"headless={hydra_bool(headless)}",
    ])
    if args.device:
        argv.append(f"+device={args.device}")
    if args.wandb:
        append_group(argv, root, "opt", "wandb", errors)


def value_or_placeholder(
    value: Optional[str],
    placeholder: str,
    field_name: str,
    args: argparse.Namespace,
    warnings: List[str],
    errors: List[str],
) -> str:
    if value:
        return value
    msg = f"{field_name} was not provided; using placeholder {placeholder}"
    if args.strict:
        errors.append(msg)
    else:
        warnings.append(msg)
    return placeholder


def validate_existing_path(root: Path, maybe_path: str, label: str, errors: List[str]) -> None:
    if maybe_path.startswith("<") and maybe_path.endswith(">"):
        return
    path = Path(maybe_path).expanduser()
    if not path.is_absolute():
        path = root / path
    if not path.exists():
        errors.append(f"{label} does not exist: {path}")


def add_tail_options(argv: List[str], args: argparse.Namespace) -> None:
    if args.iterations is not None:
        argv.append(f"algo.config.num_learning_iterations={args.iterations}")
    if args.save_interval is not None:
        argv.append(f"algo.config.save_interval={args.save_interval}")
    for extra in args.extra or []:
        if not extra or "\n" in extra or "\r" in extra:
            raise BuildError("--extra values must be one-line Hydra overrides")
        argv.append(extra)
    if args.cfg_job:
        argv.extend(["--cfg", "job"])


def build_train_command(root: Path, args: argparse.Namespace, warnings: List[str], errors: List[str]) -> List[str]:
    argv = [args.python, "humanoidverse/train_agent.py"]

    if args.workflow == "locomotion-smoke":
        append_common_train(
            argv,
            root,
            errors,
            args,
            exp="locomotion",
            domain_rand="NO_domain_rand",
            rewards="loco/reward_g1_locomotion",
            obs="loco/leggedloco_obs_singlestep_withlinvel",
            default_num_envs=1,
            default_project="TestIsaacGymInstallation",
            default_experiment="G123dof_loco",
            default_headless=False,
        )

    elif args.workflow == "locomotion-train":
        append_common_train(
            argv,
            root,
            errors,
            args,
            exp="locomotion",
            domain_rand="NO_domain_rand",
            rewards="loco/reward_g1_locomotion",
            obs="loco/leggedloco_obs_singlestep_withlinvel",
            default_num_envs=4096,
            default_project="Locomotion",
            default_experiment="G123dof_loco",
            default_headless=True,
        )
        if args.checkpoint:
            argv.append(f"checkpoint={args.checkpoint}")
        argv.extend([
            "rewards.reward_penalty_curriculum=True",
            "rewards.reward_initial_penalty_scale=0.1",
            "rewards.reward_penalty_degree=0.00003",
        ])

    elif args.workflow == "motion-tracking":
        append_common_train(
            argv,
            root,
            errors,
            args,
            exp="motion_tracking",
            domain_rand="NO_domain_rand",
            rewards="motion_tracking/reward_motion_tracking_dm_2real",
            obs="motion_tracking/deepmimic_a2c_nolinvel_LARGEnoise_history",
            default_num_envs=4096,
            default_project="MotionTracking",
            default_experiment="MotionTracking_CR7",
            default_headless=True,
        )
        if args.checkpoint:
            argv.append(f"checkpoint={args.checkpoint}")
        motion_file = value_or_placeholder(
            args.motion_file,
            "<PATH_TO_MOTION_FILE>",
            "--motion-file",
            args,
            warnings,
            errors,
        )
        argv.extend([
            f"robot.motion.motion_file={motion_file}",
            "rewards.reward_penalty_curriculum=True",
            "rewards.reward_penalty_degree=0.00001",
            "env.config.resample_motion_when_training=False",
            "env.config.termination.terminate_when_motion_far=True",
            "env.config.termination_curriculum.terminate_when_motion_far_curriculum=True",
            "env.config.termination_curriculum.terminate_when_motion_far_threshold_min=0.3",
            "env.config.termination_curriculum.terminate_when_motion_far_curriculum_degree=0.000025",
            "robot.asset.self_collisions=0",
        ])
        if args.require_existing_paths:
            validate_existing_path(root, motion_file, "motion file", errors)

    elif args.workflow == "delta-a-open-loop":
        append_common_train(
            argv,
            root,
            errors,
            args,
            exp="train_delta_a_open_loop",
            domain_rand="NO_domain_rand",
            rewards="motion_tracking/delta_a/reward_delta_a_openloop",
            obs="delta_a/open_loop",
            default_num_envs=5000,
            default_project="DeltaA_Training",
            default_experiment="openloopDeltaA_training",
            default_headless=True,
        )
        if args.checkpoint:
            argv.append(f"checkpoint={args.checkpoint}")
        motion_file = value_or_placeholder(
            args.motion_file,
            "<PATH_TO_MOTION_FILE_WITH_ACTION_KEY>",
            "--motion-file",
            args,
            warnings,
            errors,
        )
        argv.extend([
            f"robot.motion.motion_file={motion_file}",
            "env.config.max_episode_length_s=1.0",
            "rewards.reward_scales.penalty_minimal_action_norm=-0.1",
            "env.config.resample_motion_when_training=True",
            "env.config.resample_time_interval_s=10000",
        ])
        warnings.append("delta-a-open-loop expects each loaded motion record to contain an 'action' key")
        if args.require_existing_paths:
            validate_existing_path(root, motion_file, "motion file with action key", errors)

    elif args.workflow == "delta-a-finetune":
        append_common_train(
            argv,
            root,
            errors,
            args,
            exp="train_delta_a_closed_loop",
            domain_rand="NO_domain_rand_finetune_with_deltaA",
            rewards="motion_tracking/reward_motion_tracking_dm_simfinetuning",
            obs="delta_a/train_policy_with_delta_a",
            default_num_envs=4096,
            default_project="DeltaA_Finetune",
            default_experiment="finetune_with_deltaA",
            default_headless=True,
        )
        motion_file = value_or_placeholder(args.motion_file, "<PATH_TO_MOTION_FILE>", "--motion-file", args, warnings, errors)
        delta_policy = value_or_placeholder(
            args.delta_policy_checkpoint,
            "<PATH_TO_YOUR_DELTA_A_MODEL>",
            "--delta-policy-checkpoint",
            args,
            warnings,
            errors,
        )
        fine_tune_checkpoint = value_or_placeholder(
            args.checkpoint,
            "<PATH_TO_YOUR_POLICY_TO_BE_FINETUNED>",
            "--checkpoint",
            args,
            warnings,
            errors,
        )
        argv.extend([
            f"algo.config.policy_checkpoint={delta_policy}",
            f"robot.motion.motion_file={motion_file}",
            "env.config.add_extra_action=True",
            f"checkpoint={fine_tune_checkpoint}",
            "domain_rand.push_robots=False",
            "env.config.noise_to_initial_level=1",
            "rewards.reward_penalty_curriculum=True",
            "algo.config.save_interval=5",
            "algo.config.num_learning_iterations=1000",
        ])
        if args.require_existing_paths:
            validate_existing_path(root, motion_file, "motion file", errors)
            validate_existing_path(root, delta_policy, "delta policy checkpoint", errors)
            validate_existing_path(root, fine_tune_checkpoint, "policy checkpoint to fine-tune", errors)

    else:
        raise BuildError(f"unsupported training workflow {args.workflow}")

    add_tail_options(argv, args)
    return argv


def build_eval_command(root: Path, args: argparse.Namespace, warnings: List[str], errors: List[str]) -> List[str]:
    argv = [args.python, "humanoidverse/eval_agent.py"]
    checkpoint = value_or_placeholder(args.checkpoint, "<PATH_TO_CHECKPOINT_PT>", "--checkpoint", args, warnings, errors)
    argv.append(f"+checkpoint={checkpoint}")

    eval_name = args.eval_name or ("export_onnx" if args.workflow == "export-onnx" else "eval")
    argv.append(f"eval_name={eval_name}")
    if args.headless is not None:
        # base_eval.yaml does not define headless; append so it can override the loaded training config.
        argv.append(f"+headless={hydra_bool(args.headless)}")
    if args.num_envs is not None:
        argv.append(f"+num_envs={args.num_envs}")
    if args.device:
        argv.append(f"+device={args.device}")
    if args.analysis != "none":
        opt = ANALYSIS_OPTS[args.analysis]
        append_group(argv, root, "opt", opt, errors)
    if args.workflow == "eval-record-motion":
        append_group(argv, root, "opt", "record", errors)
        save_note = args.save_note or "recorded_policy_motion"
        save_steps = args.save_total_steps if args.save_total_steps is not None else 10000
        argv.extend([
            "env.config.save_motion=True",
            f"env.config.save_note={save_note}",
            f"env.config.save_total_steps={save_steps}",
        ])
        warnings.append("eval-record-motion writes a motion pkl under checkpoint.parent/motions/ and exits after save_total_steps")
    if args.workflow == "export-onnx":
        warnings.append("eval_agent.py exports ONNX before entering its evaluation loop; stop the process after the export log if export-only")
    if args.require_existing_paths:
        validate_existing_path(root, checkpoint, "checkpoint", errors)

    add_tail_options(argv, args)
    return argv


def format_command(argv: Sequence[str], args: argparse.Namespace) -> str:
    parts: List[str] = []
    if not args.no_hydra_full_error:
        parts.append("HYDRA_FULL_ERROR=1")
    parts.extend(shlex.quote(part) for part in argv)
    command = " ".join(parts) if args.one_line else " \\\n  ".join(parts)
    repo_prefix = f"cd {shlex.quote(str(args.repo_root))} &&"
    if args.one_line:
        return repo_prefix + " " + command
    return repo_prefix + " \\\n" + command


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Print safe HumanoidVerse train/eval/export commands for known ASAP workflows."
    )
    parser.add_argument("--workflow", required=True, choices=sorted(WORKFLOWS))
    parser.add_argument("--repo-root", default=".", type=repo_root)
    parser.add_argument("--python", default="python", help="Python executable to print in the command")
    parser.add_argument("--simulator", default=None, help="Hydra simulator choice, e.g. isaacgym, isaacsim, genesis, mujoco")
    parser.add_argument("--robot", default=None, help="Hydra robot choice, e.g. g1/g1_29dof_anneal_23dof")
    parser.add_argument("--terrain", default=None, help="Hydra terrain choice, e.g. terrain_locomotion_plane")
    parser.add_argument("--num-envs", type=int, default=None)
    parser.add_argument("--project-name", default=None)
    parser.add_argument("--experiment-name", default=None)
    parser.add_argument("--headless", type=parse_bool, default=None, help="true/false; eval uses +headless because base_eval lacks the key")
    parser.add_argument("--device", default=None, help="Optional Hydra +device override, e.g. cuda:0 or cpu")
    parser.add_argument("--motion-file", default=None, help="Motion pkl path for motion-tracking or delta-action training")
    parser.add_argument("--checkpoint", default=None, help="Training resume checkpoint, eval/export checkpoint, or policy checkpoint to fine-tune")
    parser.add_argument("--delta-policy-checkpoint", default=None, help="Closed-loop delta-action model loaded by algo.config.policy_checkpoint")
    parser.add_argument("--wandb", action="store_true", help="Add +opt=wandb to training commands")
    parser.add_argument("--analysis", choices=["none", "motion_tracking", "locomotion"], default="none")
    parser.add_argument("--eval-name", default=None)
    parser.add_argument("--save-note", default=None)
    parser.add_argument("--save-total-steps", type=int, default=None)
    parser.add_argument("--iterations", type=int, default=None, help="Append algo.config.num_learning_iterations")
    parser.add_argument("--save-interval", type=int, default=None, help="Append algo.config.save_interval")
    parser.add_argument("--extra", action="append", default=[], help="Append an extra one-line Hydra override; may be passed multiple times")
    parser.add_argument("--cfg-job", action="store_true", help="Append --cfg job for Hydra composition-only smoke checks")
    parser.add_argument("--require-existing-paths", action="store_true", help="Fail if motion/checkpoint paths do not exist")
    parser.add_argument("--strict", action="store_true", help="Fail instead of printing placeholders for missing required paths")
    parser.add_argument("--one-line", action="store_true", help="Print the command on one line")
    parser.add_argument("--no-hydra-full-error", action="store_true", help="Do not prefix HYDRA_FULL_ERROR=1")
    return parser.parse_args(argv)


def main(argv: Sequence[str]) -> int:
    try:
        args = parse_args(argv)
        root: Path = args.repo_root
        warnings: List[str] = []
        errors: List[str] = []
        if args.workflow in {"eval", "export-onnx", "eval-record-motion"}:
            command = build_eval_command(root, args, warnings, errors)
        else:
            command = build_train_command(root, args, warnings, errors)
        if errors:
            for msg in errors:
                print(f"ERROR: {msg}", file=sys.stderr)
            return 2
        for msg in warnings:
            print(f"WARNING: {msg}", file=sys.stderr)
        print(format_command(command, args))
        return 0
    except (BuildError, argparse.ArgumentTypeError, argparse.ArgumentError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
