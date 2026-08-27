#!/usr/bin/env python3
"""Safe Sana video/world/streaming command planner.

This helper prints command candidates and validation warnings only. It never
imports Sana, downloads weights, opens CUDA, or runs generation. Paths in the
printed commands are ordinary Sana checkout-relative command surfaces; review
and run them only in an environment prepared for the selected workflow.
"""

from __future__ import annotations

import argparse
import json
import math
import shlex
import sys
from pathlib import Path
from typing import Iterable, Sequence

NEGATIVE_PROMPT = (
    "A chaotic sequence with misshapen, deformed limbs in heavy motion blur, sudden disappearance, jump cuts, "
    "jerky movements, rapid shot changes, frames out of sync, inconsistent character shapes, temporal artifacts, "
    "jitter, and ghosting effects, creating a disorienting visual experience."
)

VIDEO_MODELS = {
    "480p": {
        "height": 480,
        "width": 832,
        "frames": 81,
        "config": "configs/sana_video_config/Sana_2000M_480px_AdamW_fsdp.yaml",
        "model_path": "hf://Efficient-Large-Model/SANA-Video_2B_480p/checkpoints/SANA_Video_2B_480p.pth",
        "diffusers_id": "Efficient-Large-Model/SANA-Video_2B_480p_diffusers",
        "flow_shift": 8.0,
    },
    "720p": {
        "height": 704,
        "width": 1280,
        "frames": 81,
        "config": "configs/sana_video_config/Sana_2000M_720px_ltx2vae_AdamW_fsdp.yaml",
        "model_path": "hf://Efficient-Large-Model/SANA-Video_2B_720p/checkpoints/SANA_Video_2B_720p.pth",
        "diffusers_id": "Efficient-Large-Model/SANA-Video_2B_720p_diffusers",
        "flow_shift": 8.0,
    },
}

LONGSANA = {
    "config": "configs/sana_video_config/Sana_2000M_480px_adamW_fsdp_longsana.yaml",
    "model_path": "hf://Efficient-Large-Model/SANA-Video_2B_480p_LongLive/checkpoints/SANA_Video_2B_480p_LongLive.pth",
    "diffusers_id": "Efficient-Large-Model/Sana-Video_2B_480p_LongLive_diffusers",
    "height": 480,
    "width": 832,
    "flow_shift": 7.0,
}

SANA_WM_DEFAULTS = {
    "bidirectional": {
        "config": "hf://Efficient-Large-Model/SANA-WM_bidirectional/config.yaml",
        "model_path": "hf://Efficient-Large-Model/SANA-WM_bidirectional/dit/sana_wm_1600m_720p.safetensors",
    },
    "chunk-causal": {
        "config": "configs/sana_wm/sana_wm_chunk_causal_1600m_720p.yaml",
        "model_path": "hf://Efficient-Large-Model/SANA-WM_chunk_causal/dit/sana_wm_chunk_causal_1600m_720p.safetensors",
    },
}

SANA_STREAMING_DEFAULTS = {
    "long_streaming": {
        "config": "configs/sana_streaming/sana_streaming_2b_720p.yaml",
        "model_path": "hf://Efficient-Large-Model/SANA-Streaming/dit/sana_streaming_ar.pth",
        "num_frames": 969,
        "step": 4,
        "cfg_scale": 1.0,
    },
    "bidirectional_short": {
        "config": "configs/sana_streaming/sana_streaming_bidirectional_2b_720p.yaml",
        "model_path": "hf://Efficient-Large-Model/SANA-Streaming_bidirectional/dit/sana_bidirectional_short.pth",
        "num_frames": 81,
        "step": 50,
        "cfg_scale": 6.0,
    },
}

ALLOWED_ACTION_KEYS = set("wasdijkl")
UPDATED_MAPPING = {
    "w": "forward",
    "s": "back",
    "a": "yaw_left",
    "d": "yaw_right",
    "i": "pitch_up",
    "k": "pitch_down",
    "j": "strafe_left",
    "l": "strafe_right",
}


def q(value: object) -> str:
    return shlex.quote(str(value))


def shell_join(parts: Sequence[object]) -> str:
    return " ".join(q(p) for p in parts)


def line_continue(parts: Sequence[object], *, indent: str = "  ") -> str:
    if not parts:
        return ""
    out = [q(parts[0])]
    for part in parts[1:]:
        out.append("\\\n" + indent + q(part))
    return " ".join(out)


def snap_to_stride_plus_one(n: int, stride: int) -> int:
    if n < 1:
        return 1
    if (n - 1) % stride == 0:
        return n
    floor_cand = n - ((n - 1) % stride)
    ceil_cand = floor_cand + stride
    return floor_cand if (n - floor_cand) < (ceil_cand - n) else ceil_cand


def parse_action(action: str) -> tuple[int, list[str], list[dict[str, object]]]:
    cleaned = "".join(action.replace("，", ",").split())
    if not cleaned:
        raise ValueError("action string is empty")
    total = 0
    warnings: list[str] = []
    rows: list[dict[str, object]] = []
    for raw_segment in cleaned.split(","):
        if not raw_segment or "-" not in raw_segment:
            raise ValueError(f"invalid action segment {raw_segment!r}; expected '<keys>-<frames>'")
        keys_part, frames_text = raw_segment.rsplit("-", 1)
        if not frames_text.isdigit() or int(frames_text) <= 0:
            raise ValueError(f"action segment {raw_segment!r} has non-positive frame count {frames_text!r}")
        frames = int(frames_text)
        keys = keys_part.lower()
        if keys == "none":
            controls: list[str] = []
        else:
            bad = sorted({c for c in keys if c not in ALLOWED_ACTION_KEYS})
            if bad:
                raise ValueError(
                    f"action segment {raw_segment!r} contains unknown keys {bad}; allowed keys are wasdijkl or none"
                )
            duplicate = sorted({c for c in keys if keys.count(c) > 1})
            if duplicate:
                warnings.append(f"segment {raw_segment!r} repeats key(s) {duplicate}; native rollout de-duplicates keys")
            controls = [UPDATED_MAPPING[c] for c in sorted(set(keys))]
        rows.append({"segment": raw_segment, "frames": frames, "controls": controls})
        total += frames
    if any(letter in cleaned for letter in "adjl"):
        warnings.append("updated mapping: a/d are yaw left/right; j/l are strafe left/right")
    return total, warnings, rows


def add_common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--mode", required=True, choices=[
        "sana-video", "sana-video-refiner", "sana-wm", "sana-wm-streaming", "sana-streaming-v2v"
    ])
    parser.add_argument("--output-format", choices=["markdown", "json"], default="markdown")
    parser.add_argument("--check-input-paths", action="store_true", help="Warn when local input paths do not exist.")

    parser.add_argument("--prompt", default="A cat and a dog baking a cake together in a kitchen.")
    parser.add_argument("--negative-prompt", default=NEGATIVE_PROMPT)
    parser.add_argument("--txt-file", default=None, help="Prompt text file for native SANA-Video inference.")
    parser.add_argument("--prompt-file", default="asset/sana_wm/demo_0.txt", help="Prompt file for SANA-WM.")
    parser.add_argument("--image", default="asset/sana_wm/demo_0.png", help="First image for SANA-WM or I2V prompt planning.")
    parser.add_argument("--camera", default=None)
    parser.add_argument("--intrinsics", default=None)
    parser.add_argument("--action", default=None)
    parser.add_argument("--source-video", default="hf://Efficient-Large-Model/SANA-Streaming/source/09_style_transfer_source.mp4")

    parser.add_argument("--resolution", choices=["480p", "720p"], default="480p")
    parser.add_argument("--video-task", choices=["t2v", "i2v"], default="t2v")
    parser.add_argument("--video-family", choices=["standard", "longsana"], default="standard")
    parser.add_argument("--interface", choices=["native", "diffusers"], default="native")

    parser.add_argument("--num-frames", type=int, default=None)
    parser.add_argument("--height", type=int, default=None)
    parser.add_argument("--width", type=int, default=None)
    parser.add_argument("--fps", type=int, default=16)
    parser.add_argument("--steps", type=int, default=None)
    parser.add_argument("--cfg-scale", type=float, default=None)
    parser.add_argument("--flow-shift", type=float, default=None)
    parser.add_argument("--motion-score", type=int, default=30)
    parser.add_argument("--seed", type=int, default=42)

    parser.add_argument("--np", type=int, default=1, help="accelerate process count for native SANA-Video.")
    parser.add_argument("--work-dir", default="output/sana_video_results")
    parser.add_argument("--output-dir", default="results/sana_video_planned")
    parser.add_argument("--output-name", default="output.mp4")
    parser.add_argument("--name", default="demo")

    parser.add_argument("--wm-variant", choices=["bidirectional", "chunk-causal"], default="bidirectional")
    parser.add_argument("--no-refiner", action="store_true")
    parser.add_argument("--offload-vae", action="store_true")
    parser.add_argument("--offload-refiner", action="store_true")
    parser.add_argument("--translation-speed", type=float, default=0.025)
    parser.add_argument("--rotation-speed-deg", type=float, default=0.6)
    parser.add_argument("--refiner-block-size", type=int, default=3)
    parser.add_argument("--refiner-kv-max-frames", type=int, default=11)
    parser.add_argument("--num-frame-per-block", type=int, default=3)
    parser.add_argument("--denoising-step-list", default="1000,960,889,727,0")
    parser.add_argument("--num-cached-blocks", type=int, default=2)
    parser.add_argument("--sink-token", choices=["true", "false"], default="true")
    parser.add_argument("--no-compile", action="store_true")
    parser.add_argument("--streaming-preset", default="medium")
    parser.add_argument("--streaming-encoder", default="libx264")
    parser.add_argument("--stage1-precision", choices=["bf16", "fp8", "fp4"], default="bf16")
    parser.add_argument("--refiner-precision", choices=["bf16", "fp8", "fp4"], default="bf16")
    parser.add_argument("--streaming-v2v-mode", choices=["long_streaming", "bidirectional_short"], default="long_streaming")


def warn_for_missing_paths(args: argparse.Namespace, warnings: list[str], paths: Iterable[str | None]) -> None:
    if not args.check_input_paths:
        return
    for item in paths:
        if not item or str(item).startswith("hf://"):
            continue
        if not Path(item).exists():
            warnings.append(f"local path does not exist yet: {item}")


def plan_sana_video(args: argparse.Namespace, warnings: list[str]) -> list[str]:
    if args.video_family == "longsana":
        frames = args.num_frames if args.num_frames is not None else 321
        if args.resolution != "480p":
            warnings.append("LongSANA public inference plan uses the 480p LongLive checkpoint/config.")
        if args.interface == "diffusers":
            warnings.append("LongSANA diffusers support may require a recent development diffusers install.")
        if (frames - 1) % args.fps != 0:
            warnings.append("LongSANA convention is num_frames = seconds * fps + 1; requested frames are not fps*k+1.")
        if args.cfg_scale not in (None, 1.0):
            warnings.append("LongSANA longlive_flow_euler requires cfg_scale=1.0; overriding non-1.0 plans is unsafe.")
        cmd = [
            "accelerate", "launch", "--mixed_precision=bf16",
            "inference_video_scripts/inference_sana_video.py",
            f"--config={LONGSANA['config']}",
            f"--model_path={LONGSANA['model_path']}",
            f"--work_dir={args.work_dir}",
            f"--txt_file={args.txt_file or 'asset/samples/video_prompts_samples.txt'}",
            "--dataset=samples",
            "--cfg_scale=1.0",
            f"--num_frames={frames}",
        ]
        if args.flow_shift is not None:
            cmd.append(f"--flow_shift={args.flow_shift}")
        return [line_continue(cmd)]

    spec = VIDEO_MODELS[args.resolution]
    height = args.height if args.height is not None else spec["height"]
    width = args.width if args.width is not None else spec["width"]
    frames = args.num_frames if args.num_frames is not None else spec["frames"]
    steps = args.steps if args.steps is not None else 50
    cfg = args.cfg_scale if args.cfg_scale is not None else 6.0
    flow = args.flow_shift if args.flow_shift is not None else spec["flow_shift"]
    if args.resolution == "720p":
        warnings.append("720p uses the LTX-2 VAE path and normally needs substantially more VRAM than 480p.")
    if args.video_task == "i2v" and not args.txt_file:
        warnings.append("native I2V expects prompt text lines containing '<image>' followed by an image path.")
    warn_for_missing_paths(args, warnings, [args.txt_file, args.image if args.video_task == "i2v" else None])

    if args.interface == "diffusers":
        warnings.append("Diffusers commands require a diffusers build that includes SanaVideoPipeline / SanaImageToVideoPipeline.")
        pipe_class = "SanaImageToVideoPipeline" if args.video_task == "i2v" else "SanaVideoPipeline"
        snippet = f"""python - <<'PY'
import torch
from diffusers import {pipe_class}
from diffusers.utils import export_to_video, load_image
pipe = {pipe_class}.from_pretrained({spec['diffusers_id']!r}, torch_dtype=torch.bfloat16)
pipe.text_encoder.to(torch.bfloat16)
pipe.vae.to(torch.float32)
pipe.to('cuda')
prompt = {args.prompt!r} + ' motion score: {int(args.motion_score)}.'
kwargs = dict(prompt=prompt, negative_prompt={args.negative_prompt!r}, height={height}, width={width}, frames={frames}, guidance_scale={cfg}, num_inference_steps={steps}, generator=torch.Generator(device='cuda').manual_seed({args.seed}))
"""
        if args.video_task == "i2v":
            snippet += f"kwargs['image'] = load_image({args.image!r})\n"
        snippet += f"video = pipe(**kwargs).frames[0]\nexport_to_video(video, {args.output_name!r}, fps={args.fps})\nPY"
        return [snippet]

    cmd = [
        "bash", "inference_video_scripts/inference_sana_video.sh",
        "--np", args.np,
        "--config", spec["config"],
        "--model_path", spec["model_path"],
        f"--txt_file={args.txt_file or ('asset/samples/sample_i2v.txt' if args.video_task == 'i2v' else 'asset/samples/video_prompts_samples.txt')}",
        "--cfg_scale", cfg,
        "--motion_score", int(args.motion_score),
        "--flow_shift", flow,
        "--work_dir", args.work_dir,
    ]
    if args.video_task == "i2v":
        cmd.append("--task=ltx")
    if frames != spec["frames"]:
        cmd.extend(["--num_frames", frames])
    return [line_continue(cmd)]


def plan_refiner(args: argparse.Namespace, warnings: list[str]) -> list[str]:
    spec = VIDEO_MODELS["720p"]
    height = args.height if args.height is not None else 704
    width = args.width if args.width is not None else 1280
    frames = args.num_frames if args.num_frames is not None else 81
    steps = args.steps if args.steps is not None else 50
    cfg = args.cfg_scale if args.cfg_scale is not None else 6.0
    warnings.append("SANA-Video + LTX-2 refiner loads both SANA-Video and LTX-2 components; plan for high VRAM or CPU offload.")
    warnings.append("The refiner path is for video generation; do not use it for image-only requests.")
    cmd = [
        "python", "app/sana_video_refiner_pipeline_diffusers.py",
        "--sana_model_id", spec["diffusers_id"],
        "--ltx2_model_id", "Lightricks/LTX-2",
        "--prompt", args.prompt,
        "--negative_prompt", args.negative_prompt,
        "--sana_height", height,
        "--sana_width", width,
        "--sana_frames", frames,
        "--motion_score", int(args.motion_score),
        "--sana_guidance_scale", cfg,
        "--sana_num_steps", steps,
        "--frame_rate", float(args.fps),
        "--seed", args.seed,
        "--output_path", args.output_name,
    ]
    return [line_continue(cmd)]


def plan_wm(args: argparse.Namespace, warnings: list[str]) -> list[str]:
    defaults = SANA_WM_DEFAULTS[args.wm_variant]
    frames = args.num_frames if args.num_frames is not None else (961 if args.wm_variant == "chunk-causal" else 161)
    snapped = snap_to_stride_plus_one(frames, 8)
    if snapped != frames:
        warnings.append(f"SANA-WM LTX-2 VAE prefers num_frames=8*k+1; {frames} would snap near {snapped}.")
    if args.action:
        try:
            total, action_warnings, _ = parse_action(args.action)
            warnings.extend(action_warnings)
            if total + 1 < frames:
                warnings.append(f"action rollout has {total + 1} poses but num_frames={frames}; generation will be truncated to action length.")
            elif total not in {frames, frames - 1}:
                warnings.append(f"action duration is {total} frames; common convention is num_frames-1={frames - 1}.")
        except ValueError as exc:
            warnings.append(f"invalid action DSL: {exc}")
    elif not args.camera:
        warnings.append("SANA-WM needs exactly one of --action or --camera; this plan uses no trajectory input yet.")
    warn_for_missing_paths(args, warnings, [args.image, args.prompt_file, args.camera, args.intrinsics])
    if args.intrinsics is None:
        warnings.append("Without --intrinsics, SANA-WM estimates intrinsics with Pi3X and aborts if FOV is outside 25-120 degrees.")
    if args.wm_variant == "chunk-causal":
        warnings.append("Chunk-causal Stage-1 teacher may show artifacts; keep the refiner unless planning fast Stage-1 debugging.")
    cmd = [
        "python", "inference_video_scripts/wm/inference_sana_wm.py",
        "--config", defaults["config"],
        "--model_path", defaults["model_path"],
        "--image", args.image,
        "--prompt", args.prompt_file,
        "--num_frames", frames,
        "--fps", args.fps,
        "--step", args.steps if args.steps is not None else 60,
        "--cfg_scale", args.cfg_scale if args.cfg_scale is not None else 5.0,
        "--output_dir", args.output_dir,
        "--name", args.name,
    ]
    if args.action:
        cmd.extend(["--action", args.action, "--translation_speed", args.translation_speed, "--rotation_speed_deg", args.rotation_speed_deg])
    if args.camera:
        cmd.extend(["--camera", args.camera])
    if args.intrinsics:
        cmd.extend(["--intrinsics", args.intrinsics])
    if args.flow_shift is not None:
        cmd.extend(["--flow_shift", args.flow_shift])
    if args.no_refiner:
        cmd.append("--no_refiner")
    if args.offload_vae:
        cmd.append("--offload_vae")
    if args.offload_refiner:
        cmd.append("--offload_refiner")
    if args.wm_variant == "chunk-causal" and not args.no_refiner:
        cmd.append("--offload_refiner")
    return [line_continue(cmd)]


def plan_wm_streaming(args: argparse.Namespace, warnings: list[str]) -> list[str]:
    frames = args.num_frames if args.num_frames is not None else 241
    stride = 8 * args.refiner_block_size
    snapped = snap_to_stride_plus_one(frames, stride)
    if snapped != frames:
        warnings.append(f"SANA-WM streaming snaps num_frames to {stride}*k+1; {frames} would snap near {snapped}.")
    if args.stage1_precision == "fp4" or args.refiner_precision == "fp4":
        warnings.append("fp4/NVFP4 requires Blackwell-class GPUs and Transformer Engine >= 2.x.")
    if args.stage1_precision == "fp8" or args.refiner_precision == "fp8":
        warnings.append("fp8 requires Hopper-or-newer GPUs and Transformer Engine >= 2.x.")
    if args.no_compile:
        warnings.append("--no_compile is useful for smoke/debug runs but slower than the canonical streaming recipe.")
    if args.action:
        try:
            total, action_warnings, _ = parse_action(args.action)
            warnings.extend(action_warnings)
            if total + 1 < frames:
                warnings.append(f"action rollout has {total + 1} poses but num_frames={frames}; generation will be truncated to action length.")
        except ValueError as exc:
            warnings.append(f"invalid action DSL: {exc}")
    elif not args.camera:
        warnings.append("SANA-WM streaming needs exactly one of --action or --camera; this plan uses no trajectory input yet.")
    warn_for_missing_paths(args, warnings, [args.image, args.prompt_file, args.camera, args.intrinsics])
    cmd = [
        "python", "inference_video_scripts/wm/inference_sana_wm_streaming.py",
        "--image", args.image,
        "--prompt", args.prompt_file,
        "--num_frames", frames,
        "--fps", args.fps,
        "--output_dir", args.output_dir,
        "--name", args.name,
        "--denoising_step_list", args.denoising_step_list,
        "--num_frame_per_block", args.num_frame_per_block,
        "--refiner_block_size", args.refiner_block_size,
        "--refiner_kv_max_frames", args.refiner_kv_max_frames,
        "--num_cached_blocks", args.num_cached_blocks,
        "--streaming_preset", args.streaming_preset,
        "--streaming_encoder", args.streaming_encoder,
        "--stage1_precision", args.stage1_precision,
        "--refiner_precision", args.refiner_precision,
    ]
    if args.action:
        cmd.extend(["--action", args.action, "--translation_speed", args.translation_speed, "--rotation_speed_deg", args.rotation_speed_deg])
    if args.camera:
        cmd.extend(["--camera", args.camera])
    if args.intrinsics:
        cmd.extend(["--intrinsics", args.intrinsics])
    if args.no_compile:
        cmd.append("--no_compile")
    if args.offload_vae:
        cmd.append("--offload_vae")
    if args.offload_refiner:
        cmd.append("--offload_refiner")
    return [line_continue(cmd)]


def plan_streaming_v2v(args: argparse.Namespace, warnings: list[str]) -> list[str]:
    spec = SANA_STREAMING_DEFAULTS[args.streaming_v2v_mode]
    frames = args.num_frames if args.num_frames is not None else spec["num_frames"]
    steps = args.steps if args.steps is not None else spec["step"]
    cfg = args.cfg_scale if args.cfg_scale is not None else spec["cfg_scale"]
    if args.streaming_v2v_mode == "long_streaming":
        warnings.append("long_streaming requires a source video with at least num_frames decoded frames; short decodes raise an error.")
        if args.sink_token == "false":
            warnings.append("long_streaming defaults to sink-token caching; disabling it is an ablation-quality change.")
    else:
        warnings.append("bidirectional_short uses a default negative prompt and flow-DPM sampling; it is the 5-second editing path.")
    warn_for_missing_paths(args, warnings, [args.source_video])
    cmd = [
        "python", "inference_video_scripts/v2v/inference_sana_streaming.py",
        "--mode", args.streaming_v2v_mode,
        "--config", spec["config"],
        "--model_path", spec["model_path"],
        "--prompt", args.prompt,
        "--video_path", args.source_video,
        "--num_frames", frames,
        "--height", args.height if args.height is not None else 704,
        "--width", args.width if args.width is not None else 1280,
        "--fps", args.fps,
        "--step", steps,
        "--cfg_scale", cfg,
        "--output_dir", args.output_dir,
        "--output_name", args.output_name,
    ]
    if args.flow_shift is not None:
        cmd.extend(["--flow_shift", args.flow_shift])
    if args.streaming_v2v_mode == "long_streaming":
        cmd.extend(["--num_cached_blocks", args.num_cached_blocks, "--sink_token", args.sink_token])
    if args.negative_prompt != NEGATIVE_PROMPT or args.streaming_v2v_mode == "bidirectional_short":
        cmd.extend(["--negative_prompt", args.negative_prompt])
    return [line_continue(cmd)]


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    add_common(parser)
    args = parser.parse_args(argv)

    warnings: list[str] = ["planner only: commands are printed, not executed"]
    commands: list[str]
    if args.mode == "sana-video":
        commands = plan_sana_video(args, warnings)
    elif args.mode == "sana-video-refiner":
        commands = plan_refiner(args, warnings)
    elif args.mode == "sana-wm":
        commands = plan_wm(args, warnings)
    elif args.mode == "sana-wm-streaming":
        commands = plan_wm_streaming(args, warnings)
    elif args.mode == "sana-streaming-v2v":
        commands = plan_streaming_v2v(args, warnings)
    else:  # pragma: no cover
        parser.error(f"unsupported mode {args.mode}")

    payload = {
        "mode": args.mode,
        "commands": commands,
        "warnings": warnings,
        "validation_helpers": [
            "Run validate_camera_controls.py for --action/--camera/--intrinsics before world-model generation.",
            "Use ffprobe or imageio/decord to check the resulting MP4 frame count after generation.",
        ],
    }
    if args.output_format == "json":
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"# Planned Sana command: {args.mode}\n")
        for idx, command in enumerate(commands, 1):
            print(f"## Command {idx}\n")
            print("```bash")
            print(command)
            print("```\n")
        print("## Warnings")
        for warning in warnings:
            print(f"- {warning}")
        print("\n## Follow-up validation")
        for item in payload["validation_helpers"]:
            print(f"- {item}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
