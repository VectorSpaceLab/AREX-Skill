#!/usr/bin/env python3
"""Print MASt3R-SLAM benchmark dataset download manifests.

This helper never performs downloads. It prints URLs and, with --commands,
source-script-like shell commands for user-approved execution.
"""
from __future__ import annotations

import argparse
import pathlib

TUM_URLS = [
    "https://cvg.cit.tum.de/rgbd/dataset/freiburg1/rgbd_dataset_freiburg1_360.tgz",
    "https://cvg.cit.tum.de/rgbd/dataset/freiburg1/rgbd_dataset_freiburg1_floor.tgz",
    "https://cvg.cit.tum.de/rgbd/dataset/freiburg1/rgbd_dataset_freiburg1_desk.tgz",
    "https://cvg.cit.tum.de/rgbd/dataset/freiburg1/rgbd_dataset_freiburg1_desk2.tgz",
    "https://cvg.cit.tum.de/rgbd/dataset/freiburg1/rgbd_dataset_freiburg1_room.tgz",
    "https://cvg.cit.tum.de/rgbd/dataset/freiburg1/rgbd_dataset_freiburg1_plant.tgz",
    "https://cvg.cit.tum.de/rgbd/dataset/freiburg1/rgbd_dataset_freiburg1_teddy.tgz",
    "https://cvg.cit.tum.de/rgbd/dataset/freiburg1/rgbd_dataset_freiburg1_xyz.tgz",
    "https://cvg.cit.tum.de/rgbd/dataset/freiburg1/rgbd_dataset_freiburg1_rpy.tgz",
]
SEVEN = ["chess", "fire", "heads", "office", "pumpkin", "redkitchen", "stairs"]
EUROC_URLS = [
    "http://robotics.ethz.ch/~asl-datasets/ijrr_euroc_mav_dataset/vicon_room1/V1_01_easy/V1_01_easy.zip",
    "http://robotics.ethz.ch/~asl-datasets/ijrr_euroc_mav_dataset/vicon_room1/V1_02_medium/V1_02_medium.zip",
    "http://robotics.ethz.ch/~asl-datasets/ijrr_euroc_mav_dataset/vicon_room1/V1_03_difficult/V1_03_difficult.zip",
    "http://robotics.ethz.ch/~asl-datasets/ijrr_euroc_mav_dataset/vicon_room2/V2_01_easy/V2_01_easy.zip",
    "http://robotics.ethz.ch/~asl-datasets/ijrr_euroc_mav_dataset/vicon_room2/V2_02_medium/V2_02_medium.zip",
    "http://robotics.ethz.ch/~asl-datasets/ijrr_euroc_mav_dataset/vicon_room2/V2_03_difficult/V2_03_difficult.zip",
    "http://robotics.ethz.ch/~asl-datasets/ijrr_euroc_mav_dataset/machine_hall/MH_01_easy/MH_01_easy.zip",
    "http://robotics.ethz.ch/~asl-datasets/ijrr_euroc_mav_dataset/machine_hall/MH_02_easy/MH_02_easy.zip",
    "http://robotics.ethz.ch/~asl-datasets/ijrr_euroc_mav_dataset/machine_hall/MH_03_medium/MH_03_medium.zip",
    "http://robotics.ethz.ch/~asl-datasets/ijrr_euroc_mav_dataset/machine_hall/MH_04_difficult/MH_04_difficult.zip",
    "http://robotics.ethz.ch/~asl-datasets/ijrr_euroc_mav_dataset/machine_hall/MH_05_difficult/MH_05_difficult.zip",
]
ETH3D = [
    "cables_1", "cables_2", "cables_3", "camera_shake_1", "camera_shake_2", "camera_shake_3",
    "ceiling_1", "ceiling_2", "desk_3", "desk_changing_1", "einstein_1", "einstein_2",
    "einstein_dark", "einstein_flashlight", "einstein_global_light_changes_1", "einstein_global_light_changes_2",
    "einstein_global_light_changes_3", "kidnap_1", "kidnap_dark", "large_loop_1", "mannequin_1",
    "mannequin_3", "mannequin_4", "mannequin_5", "mannequin_7", "mannequin_face_1", "mannequin_face_2",
    "mannequin_face_3", "mannequin_head", "motion_1", "planar_2", "planar_3", "plant_1", "plant_2",
    "plant_3", "plant_4", "plant_5", "plant_dark", "plant_scene_1", "plant_scene_2", "plant_scene_3",
    "reflective_1", "repetitive", "sfm_bench", "sfm_garden", "sfm_house_loop", "sfm_lab_room_1",
    "sfm_lab_room_2", "sofa_1", "sofa_2", "sofa_3", "sofa_4", "sofa_dark_1", "sofa_dark_2",
    "sofa_dark_3", "sofa_shake", "table_3", "table_4", "table_7", "vicon_light_1", "vicon_light_2",
]


def emit_tum(root: pathlib.Path, commands: bool) -> None:
    dest = root / "tum"
    for url in TUM_URLS:
        name = pathlib.PurePosixPath(url).name
        print(f"tum\t{name}\t{url}")
        if commands:
            print(f"mkdir -p {dest}")
            print(f"wget {url} -O {dest / name}")
            print(f"tar -xvzf {dest / name} -C {dest}")


def emit_seven(root: pathlib.Path, commands: bool) -> None:
    dest = root / "7-scenes"
    base = "http://download.microsoft.com/download/2/8/5/28564B23-0828-408F-8631-23B1EFF1DAC8"
    for scene in SEVEN:
        url = f"{base}/{scene}.zip"
        print(f"7-scenes\t{scene}.zip\t{url}")
        if commands:
            print(f"mkdir -p {dest}")
            print(f"wget {url} -O {dest / (scene + '.zip')}")
            print(f"unzip {dest / (scene + '.zip')} -d {dest}")
            print(f"unzip {dest / scene / 'seq-01'} -d {dest / scene}")


def emit_euroc(root: pathlib.Path, commands: bool) -> None:
    dest = root / "euroc"
    for url in EUROC_URLS:
        name = pathlib.PurePosixPath(url).name
        stem = name.removesuffix(".zip")
        print(f"euroc\t{name}\t{url}")
        if commands:
            print(f"mkdir -p {dest}")
            print(f"wget {url} -O {dest / name}")
            print(f"unzip {dest / name} -d {dest / stem}")


def emit_eth3d(root: pathlib.Path, commands: bool) -> None:
    dest = root / "eth3d" / "train"
    for seq in ETH3D:
        url = f"https://www.eth3d.net/data/slam/datasets/{seq}_mono.zip"
        name = f"{seq}_mono.zip"
        print(f"eth3d\t{name}\t{url}")
        if commands:
            print(f"mkdir -p {dest}")
            print(f"wget {url} -O {dest / name}")
            print(f"unzip {dest / name} -d {dest}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--suite", action="append", choices=["all", "tum", "7-scenes", "euroc", "eth3d"], default=None)
    parser.add_argument("--dataset-root", type=pathlib.Path, default=pathlib.Path("datasets"))
    parser.add_argument("--commands", action="store_true", help="Print source-script-like shell commands after each URL row.")
    args = parser.parse_args()

    suites = args.suite or ["all"]
    if "all" in suites:
        suites = ["tum", "7-scenes", "euroc", "eth3d"]
    for suite in suites:
        if suite == "tum":
            emit_tum(args.dataset_root, args.commands)
        elif suite == "7-scenes":
            emit_seven(args.dataset_root, args.commands)
        elif suite == "euroc":
            emit_euroc(args.dataset_root, args.commands)
        elif suite == "eth3d":
            emit_eth3d(args.dataset_root, args.commands)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
