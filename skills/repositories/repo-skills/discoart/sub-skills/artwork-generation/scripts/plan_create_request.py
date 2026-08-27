#!/usr/bin/env python3
"""Plan a DiscoArt create() request without running generation.

This helper intentionally calls discoart.config.load_config() only. It does not
call discoart.create(), load diffusion/CLIP models, create output directories,
start servers, or download model files.
"""

import argparse
import json
import os
import sys
from pathlib import Path

COMMON_DIFFUSION_PREFIXES = {
    "256": "256x256_diffusion_uncond",
    "512": "512x512_diffusion_uncond_finetune_008100",
    "pulp": "PulpSciFiDiffusion",
    "pixel_art_diffusion_hard": "pixel_art_diffusion_hard_256",
    "pixel_art_diffusion_soft": "pixel_art_diffusion_soft_256",
    "pixelart": "pixelartdiffusion4k",
    "pad": "PADexpanded",
    "watercolor": "watercolordiffusion",
    "portrait": "portrait_generator_v1.5",
}

HEAVY_CLIP_MARKERS = ("RN50x16", "RN50x64", "ViT-L-14", "ViT-L-14-336")
DEFAULT_CLIP_MODELS = ["ViT-B-32::openai", "ViT-B-16::openai", "RN50::openai"]


def build_parser():
    parser = argparse.ArgumentParser(
        description=(
            "Summarize a DiscoArt create() YAML config without running generation "
            "or downloading models."
        )
    )
    parser.add_argument(
        "--config",
        metavar="PATH",
        help="YAML config to normalize via discoart.config.load_config. If omitted, defaults are summarized.",
    )
    parser.add_argument(
        "--check-cuda",
        action="store_true",
        help="Also import torch and report CUDA visibility. Does not allocate tensors or load DiscoArt models.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit a machine-readable JSON summary instead of text.",
    )
    return parser


def fail(message, use_json=False, code=2):
    payload = {"ok": False, "error": message}
    if use_json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print("ERROR: {}".format(message), file=sys.stderr)
    return code


def normalize_config(config_path):
    if config_path:
        path = Path(config_path).expanduser()
        if not path.exists():
            raise FileNotFoundError("config file does not exist: {}".format(path))
        if not path.is_file():
            raise OSError("config path is not a file: {}".format(path))
        load_arg = str(path)
    else:
        load_arg = {}

    try:
        from discoart.config import load_config
    except Exception as exc:  # pragma: no cover - depends on user env
        raise RuntimeError(
            "could not import discoart.config.load_config; install DiscoArt in this Python environment first ({})".format(
                exc
            )
        )

    try:
        return load_config(user_config=load_arg)
    except Exception as exc:
        raise RuntimeError("could not normalize DiscoArt config: {}".format(exc))


def cuda_probe(enabled):
    if not enabled:
        return {"checked": False, "available": None, "advice": "pass --check-cuda to inspect torch.cuda availability"}

    info = {"checked": True, "available": False}
    try:
        import torch
    except Exception as exc:  # pragma: no cover - depends on user env
        info.update({"error": "could not import torch: {}".format(exc)})
        return info

    info["torch_version"] = getattr(torch, "__version__", "unknown")
    try:
        available = bool(torch.cuda.is_available())
        info["available"] = available
        info["device_count"] = int(torch.cuda.device_count()) if available else 0
        if available and info["device_count"]:
            info["device_0"] = torch.cuda.get_device_name(0)
    except Exception as exc:  # pragma: no cover - depends on user env
        info.update({"available": False, "error": "torch CUDA probe failed: {}".format(exc)})
    return info


def as_int(value, default=0):
    try:
        return int(value)
    except Exception:
        return default


def output_dir_for(cfg):
    root = os.environ.get("DISCOART_OUTPUT_DIR", ".")
    name = cfg.get("name_docarray") or "<unknown-name_docarray>"
    return os.path.abspath(os.path.join(root, name))


def local_model_guess(name):
    if not name:
        return {"kind": "missing", "known_prefix": None}
    expanded = os.path.expanduser(str(name))
    if expanded.endswith(('.pt', '.pth')) or os.path.sep in expanded:
        return {"kind": "local-file", "exists": os.path.isfile(expanded), "path": expanded}
    lowered = str(name).lower()
    match = None
    for prefix, full_name in COMMON_DIFFUSION_PREFIXES.items():
        if full_name.lower().startswith(lowered) or lowered.startswith(prefix):
            match = full_name
            break
    return {"kind": "catalog-or-prefix", "known_prefix": match}


def collect_risks(cfg, cuda):
    risks = []

    width_height = cfg.get("width_height") or []
    width = as_int(width_height[0]) if len(width_height) > 0 else 0
    height = as_int(width_height[1]) if len(width_height) > 1 else 0
    pixels = width * height

    if not width or not height:
        risks.append("width_height is missing or invalid; create() expects [width, height].")
    else:
        if width % 64 or height % 64:
            risks.append("width_height should use multiples of 64; DiscoArt may adjust or fail on odd sizes.")
        if min(width, height) < 512:
            risks.append("width_height below 512 is best treated as a smoke-test size, not a normal artwork size.")
        if pixels > 1024 * 1024:
            risks.append("large canvas ({}x{}) can consume substantial VRAM.".format(width, height))

    steps = as_int(cfg.get("steps"), 0)
    skip_steps = as_int(cfg.get("skip_steps"), 0)
    if steps <= 0:
        risks.append("steps must be positive.")
    elif steps < 50:
        risks.append("very low steps may be useful for smoke tests but usually produce poor artwork.")
    elif steps > 500:
        risks.append("steps above 500 can be very slow.")
    if steps and skip_steps >= steps:
        risks.append("skip_steps must be less than steps or there may be no useful denoising left.")

    if cfg.get("init_image") and steps and skip_steps < int(0.4 * steps):
        risks.append("init_image is set but skip_steps is below ~40% of steps; the init image may be heavily overwritten.")
    if cfg.get("perlin_init") and cfg.get("init_image"):
        risks.append("perlin_init overrides/replaces the usual init_image starting state.")

    n_batches = as_int(cfg.get("n_batches"), 1)
    batch_size = as_int(cfg.get("batch_size"), 1)
    if batch_size > 1:
        risks.append("batch_size > 1 increases peak VRAM and is a common OOM trigger.")
    if n_batches * max(batch_size, 1) > 4:
        risks.append("n_batches * batch_size exceeds the default result count; expect longer runtime and more output files.")

    clip_models = cfg.get("clip_models") or []
    if len(clip_models) > len(DEFAULT_CLIP_MODELS):
        risks.append("more than the default number of CLIP models increases load time and VRAM.")
    heavy = [m for m in clip_models if any(marker in str(m) for marker in HEAVY_CLIP_MARKERS)]
    if heavy:
        risks.append("memory-heavy CLIP models selected: {}.".format(", ".join(map(str, heavy))))
    if cfg.get("clip_models_schedules"):
        scheduled = set((cfg.get("clip_models_schedules") or {}).keys())
        missing = sorted(scheduled.difference(set(clip_models)))
        if missing:
            risks.append("clip_models_schedules contains models not present in clip_models: {}.".format(", ".join(missing)))

    if cfg.get("diffusion_sampling_mode") not in ("ddim", "plms"):
        risks.append("diffusion_sampling_mode should normally be 'ddim' or 'plms'.")

    model_info = local_model_guess(cfg.get("diffusion_model"))
    if model_info.get("kind") == "local-file" and not model_info.get("exists"):
        risks.append("diffusion_model looks like a local file path but does not exist: {}.".format(model_info.get("path")))
    elif model_info.get("kind") == "catalog-or-prefix" and not model_info.get("known_prefix"):
        risks.append("diffusion_model is not one of the common known prefixes; verify the model catalog or DISCOART_MODELS_YAML.")

    if cfg.get("diffusion_model_config"):
        risks.append("custom diffusion_model_config is set; verify it matches the selected model architecture.")

    if cfg.get("use_secondary_model") is False:
        risks.append("use_secondary_model=False skips the secondary model but can increase VRAM and runtime.")

    if cfg.get("image_output") is False:
        risks.append("image_output=False means no PNG/GIF files; recover from da.protobuf.lz4 instead.")
    if as_int(cfg.get("save_rate"), 0) < 0:
        risks.append("save_rate < 0 disables intermediate image/protobuf saves before completion.")
    if as_int(cfg.get("gif_fps"), 0) <= 0:
        risks.append("gif_fps <= 0 disables progress GIF output.")

    if not os.environ.get("DISCOART_CACHE_DIR"):
        risks.append("DISCOART_CACHE_DIR is not set; model files will use DiscoArt's default user cache.")
    if not os.environ.get("DISCOART_OUTPUT_DIR"):
        risks.append("DISCOART_OUTPUT_DIR is not set; outputs will be relative to the process working directory.")
    if not os.environ.get("DISCOART_DISABLE_REMOTE_MODELS"):
        risks.append("DISCOART_DISABLE_REMOTE_MODELS is not set; DiscoArt may try remote model-list sync during runtime imports.")

    wandb_mode = os.environ.get("WANDB_MODE", "disabled")
    if wandb_mode == "online":
        risks.append("WANDB_MODE=online requires W&B credentials/network and may add runtime failure points.")

    if cuda.get("checked"):
        if not cuda.get("available"):
            risks.append("CUDA is not available to torch; DiscoArt create() will fall back to impractically slow CPU mode.")
    else:
        risks.append("CUDA was not checked; pass --check-cuda before running generation on a new machine.")

    return risks


def build_summary(cfg, args, cuda):
    output_dir = output_dir_for(cfg)
    model_info = local_model_guess(cfg.get("diffusion_model"))
    key_settings = {
        "text_prompts_type": type(cfg.get("text_prompts")).__name__,
        "width_height": cfg.get("width_height"),
        "steps": cfg.get("steps"),
        "skip_steps": cfg.get("skip_steps"),
        "n_batches": cfg.get("n_batches"),
        "batch_size": cfg.get("batch_size"),
        "seed": cfg.get("seed"),
        "diffusion_model": cfg.get("diffusion_model"),
        "diffusion_model_guess": model_info,
        "diffusion_sampling_mode": cfg.get("diffusion_sampling_mode"),
        "clip_models": cfg.get("clip_models"),
        "clip_models_schedules_keys": sorted((cfg.get("clip_models_schedules") or {}).keys()),
        "use_secondary_model": cfg.get("use_secondary_model"),
        "text_clip_on_cpu": cfg.get("text_clip_on_cpu"),
        "image_output": cfg.get("image_output"),
        "save_rate": cfg.get("save_rate"),
        "gif_fps": cfg.get("gif_fps"),
        "display_rate": cfg.get("display_rate"),
    }
    environment = {
        "DISCOART_OUTPUT_DIR": os.environ.get("DISCOART_OUTPUT_DIR"),
        "DISCOART_CACHE_DIR": os.environ.get("DISCOART_CACHE_DIR"),
        "DISCOART_DISABLE_REMOTE_MODELS": os.environ.get("DISCOART_DISABLE_REMOTE_MODELS"),
        "DISCOART_OPTOUT_CLOUD_BACKUP": os.environ.get("DISCOART_OPTOUT_CLOUD_BACKUP"),
        "WANDB_MODE": os.environ.get("WANDB_MODE", "disabled"),
    }
    artifacts = {
        "run_directory": output_dir,
        "protobuf": os.path.join(output_dir, "da.protobuf.lz4"),
        "final_png_pattern": os.path.join(output_dir, "<batch>-done-<minibatch>.png"),
        "step_png_pattern": os.path.join(output_dir, "<batch>-step-<step>-<minibatch>.png"),
        "progress_png_pattern": os.path.join(output_dir, "<batch>-progress-<minibatch>.png"),
        "progress_gif_pattern": os.path.join(output_dir, "<batch>-progress-<minibatch>.gif"),
    }
    risks = collect_risks(cfg, cuda)
    return {
        "ok": True,
        "generation_ran": False,
        "config_source": args.config or "<defaults>",
        "name_docarray": cfg.get("name_docarray"),
        "key_settings": key_settings,
        "environment": environment,
        "artifacts": artifacts,
        "cuda": cuda,
        "risky_settings": risks,
        "next_steps": [
            "Fix any config/schema issues before calling create().",
            "Set output/cache/W&B environment variables before importing discoart in the generation process.",
            "Run generation only in a CUDA-capable environment with model cache/download access.",
        ],
    }


def emit_text(summary):
    print("DiscoArt create() plan (no generation ran)")
    print("config source: {}".format(summary["config_source"]))
    print("name_docarray: {}".format(summary["name_docarray"]))
    print("run directory: {}".format(summary["artifacts"]["run_directory"]))
    print("protobuf: {}".format(summary["artifacts"]["protobuf"]))
    print("")
    print("Key settings:")
    for key in (
        "width_height",
        "steps",
        "skip_steps",
        "n_batches",
        "batch_size",
        "seed",
        "diffusion_model",
        "diffusion_sampling_mode",
        "clip_models",
        "use_secondary_model",
        "text_clip_on_cpu",
        "image_output",
        "save_rate",
        "gif_fps",
        "display_rate",
    ):
        print("  - {}: {}".format(key, summary["key_settings"].get(key)))

    cuda = summary["cuda"]
    print("")
    if cuda.get("checked"):
        line = "CUDA checked: available={}".format(cuda.get("available"))
        if cuda.get("torch_version"):
            line += ", torch={}".format(cuda.get("torch_version"))
        if cuda.get("device_0"):
            line += ", device_0={}".format(cuda.get("device_0"))
        if cuda.get("error"):
            line += ", error={}".format(cuda.get("error"))
        print(line)
    else:
        print("CUDA not checked; pass --check-cuda to inspect torch.cuda availability.")

    print("")
    risks = summary["risky_settings"]
    if risks:
        print("Risks / warnings:")
        for risk in risks:
            print("  - {}".format(risk))
    else:
        print("Risks / warnings: none detected by this planner.")

    print("")
    print("Expected artifact patterns:")
    for key, value in summary["artifacts"].items():
        if key != "run_directory":
            print("  - {}: {}".format(key, value))

    print("")
    print("Next steps:")
    for step in summary["next_steps"]:
        print("  - {}".format(step))


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        cfg = normalize_config(args.config)
    except Exception as exc:
        return fail(str(exc), use_json=args.json)

    cuda = cuda_probe(args.check_cuda)
    summary = build_summary(cfg, args, cuda)

    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        emit_text(summary)
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
