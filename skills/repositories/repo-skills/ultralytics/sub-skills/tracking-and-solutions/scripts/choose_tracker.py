#!/usr/bin/env python3
"""Recommend an Ultralytics tracker YAML for a tracking or solutions workflow."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass


@dataclass(frozen=True)
class TrackerProfile:
    yaml_name: str
    tracker_type: str
    summary: str
    strengths: tuple[str, ...]
    caveats: tuple[str, ...]
    optional_packages: tuple[str, ...] = ()
    optional_notes: tuple[str, ...] = ()


TRACKERS = {
    "botsort": TrackerProfile(
        yaml_name="botsort.yaml",
        tracker_type="botsort",
        summary="Default stable general-purpose tracker with global motion compensation and optional ReID.",
        strengths=("general", "moving_camera", "stable_ids", "reid"),
        caveats=("ReID is disabled by default; enabling it adds model/backend compute.",),
        optional_notes=("with_reid=True can use native detector features for compatible YOLO detect models or a separate ReID model.",),
    ),
    "bytetrack": TrackerProfile(
        yaml_name="bytetrack.yaml",
        tracker_type="bytetrack",
        summary="Fast two-stage low-confidence recovery baseline without ReID.",
        strengths=("speed", "simple", "low_confidence"),
        caveats=("No appearance ReID; identity switches can persist in crowded or long-occlusion scenes.",),
    ),
    "ocsort": TrackerProfile(
        yaml_name="ocsort.yaml",
        tracker_type="ocsort",
        summary="Observation-centric SORT tracker without ReID.",
        strengths=("motion", "simple", "no_reid"),
        caveats=("Use ByteTrack-style second pass only if use_byte=True in a copied config.",),
    ),
    "deepocsort": TrackerProfile(
        yaml_name="deepocsort.yaml",
        tracker_type="deepocsort",
        summary="OC-SORT variant with optional appearance features and optional camera motion compensation.",
        strengths=("reid", "stable_ids", "occlusion"),
        caveats=("with_reid=False by default; enabling ReID requires more compute and a compatible model/backend.",),
        optional_notes=("Set gmc_method for moving-camera scenes and validate the selected ReID model format separately.",),
    ),
    "fasttrack": TrackerProfile(
        yaml_name="fasttrack.yaml",
        tracker_type="fasttrack",
        summary="Lightweight occlusion-aware ByteTrack-style tracker with Kalman rollback.",
        strengths=("occlusion", "speed", "no_reid"),
        caveats=("Occlusion knobs are useful but need scene-specific tuning.",),
    ),
    "tracktrack": TrackerProfile(
        yaml_name="tracktrack.yaml",
        tracker_type="tracktrack",
        summary="Multi-cue tracker with iterative association, Track-Aware Initialization, GMC, and optional ReID.",
        strengths=("occlusion", "moving_camera", "reid", "stable_ids"),
        caveats=("More tuning-sensitive than ByteTrack/BOTSort; ReID remains optional.",),
        optional_notes=("lost_match_thr, association weights, and with_reid should be tuned on representative video clips.",),
    ),
}

GOAL_ORDER = {
    "general": ("botsort", "bytetrack", "ocsort"),
    "speed": ("bytetrack", "fasttrack", "botsort"),
    "occlusion": ("fasttrack", "tracktrack", "botsort"),
    "moving-camera": ("botsort", "tracktrack", "deepocsort"),
    "reid": ("botsort", "deepocsort", "tracktrack"),
    "simple": ("bytetrack", "ocsort", "botsort"),
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Recommend a built-in Ultralytics tracker YAML and note optional dependency/backend considerations.",
    )
    parser.add_argument(
        "--goal",
        choices=sorted(GOAL_ORDER),
        default="general",
        help="Primary tracking goal or scene condition.",
    )
    parser.add_argument("--moving-camera", action="store_true", help="Prefer trackers with global motion compensation.")
    parser.add_argument("--prefer-stable-ids", action="store_true", help="Prefer trackers that can reduce ID switches.")
    parser.add_argument("--prefer-speed", action="store_true", help="Prefer lower-overhead trackers over ReID-heavy choices.")
    parser.add_argument("--needs-reid", action="store_true", help="The workflow explicitly needs appearance/ReID guidance.")
    parser.add_argument(
        "--needs-exported-reid",
        action="store_true",
        help="Mention that a separate exported ReID model may be required for non-auto ReID use.",
    )
    parser.add_argument("--json", action="store_true", help="Emit a JSON recommendation instead of text.")
    return parser


def score_tracker(key: str, args: argparse.Namespace) -> int:
    profile = TRACKERS[key]
    score = 0
    preferred = GOAL_ORDER[args.goal]
    if key in preferred:
        score += (len(preferred) - preferred.index(key)) * 10
    if args.moving_camera and "moving_camera" in profile.strengths:
        score += 8
    if args.prefer_stable_ids and "stable_ids" in profile.strengths:
        score += 7
    if args.prefer_speed and "speed" in profile.strengths:
        score += 7
    if args.prefer_speed and "reid" in profile.strengths:
        score -= 3
    if args.needs_reid and "reid" in profile.strengths:
        score += 10
    if args.needs_reid and "reid" not in profile.strengths:
        score -= 8
    return score


def recommendation(args: argparse.Namespace) -> dict[str, object]:
    ranked_keys = sorted(TRACKERS, key=lambda key: (-score_tracker(key, args), TRACKERS[key].yaml_name))
    chosen = TRACKERS[ranked_keys[0]]
    alternatives = [TRACKERS[key].yaml_name for key in ranked_keys[1:4]]
    notes = list(chosen.optional_notes)
    if args.needs_reid:
        notes.append("Enable ReID only in a copied YAML for botsort, deepocsort, or tracktrack; validate compute and model compatibility first.")
    if args.needs_exported_reid:
        notes.append("For non-auto ReID, prepare a compatible classification/ReID model path or exported model and test on a short clip before full runs.")
    if args.moving_camera:
        notes.append("For moving cameras, keep or enable a suitable gmc_method such as sparseOptFlow unless validation shows it hurts.")
    return {
        "recommended_yaml": chosen.yaml_name,
        "tracker_type": chosen.tracker_type,
        "summary": chosen.summary,
        "alternatives": alternatives,
        "caveats": list(chosen.caveats),
        "optional_packages": list(chosen.optional_packages),
        "notes": notes,
        "example_cli": f"yolo track model=yolo26n.pt source=video.mp4 tracker={chosen.yaml_name} show=False",
        "example_python": f'model.track("video.mp4", tracker="{chosen.yaml_name}", show=False)',
    }


def print_text(result: dict[str, object]) -> None:
    print(f"Recommended tracker: {result['recommended_yaml']} ({result['tracker_type']})")
    print(f"Why: {result['summary']}")
    print("Alternatives: " + ", ".join(result["alternatives"]))
    if result["caveats"]:
        print("Caveats:")
        for item in result["caveats"]:
            print(f"- {item}")
    if result["notes"]:
        print("Notes:")
        for item in result["notes"]:
            print(f"- {item}")
    print("CLI example:")
    print(result["example_cli"])
    print("Python example:")
    print(result["example_python"])


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    result = recommendation(args)
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print_text(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
