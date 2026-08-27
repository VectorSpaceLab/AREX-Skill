#!/usr/bin/env python3
"""Statically summarize generative-models video sampling CLIs.

This helper intentionally avoids importing the source repository, torch, CUDA,
checkpoints, or video dependencies. It is safe to run from any current working
directory and prints metadata distilled from the standalone video sampling
scripts and their config filenames.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Dict, Iterable, List

COMMON_NOTES = [
    "Full sampling is checkpoint-bound and normally CUDA/GPU-bound.",
    "This helper is static metadata only: it imports no repo modules and opens no checkpoints.",
    "Python Fire commands pass args as --name value or --name=value; quote list values.",
]

SCRIPT_METADATA: Dict[str, Dict[str, Any]] = {
    "svd-sv3d": {
        "source_script": "scripts/sampling/simple_video_sample.py",
        "entrypoint": "sample",
        "description": "Image-to-video and image-to-multi-view sampling for SVD, SVD-XT, SV3D_u, and SV3D_p.",
        "accepted_inputs": [
            "single .jpg/.jpeg/.png image",
            "directory containing .jpg/.jpeg/.png images",
        ],
        "unsupported_inputs": ["glob patterns", ".gif/.mp4 video files"],
        "outputs": [
            "<output_folder>/<counter>.jpg copied/processed conditioning image",
            "<output_folder>/<counter>.mp4 generated video",
        ],
        "parameters": {
            "input_path": "assets/test_image.png",
            "num_frames": None,
            "num_steps": None,
            "version": "svd",
            "fps_id": 6,
            "motion_bucket_id": 127,
            "cond_aug": 0.02,
            "seed": 23,
            "decoding_t": 14,
            "device": "cuda",
            "output_folder": None,
            "elevations_deg": 10.0,
            "azimuths_deg": None,
            "image_frame_ratio": None,
            "verbose": False,
        },
        "versions": {
            "svd": {
                "num_frames": 14,
                "num_steps": 25,
                "config": "scripts/sampling/configs/svd.yaml",
                "checkpoint": "checkpoints/svd.safetensors",
                "default_output_folder": "outputs/simple_video_sample/svd/",
                "resolution_target": "576x1024",
            },
            "svd_xt": {
                "num_frames": 25,
                "num_steps": 30,
                "config": "scripts/sampling/configs/svd_xt.yaml",
                "checkpoint": "checkpoints/svd_xt.safetensors",
                "default_output_folder": "outputs/simple_video_sample/svd_xt/",
                "resolution_target": "576x1024",
            },
            "svd_image_decoder": {
                "num_frames": 14,
                "num_steps": 25,
                "config": "scripts/sampling/configs/svd_image_decoder.yaml",
                "checkpoint": "checkpoints/svd_image_decoder.safetensors",
                "default_output_folder": "outputs/simple_video_sample/svd_image_decoder/",
                "resolution_target": "576x1024",
            },
            "svd_xt_image_decoder": {
                "num_frames": 25,
                "num_steps": 30,
                "config": "scripts/sampling/configs/svd_xt_image_decoder.yaml",
                "checkpoint": "checkpoints/svd_xt_image_decoder.safetensors",
                "default_output_folder": "outputs/simple_video_sample/svd_xt_image_decoder/",
                "resolution_target": "576x1024",
            },
            "sv3d_u": {
                "num_frames": 21,
                "num_steps": 50,
                "config": "scripts/sampling/configs/sv3d_u.yaml",
                "checkpoint": "checkpoints/sv3d_u.safetensors",
                "default_output_folder": "outputs/simple_video_sample/sv3d_u/",
                "resolution_target": "576x576",
                "cond_aug_override": 1e-5,
            },
            "sv3d_p": {
                "num_frames": 21,
                "num_steps": 50,
                "config": "scripts/sampling/configs/sv3d_p.yaml",
                "checkpoint": "checkpoints/sv3d_p.safetensors",
                "default_output_folder": "outputs/simple_video_sample/sv3d_p/",
                "resolution_target": "576x576",
                "cond_aug_override": 1e-5,
                "camera_requirements": {
                    "elevations_deg": "scalar or exactly 21 values",
                    "azimuths_deg": "omitted for default orbit or exactly 21 values",
                },
            },
        },
        "safe_templates": [
            "python scripts/sampling/simple_video_sample.py --input_path inputs/object.png --version svd --decoding_t 8",
            "python scripts/sampling/simple_video_sample.py --input_path inputs/object.png --version svd_xt --num_steps 20 --decoding_t 4",
            "python scripts/sampling/simple_video_sample.py --input_path inputs/object.png --version sv3d_u --decoding_t 4",
            "python scripts/sampling/simple_video_sample.py --input_path inputs/object.png --version sv3d_p --elevations_deg 15.0 --decoding_t 4",
        ],
        "low_vram": ["lower decoding_t", "use fewer num_steps for speed, not primarily memory"],
    },
    "sv4d": {
        "source_script": "scripts/sampling/simple_video_sample_4d.py",
        "entrypoint": "sample",
        "description": "Original SV4D video-to-4D sampling with SV3D-generated reference views from the first frame.",
        "accepted_inputs": [
            "single .gif/.mp4 video file",
            "directory containing .jpg/.jpeg/.png frames",
            "glob pattern containing * that resolves to .jpg/.jpeg/.png frames",
        ],
        "outputs": [
            "processed input video <counter>_process_input.mp4",
            "first-frame reference video <counter>_t000.mp4",
            "novel-view videos <counter>_v001.mp4 through <counter>_v008.mp4",
            "diagonal video <counter>_diag.mp4",
        ],
        "parameters": {
            "input_path": "assets/sv4d_videos/test_video1.mp4",
            "output_folder": "outputs/sv4d",
            "num_steps": 20,
            "sv3d_version": "sv3d_u",
            "img_size": 576,
            "fps_id": 6,
            "motion_bucket_id": 127,
            "cond_aug": 1e-5,
            "seed": 23,
            "encoding_t": 8,
            "decoding_t": 4,
            "device": "cuda",
            "elevations_deg": 10.0,
            "azimuths_deg": None,
            "image_frame_ratio": 0.917,
            "verbose": False,
            "remove_bg": False,
        },
        "config": "scripts/sampling/configs/sv4d.yaml",
        "checkpoints": [
            "checkpoints/sv4d.safetensors",
            "checkpoints/sv3d_u.safetensors or checkpoints/sv3d_p.safetensors",
        ],
        "shape": {
            "script_input_frames": 21,
            "sample_chunk": "5 frames x 8 generated views",
            "outputs": "21 frames x 8 novel views plus diagonal",
            "n_views_total": 9,
            "resolution_target": "576x576",
        },
        "sv3d_reference": {
            "sv3d_version": "sv3d_u or sv3d_p",
            "n_views_sv3d": 21,
            "subsampled_views": [0, 2, 5, 7, 9, 12, 14, 16, 19],
            "elevations_deg": "scalar or exactly 21 values",
            "azimuths_deg": "omitted for default orbit or exactly 21 values",
        },
        "safe_templates": [
            "python scripts/sampling/simple_video_sample_4d.py --input_path inputs/object.mp4 --output_folder outputs/sv4d",
            "python scripts/sampling/simple_video_sample_4d.py --input_path 'frames/*.png' --remove_bg True --encoding_t 1 --decoding_t 1 --img_size 512",
            "python scripts/sampling/simple_video_sample_4d.py --input_path inputs/object.mp4 --sv3d_version sv3d_p --elevations_deg 30.0",
        ],
        "low_vram": ["set encoding_t=1", "set decoding_t=1", "lower img_size to 512 if needed"],
    },
    "sv4d2": {
        "source_script": "scripts/sampling/simple_video_sample_4d2.py",
        "entrypoint": "sample",
        "description": "SV4D 2.0 video-to-4D sampling; mode is selected by model_path basename.",
        "accepted_inputs": [
            "single .gif/.mp4 video file",
            "directory containing .jpg/.jpeg/.png frames",
            "glob pattern containing * that resolves to .jpg/.jpeg/.png frames",
        ],
        "outputs": [
            "processed input video under <output_folder>/<mode>/",
            "novel-view videos <counter>_v001.mp4 through generated view count",
        ],
        "parameters": {
            "input_path": "assets/sv4d_videos/camel.gif",
            "model_path": "checkpoints/sv4d2.safetensors",
            "output_folder": "outputs",
            "num_steps": 50,
            "img_size": 576,
            "n_frames": 21,
            "seed": 23,
            "encoding_t": 8,
            "decoding_t": 4,
            "device": "cuda",
            "elevations_deg": 0.0,
            "azimuths_deg": None,
            "image_frame_ratio": 0.9,
            "verbose": False,
            "remove_bg": False,
        },
        "model_path_basename_assertion": ["sv4d2.safetensors", "sv4d2_8views.safetensors"],
        "modes": {
            "sv4d2": {
                "model_path_basename": "sv4d2.safetensors",
                "config": "scripts/sampling/configs/sv4d2.yaml",
                "checkpoint": "checkpoints/sv4d2.safetensors",
                "chunk": "12 frames x 4 generated views",
                "generated_views": 4,
                "total_views_including_input": 5,
                "default_azimuths_deg": [0, 60, 120, 180, 240],
                "output_subfolder": "sv4d2",
            },
            "sv4d2_8views": {
                "model_path_basename": "sv4d2_8views.safetensors",
                "config": "scripts/sampling/configs/sv4d2_8views.yaml",
                "checkpoint": "checkpoints/sv4d2_8views.safetensors",
                "chunk": "5 frames x 8 generated views",
                "generated_views": 8,
                "total_views_including_input": 9,
                "default_azimuths_deg": [0, 30, 75, 120, 165, 210, 255, 300, 330],
                "output_subfolder": "sv4d2_8views",
            },
        },
        "camera_requirements": {
            "elevations_deg": "scalar or total-view list matching selected basename: 5 for sv4d2, 9 for sv4d2_8views",
            "azimuths_deg": "omitted for defaults or total-view list matching selected basename",
        },
        "safe_templates": [
            "python scripts/sampling/simple_video_sample_4d2.py --input_path inputs/object.gif --model_path checkpoints/sv4d2.safetensors --output_folder outputs",
            "python scripts/sampling/simple_video_sample_4d2.py --input_path inputs/object.gif --model_path checkpoints/sv4d2_8views.safetensors --output_folder outputs --encoding_t 1 --decoding_t 1",
            "python scripts/sampling/simple_video_sample_4d2.py --input_path 'frames/*.png' --remove_bg True --img_size 512 --n_frames 21",
        ],
        "low_vram": ["set encoding_t=1", "set decoding_t=1", "lower img_size to 512 if needed"],
    },
}

ALIASES = {
    "svd": "svd-sv3d",
    "svd_xt": "svd-sv3d",
    "svd-xt": "svd-sv3d",
    "sv3d": "svd-sv3d",
    "sv3d_u": "svd-sv3d",
    "sv3d_p": "svd-sv3d",
    "simple_video_sample": "svd-sv3d",
    "simple_video_sample.py": "svd-sv3d",
    "simple_video_sample_4d": "sv4d",
    "simple_video_sample_4d.py": "sv4d",
    "simple_video_sample_4d2": "sv4d2",
    "simple_video_sample_4d2.py": "sv4d2",
}


def selected_keys(value: str) -> List[str]:
    normalized = value.strip().lower()
    if normalized == "all":
        return ["svd-sv3d", "sv4d", "sv4d2"]
    return [ALIASES.get(normalized, normalized)]


def build_payload(keys: Iterable[str]) -> Dict[str, Any]:
    missing = [key for key in keys if key not in SCRIPT_METADATA]
    if missing:
        valid = sorted(set(SCRIPT_METADATA) | set(ALIASES) | {"all"})
        raise SystemExit(f"Unknown --script value(s): {', '.join(missing)}. Valid values include: {', '.join(valid)}")
    selected = {key: SCRIPT_METADATA[key] for key in keys}
    return {"notes": COMMON_NOTES, "scripts": selected}


def print_text(payload: Dict[str, Any]) -> None:
    print("Video sampling static CLI inspection")
    print("=" * 36)
    for note in payload["notes"]:
        print(f"- {note}")
    for key, data in payload["scripts"].items():
        print()
        print(f"[{key}] {data['source_script']}")
        print(f"  {data['description']}")
        print("  Parameters/defaults:")
        for name, default in data["parameters"].items():
            print(f"    --{name}: {default!r}")
        if "versions" in data:
            print("  Versions:")
            for version, version_data in data["versions"].items():
                print(
                    "    "
                    f"{version}: frames={version_data['num_frames']} "
                    f"steps={version_data['num_steps']} "
                    f"config={version_data['config']} "
                    f"checkpoint={version_data['checkpoint']}"
                )
        if "modes" in data:
            print("  Modes:")
            for mode, mode_data in data["modes"].items():
                print(
                    "    "
                    f"{mode}: basename={mode_data['model_path_basename']} "
                    f"chunk={mode_data['chunk']} "
                    f"generated_views={mode_data['generated_views']} "
                    f"config={mode_data['config']}"
                )
        if "config" in data:
            print(f"  Config: {data['config']}")
        if "checkpoints" in data:
            print("  Checkpoints:")
            for checkpoint in data["checkpoints"]:
                print(f"    - {checkpoint}")
        print("  Safe templates:")
        for template in data["safe_templates"]:
            print(f"    {template}")


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Statically summarize video sampling CLI defaults, configs, checkpoints, inputs, and safe templates.",
    )
    parser.add_argument(
        "--script",
        default="all",
        help="Which script family to inspect: svd-sv3d, sv4d, sv4d2, or all. Common aliases such as svd, sv3d_p, and simple_video_sample_4d2.py are accepted.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON instead of a human-readable summary.",
    )
    return parser.parse_args(argv)


def main(argv: List[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    keys = selected_keys(args.script)
    payload = build_payload(keys)
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print_text(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
