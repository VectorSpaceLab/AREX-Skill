#!/usr/bin/env python3
"""Build safe AB3DMOT post-processing, evaluation, and visualization commands.

This script prints command sequences only. It does not import AB3DMOT modules,
read result files, modify outputs, or require dataset access.
"""

import argparse
import shlex
from typing import List, Optional, Sequence

CONF_THRESHOLDS = {
    "KITTI": {
        "pointrcnn": {"Car": 3.240738, "Pedestrian": 2.683133, "Cyclist": 3.645319},
    },
    "nuScenes": {
        "megvii": {
            "Car": 0.262545,
            "Pedestrian": 0.217600,
            "Truck": 0.294967,
            "Trailer": 0.292775,
            "Bus": 0.440060,
            "Motorcycle": 0.314693,
            "Bicycle": 0.284720,
        },
        "centerpoint": {
            "Car": 0.269231,
            "Pedestrian": 0.410000,
            "Truck": 0.300000,
            "Trailer": 0.372632,
            "Bus": 0.430000,
            "Motorcycle": 0.368667,
            "Bicycle": 0.394146,
        },
    },
}

STEP_CHOICES = (
    "auto",
    "threshold",
    "visualize",
    "kitti-3d",
    "kitti-2d",
    "kitti-submission",
    "nuscenes-official",
    "nuscenes-quick",
    "nuscenes-submission",
)


def shell_join(parts: Sequence[object]) -> str:
    return " ".join(shlex.quote(str(part)) for part in parts)


def cmd(*parts: object) -> str:
    return shell_join(parts)


def detector_from_result_sha(result_sha: str) -> str:
    return result_sha.split("_", 1)[0]


def default_detector(dataset: str) -> str:
    return "pointrcnn" if dataset == "KITTI" else "megvii"


def default_result_sha(dataset: str, split: str, num_hypo: int, det_name: Optional[str]) -> str:
    detector = det_name or default_detector(dataset)
    return f"{detector}_{split}_H{num_hypo}"


def resolve_steps(dataset: str, split: str, requested: Sequence[str]) -> List[str]:
    if not requested or "auto" in requested:
        if dataset == "KITTI":
            if split == "test":
                return ["threshold", "kitti-submission", "visualize"]
            return ["kitti-3d", "kitti-2d", "threshold", "visualize"]
        if split == "test":
            return ["nuscenes-official", "nuscenes-submission", "threshold", "visualize"]
        return ["nuscenes-official", "nuscenes-quick", "threshold", "visualize"]
    return list(requested)


def add_header(lines: List[str], title: str) -> None:
    lines.append("")
    lines.append(f"# {title}")


def add_threshold_notes(lines: List[str], dataset: str, result_sha: str) -> None:
    det_name = detector_from_result_sha(result_sha)
    thresholds = CONF_THRESHOLDS.get(dataset, {}).get(det_name)
    if thresholds is None:
        lines.append(
            f"# WARNING: AB3DMOT threshold table support for dataset={dataset!r}, detector={det_name!r} "
            "is not known to this helper. The threshold script may fail unless the running repo supports it."
        )
        return
    formatted = ", ".join(f"{cat}={value:g}" for cat, value in thresholds.items())
    lines.append(f"# Track confidence thresholds inferred from result_sha detector {det_name!r}: {formatted}")


def build_kitti(args: argparse.Namespace, steps: Sequence[str]) -> List[str]:
    result_sha = args.result_sha or default_result_sha("KITTI", args.split, args.num_hypo, args.det_name)
    hypo_index = args.hypothesis_index if args.hypothesis_index is not None else args.num_hypo - 1
    thres_sha = f"{result_sha}_thres"
    visualize_sha = args.visualize_sha or (result_sha if args.raw_visualization else thres_sha)

    lines: List[str] = [
        "# AB3DMOT KITTI post-processing command plan",
        "# Run from the AB3DMOT repository root.",
        f"# result_sha={result_sha}; split={args.split}; num_hypo={args.num_hypo}; hypo_index_vis={hypo_index}",
        "set -euo pipefail",
    ]

    if args.preflight:
        add_header(lines, "Preflight expected tracking outputs")
        lines.append(cmd("test", "-d", f"results/KITTI/{result_sha}/data_{hypo_index}"))
        if "threshold" in steps or "visualize" in steps:
            lines.append(cmd("test", "-d", f"results/KITTI/{result_sha}/trk_withid_{hypo_index}"))

    if "kitti-3d" in steps:
        add_header(lines, "KITTI 3D MOT validation evaluation")
        if args.split != "val":
            lines.append("# WARNING: local KITTI metric scripts are intended for validation labels; test metrics require the server.")
        for iou in args.kitti_3d_iou:
            lines.append(cmd("python3", "scripts/KITTI/evaluate.py", result_sha, args.num_hypo, "3D", f"{iou:g}"))
        lines.append("# For the strict Car-only 0.7 IoU report, rerun with --result-sha <det>_Car_val_H<num_hypo> --kitti-3d-iou 0.7.")

    if "kitti-2d" in steps:
        add_header(lines, "KITTI 2D MOT validation evaluation")
        if args.split != "val":
            lines.append("# WARNING: local KITTI 2D validation evaluation needs validation labels; test submission uses the server.")
        lines.append(cmd("python3", "scripts/KITTI/evaluate.py", result_sha, args.num_hypo, "2D", f"{args.kitti_2d_iou:g}"))

    if "threshold" in steps:
        add_header(lines, "Confidence thresholding")
        add_threshold_notes(lines, "KITTI", result_sha)
        lines.append(cmd("python3", "scripts/post_processing/trk_conf_threshold.py", "--dataset", "KITTI", "--result_sha", result_sha, "--num_hypo", args.num_hypo))
        lines.append(f"# Expected thresholded folder: results/KITTI/{thres_sha}/")

    if "kitti-submission" in steps:
        add_header(lines, "KITTI 2D MOT test-server packaging")
        lines.append("# External/manual gate: upload the zipped thresholded data_0 folder to the official KITTI tracking server.")
        lines.append(cmd("test", "-d", f"results/KITTI/{thres_sha}/data_0"))
        lines.append(f"(cd {shlex.quote('results/KITTI/' + thres_sha)} && zip -r {shlex.quote('../' + thres_sha + '_data_0.zip')} data_0)")

    if "visualize" in steps:
        add_header(lines, "Visualization")
        if not args.raw_visualization and args.visualize_sha is None:
            lines.append("# Defaulting to the thresholded result for qualitative visualization. Pass --raw-visualization to use the raw result.")
        vis_parts: List[object] = [
            "python3",
            "scripts/post_processing/visualization.py",
            "--dataset",
            "KITTI",
            "--result_sha",
            visualize_sha,
            "--split",
            args.split,
            "--hypo_index_vis",
            hypo_index,
        ]
        if args.highlight_file:
            vis_parts.extend(["--highlight_file", args.highlight_file])
        lines.append(cmd(*vis_parts))
        lines.append(f"# Expected visualization folders: results/KITTI/{visualize_sha}/trk_image_vis/ and trk_video_vis/")

    return lines


def build_nuscenes(args: argparse.Namespace, steps: Sequence[str]) -> List[str]:
    result_sha = args.result_sha or default_result_sha("nuScenes", args.split, args.num_hypo, args.det_name)
    hypo_index = args.hypothesis_index if args.hypothesis_index is not None else args.num_hypo - 1
    thres_sha = f"{result_sha}_thres"
    visualize_sha = args.visualize_sha or (result_sha if args.raw_visualization else thres_sha)
    version = args.version or ("v1.0-test" if args.split == "test" else "v1.0-trainval")
    render_curves = 0 if args.no_render_curves else 1

    lines: List[str] = [
        "# AB3DMOT nuScenes post-processing command plan",
        "# Run from the AB3DMOT repository root.",
        f"# result_sha={result_sha}; split={args.split}; num_hypo={args.num_hypo}; hypo_index_vis={hypo_index}",
        "set -euo pipefail",
    ]

    if args.preflight:
        add_header(lines, "Preflight expected tracking and conversion outputs")
        lines.append(cmd("test", "-d", f"results/nuScenes/{result_sha}/data_{hypo_index}"))
        if "nuscenes-official" in steps:
            lines.append(cmd("test", "-d", f"data/nuScenes/nuKITTI/tracking/produced/correspondence/{args.split}"))
        if "threshold" in steps or "visualize" in steps:
            lines.append(cmd("test", "-d", f"results/nuScenes/{result_sha}/trk_withid_{hypo_index}"))

    if "nuscenes-official" in steps:
        add_header(lines, "Convert to nuScenes JSON")
        lines.append(cmd("python3", "scripts/nuScenes/export_kitti.py", "kitti_trk_result2nuscenes", "--result_name", result_sha, "--split", args.split))
        lines.append(f"# Expected JSON: results/nuScenes/{result_sha}/results_{args.split}.json")
        if args.split == "test":
            lines.append("# Local official test metrics are unavailable because nuScenes test labels are hidden; submit results_test.json externally.")
        else:
            add_header(lines, "Official nuScenes local evaluation")
            eval_parts: List[object] = [
                "python3",
                "scripts/nuScenes/evaluate.py",
                "--result_path",
                f"./results/nuScenes/{result_sha}/results_{args.split}.json",
                "--eval_set",
                args.split,
                "--dataroot",
                args.dataroot,
                "--version",
                version,
                "--render_curves",
                render_curves,
                "--verbose",
                int(args.verbose),
            ]
            if args.config_path:
                eval_parts.extend(["--config_path", args.config_path])
            if args.render_classes:
                eval_parts.append("--render_classes")
                eval_parts.extend(args.render_classes)
            lines.append(cmd(*eval_parts))
            lines.append(f"# Expected metrics: results/nuScenes/{result_sha}/metrics_summary.json and metrics_details.json")

    if "nuscenes-quick" in steps:
        add_header(lines, "Quick nuScenes validation evaluation")
        if args.split == "test":
            lines.append("# Skipping quick evaluation for test: local test labels are unavailable.")
        else:
            lines.append(cmd("python3", "scripts/nuScenes/evaluate_quick.py", result_sha, args.num_hypo, args.split))
            lines.append("# Quick evaluation is for local trends; official nuScenes metrics require the JSON export and official evaluator.")

    if "threshold" in steps:
        add_header(lines, "Confidence thresholding for visualization")
        add_threshold_notes(lines, "nuScenes", result_sha)
        lines.append("# Do not threshold before official nuScenes scoring unless evaluating a deliberate thresholded operating point.")
        lines.append(cmd("python3", "scripts/post_processing/trk_conf_threshold.py", "--dataset", "nuScenes", "--result_sha", result_sha, "--num_hypo", args.num_hypo))
        lines.append(f"# Expected thresholded folder: results/nuScenes/{thres_sha}/")

    if "nuscenes-submission" in steps:
        add_header(lines, "nuScenes test-server packaging")
        lines.append("# External/manual gate: submit the zipped results_test.json through the official nuScenes tracking server.")
        lines.append(cmd("test", "-f", f"results/nuScenes/{result_sha}/results_{args.split}.json"))
        lines.append(f"(cd {shlex.quote('results/nuScenes/' + result_sha)} && zip -r {shlex.quote('../' + result_sha + '_results_' + args.split + '.zip')} {shlex.quote('results_' + args.split + '.json')})")

    if "visualize" in steps:
        add_header(lines, "Visualization")
        if not args.raw_visualization and args.visualize_sha is None:
            lines.append("# Defaulting to the thresholded result for qualitative visualization. Pass --raw-visualization to use the raw result.")
        lines.append("# nuScenes visualization requires converted nuKITTI tracking images/calibration for the requested split.")
        vis_parts = [
            "python3",
            "scripts/post_processing/visualization.py",
            "--dataset",
            "nuScenes",
            "--result_sha",
            visualize_sha,
            "--split",
            args.split,
            "--hypo_index_vis",
            hypo_index,
        ]
        if args.highlight_file:
            vis_parts.extend(["--highlight_file", args.highlight_file])
        lines.append(cmd(*vis_parts))
        lines.append(f"# Expected visualization folders: results/nuScenes/{visualize_sha}/trk_image_vis/ and trk_video_vis/")

    return lines


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Print AB3DMOT evaluation, thresholding, submission, and visualization command sequences.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--dataset", choices=["KITTI", "nuScenes"], required=True)
    parser.add_argument("--split", default="val", choices=["train", "val", "test"], help="Dataset split used by the result folder.")
    parser.add_argument("--det-name", default=None, help="Detector name used only when --result-sha is omitted.")
    parser.add_argument("--result-sha", default=None, help="Result folder basename under results/<dataset>/.")
    parser.add_argument("--num-hypo", type=int, default=1, help="Number of hypotheses passed to AB3DMOT evaluators/thresholding.")
    parser.add_argument("--hypothesis-index", type=int, default=None, help="Zero-indexed hypothesis folder for visualization/preflight. Defaults to num_hypo - 1.")
    parser.add_argument("--steps", nargs="*", choices=STEP_CHOICES, default=["auto"], help="Command sections to print.")
    parser.add_argument("--no-preflight", dest="preflight", action="store_false", help="Do not print test -d/test -f preflight commands.")
    parser.set_defaults(preflight=True)

    parser.add_argument("--kitti-3d-iou", nargs="+", type=float, default=[0.25, 0.5], help="KITTI 3D IoU thresholds to print when using kitti-3d.")
    parser.add_argument("--kitti-2d-iou", type=float, default=0.5, help="KITTI 2D IoU threshold to print when using kitti-2d.")

    parser.add_argument("--dataroot", default="./data/nuScenes/data", help="nuScenes dataroot for official evaluation.")
    parser.add_argument("--version", default=None, help="nuScenes version. Defaults to v1.0-trainval except test uses v1.0-test.")
    parser.add_argument("--config-path", default=None, help="Optional nuScenes tracking config JSON path.")
    parser.add_argument("--no-render-curves", action="store_true", help="Pass --render_curves 0 to official nuScenes evaluation.")
    parser.add_argument("--verbose", type=int, choices=[0, 1], default=1, help="Verbosity flag for official nuScenes evaluation.")
    parser.add_argument("--render-classes", nargs="*", default=None, help="Optional class names for nuScenes curve rendering.")

    parser.add_argument("--raw-visualization", action="store_true", help="Visualize the raw result_sha instead of defaulting to result_sha_thres.")
    parser.add_argument("--visualize-sha", default=None, help="Explicit result SHA to pass to visualization.py.")
    parser.add_argument("--highlight-file", default=None, help="Optional highlight file for visualization.py.")
    return parser.parse_args(argv)


def validate_args(args: argparse.Namespace) -> None:
    if args.num_hypo < 1:
        raise SystemExit("--num-hypo must be >= 1")
    if args.hypothesis_index is not None and args.hypothesis_index < 0:
        raise SystemExit("--hypothesis-index must be >= 0")
    steps = resolve_steps(args.dataset, args.split, args.steps)
    invalid_for_dataset = []
    if args.dataset == "KITTI":
        invalid_for_dataset = [step for step in steps if step.startswith("nuscenes-")]
    elif args.dataset == "nuScenes":
        invalid_for_dataset = [step for step in steps if step.startswith("kitti-")]
    if invalid_for_dataset:
        raise SystemExit(f"Steps not valid for {args.dataset}: {', '.join(invalid_for_dataset)}")


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    validate_args(args)
    steps = resolve_steps(args.dataset, args.split, args.steps)
    lines = build_kitti(args, steps) if args.dataset == "KITTI" else build_nuscenes(args, steps)
    print("\n".join(lines).rstrip() + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
