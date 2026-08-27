#!/usr/bin/env python3
"""Print or execute MASt3R-SLAM benchmark evaluation commands.

Safe default: print commands only. Add --execute only after approving the GPU,
data, checkpoint, and runtime cost.
"""
from __future__ import annotations

import argparse
import pathlib
import shlex
import subprocess

TUM = [
    "rgbd_dataset_freiburg1_360",
    "rgbd_dataset_freiburg1_desk",
    "rgbd_dataset_freiburg1_desk2",
    "rgbd_dataset_freiburg1_floor",
    "rgbd_dataset_freiburg1_plant",
    "rgbd_dataset_freiburg1_room",
    "rgbd_dataset_freiburg1_rpy",
    "rgbd_dataset_freiburg1_teddy",
    "rgbd_dataset_freiburg1_xyz",
]
SEVEN = ["chess", "fire", "heads", "office", "pumpkin", "redkitchen", "stairs"]
EUROC = [
    "MH_01_easy", "MH_02_easy", "MH_03_medium", "MH_04_difficult", "MH_05_difficult",
    "V1_01_easy", "V1_02_medium", "V1_03_difficult", "V2_01_easy", "V2_02_medium", "V2_03_difficult",
]
ETH3D = [
    "plant_1", "plant_2", "plant_3", "plant_4", "plant_5", "cables_1", "cables_2", "cables_3",
    "camera_shake_1", "camera_shake_2", "camera_shake_3", "ceiling_1", "ceiling_2", "desk_3",
    "desk_changing_1", "einstein_1", "einstein_2", "einstein_flashlight", "einstein_global_light_changes_1",
    "einstein_global_light_changes_2", "einstein_global_light_changes_3", "kidnap_1", "large_loop_1",
    "mannequin_1", "mannequin_3", "mannequin_4", "mannequin_5", "mannequin_7", "mannequin_face_1",
    "mannequin_face_2", "mannequin_face_3", "mannequin_head", "motion_1", "planar_2", "planar_3",
    "plant_scene_1", "plant_scene_2", "plant_scene_3", "reflective_1", "repetitive", "sfm_bench",
    "sfm_garden", "sfm_house_loop", "sfm_lab_room_1", "sfm_lab_room_2", "sofa_1", "sofa_2",
    "sofa_3", "sofa_4", "sofa_shake", "table_3", "table_4", "table_7", "vicon_light_1", "vicon_light_2",
]

SUITES = {
    "tum": TUM,
    "7-scenes": SEVEN,
    "euroc": EUROC,
    "eth3d": ETH3D,
}


def rel(*parts: str) -> str:
    return "/".join(part.strip("/") for part in parts if part != "")


def shell_command(cmd: list[str], repo_root: pathlib.Path) -> str:
    return f"cd {shlex.quote(str(repo_root))} && {shlex.join(cmd)}"


def suite_paths(suite: str, seq: str, no_calib: bool, dataset_root: str, logs_root: str, config_dir: str, python: str) -> tuple[list[str], list[str]]:
    calib_state = "no_calib" if no_calib else "calib"
    if suite == "tum":
        dataset = rel(dataset_root, "tum", seq) + "/"
        save_as = rel("tum", calib_state, seq)
        config = rel(config_dir, "eval_no_calib.yaml" if no_calib else "eval_calib.yaml")
        gt = rel(dataset, "groundtruth.txt")
    elif suite == "7-scenes":
        dataset = rel(dataset_root, "7-scenes", seq) + "/"
        save_as = rel("7-scenes", calib_state, seq)
        config = rel(config_dir, "eval_no_calib.yaml" if no_calib else "eval_calib.yaml")
        gt = rel("groundtruths", "7-scenes", f"{seq}.txt")
    elif suite == "euroc":
        dataset = rel(dataset_root, "euroc", seq) + "/"
        save_as = rel("euroc", calib_state, seq)
        config = rel(config_dir, "eval_no_calib.yaml" if no_calib else "eval_calib.yaml")
        gt = rel("groundtruths", "euroc", f"{seq}.txt")
    elif suite == "eth3d":
        dataset = rel(dataset_root, "eth3d", "train", seq) + "/"
        save_as = rel("eth3d", seq)
        config = rel(config_dir, "eth3d.yaml")
        gt = rel(dataset, "groundtruth.txt")
    else:
        raise ValueError(suite)
    traj = rel(logs_root, save_as, f"{seq}.txt")
    run = [python, "main.py", "--dataset", dataset, "--no-viz", "--save-as", save_as, "--config", config]
    metric = ["evo_ape", "tum", gt, traj, "-as"]
    return run, metric


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--suite", action="append", choices=["all", *SUITES.keys()], default=None, help="Suite to plan; repeatable. Defaults to all.")
    parser.add_argument("--sequence", action="append", help="Restrict to one or more sequence names.")
    parser.add_argument("--repo-root", type=pathlib.Path, default=pathlib.Path.cwd(), help="MASt3R-SLAM checkout root used as command working directory.")
    parser.add_argument("--python", default="python", help="Python executable for the generated main.py commands. Defaults to shell 'python'.")
    parser.add_argument("--dataset-root", default="datasets", help="Dataset root relative to repo root or absolute path.")
    parser.add_argument("--logs-root", default="logs", help="Logs root relative to repo root or absolute path.")
    parser.add_argument("--config-dir", default="config", help="Directory containing evaluation config YAMLs.")
    parser.add_argument("--no-calib", action="store_true", help="Use no-calibration branches for TUM/7-Scenes/EuRoC.")
    parser.add_argument("--metric-only", action="store_true", help="Print/run only evo_ape commands, not SLAM runs.")
    parser.add_argument("--execute", action="store_true", help="Execute commands after printing them.")
    args = parser.parse_args()

    suites = args.suite or ["all"]
    if "all" in suites:
        suites = list(SUITES)
    repo_root = args.repo_root.resolve()
    wanted = set(args.sequence or [])
    commands: list[list[str]] = []

    for suite in suites:
        if suite == "eth3d" and args.no_calib:
            print("warning: ETH3D source eval script has no --no-calib branch; using eth3d.yaml", file=sys.stderr)
        for seq in SUITES[suite]:
            if wanted and seq not in wanted:
                continue
            run, metric = suite_paths(suite, seq, args.no_calib and suite != "eth3d", args.dataset_root, args.logs_root, args.config_dir, args.python)
            if not args.metric_only:
                commands.append(run)
            commands.append(metric)

    for cmd in commands:
        print(shell_command(cmd, repo_root))
    if args.execute:
        for cmd in commands:
            code = subprocess.run(cmd, cwd=repo_root).returncode
            if code:
                return code
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
