#!/usr/bin/env python3
"""Print a multi-animal DeepLabCut tracking plan without running DeepLabCut."""

from __future__ import annotations

import argparse
from textwrap import indent

TRACK_METHODS = ("ellipse", "box", "skeleton", "ctd")


def py_list(values: list[str] | None, empty: str = "None") -> str:
    if not values:
        return empty
    return "[" + ", ".join(repr(v) for v in values) + "]"


def render_call(name: str, **kwargs) -> str:
    parts = [f"{key}={value}" for key, value in kwargs.items() if value is not None]
    joined = ",\n    ".join(parts)
    return f"deeplabcut.{name}(\n    {joined}\n)"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Print an ordered DeepLabCut multi-animal tracking plan.",
    )
    parser.add_argument("--config", default="CONFIG_PATH", help="Project config path placeholder.")
    parser.add_argument(
        "--video",
        action="append",
        default=[],
        help="Video path or directory placeholder. Repeat for multiple inputs.",
    )
    parser.add_argument("--video-extensions", default="mp4", help="Video extension filter.")
    parser.add_argument("--shuffle", type=int, default=1)
    parser.add_argument("--trainingsetindex", type=int, default=0)
    parser.add_argument("--track-method", choices=TRACK_METHODS, default="ellipse")
    parser.add_argument("--n-tracks", type=int, default=None)
    parser.add_argument(
        "--animal-name",
        action="append",
        default=[],
        help="Optional output individual name. Repeat to build a list.",
    )
    parser.add_argument("--identity-only", action="store_true")
    parser.add_argument("--transformer-checkpoint", default=None)
    parser.add_argument("--n-triplets", type=int, default=1000)
    parser.add_argument("--train-epochs", type=int, default=100)
    parser.add_argument("--destfolder", default=None)
    parser.add_argument("--ctd-conditions", default="CTD_CONDITIONS")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    videos = py_list(args.video, empty="['VIDEO_OR_DIRECTORY']")
    animal_names = py_list(args.animal_name)
    n_tracks = repr(args.n_tracks)
    config = repr(args.config)
    video_extensions = repr(args.video_extensions)
    destfolder = repr(args.destfolder) if args.destfolder is not None else None
    track_method = repr(args.track_method)

    print("DeepLabCut multi-animal tracking plan")
    print("=====================================")
    print()
    print("1. Front-door analysis")
    if args.track_method == "ctd":
        print(
            indent(
                render_call(
                    "analyze_videos",
                    config=config,
                    videos=videos,
                    video_extensions=video_extensions,
                    shuffle=args.shuffle,
                    trainingsetindex=args.trainingsetindex,
                    ctd_tracking="True",
                    ctd_conditions=repr(args.ctd_conditions),
                    auto_track="True",
                    identity_only=repr(args.identity_only),
                    n_tracks=n_tracks,
                    animal_names=animal_names,
                    destfolder=destfolder,
                ),
                "   ",
            )
        )
        print("   CTD tracking happens during analysis, so the manual convert/stitch stages are skipped.")
    else:
        print(
            indent(
                render_call(
                    "analyze_videos",
                    config=config,
                    videos=videos,
                    video_extensions=video_extensions,
                    shuffle=args.shuffle,
                    trainingsetindex=args.trainingsetindex,
                    auto_track="False",
                    destfolder=destfolder,
                ),
                "   ",
            )
        )
        print()
        print("2. Convert detections to tracklets")
        print(
            indent(
                render_call(
                    "convert_detections2tracklets",
                    config=config,
                    videos=videos,
                    video_extensions=video_extensions,
                    shuffle=args.shuffle,
                    trainingsetindex=args.trainingsetindex,
                    overwrite="False",
                    destfolder=destfolder,
                    identity_only=repr(args.identity_only),
                    track_method=track_method,
                ),
                "   ",
            )
        )
        print()
        print("3. Stitch tracklets into tracks")
        stitch_kwargs = {
            "config_path": config,
            "videos": videos,
            "video_extensions": video_extensions,
            "shuffle": args.shuffle,
            "trainingsetindex": args.trainingsetindex,
            "n_tracks": n_tracks,
            "animal_names": animal_names,
            "destfolder": destfolder,
            "track_method": track_method,
            "save_as_csv": "False",
        }
        if args.transformer_checkpoint:
            stitch_kwargs["transformer_checkpoint"] = repr(args.transformer_checkpoint)
        print(indent(render_call("stitch_tracklets", **stitch_kwargs), "   "))

        print()
        print("4. Optional transformer reID upgrade")
        print(
            indent(
                render_call(
                    "transformer_reID",
                    config=config,
                    videos=videos,
                    video_extensions=video_extensions,
                    shuffle=args.shuffle,
                    trainingsetindex=args.trainingsetindex,
                    track_method=track_method,
                    n_tracks=n_tracks,
                    n_triplets=repr(args.n_triplets),
                    train_epochs=repr(args.train_epochs),
                    destfolder=destfolder,
                ),
                "   ",
            )
        )
        print(
            "   The reID wrapper mines triplets, trains the transformer, and stitches with the generated checkpoint."
        )
        if args.transformer_checkpoint:
            print("   If you already have a checkpoint, restitch baseline tracklets with that checkpoint instead of retraining.")

    print()
    print("5. Validation reminders")
    print("   - confirm `_full.pickle`, `_assemblies.pickle`, the tracklet pickle, and the final `.h5`")
    print("   - confirm `n_tracks` and `animal_names` agree")
    print("   - for labeled videos or generic postprocessing, route to the postprocessing sub-skill")
    print("   - this script only prints a plan; it never imports or runs DeepLabCut")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
