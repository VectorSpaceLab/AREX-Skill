#!/usr/bin/env python3
"""Bundled HunyuanVideo sampling runner.

This is a small self-contained replacement for the repository's sampling script.
It can import HunyuanVideo from an installed/importable `hyvideo` package, or
from an explicit --repo-root when the user is intentionally running against a
local source tree. It then uses public hyvideo APIs to load a sampler, run
prediction, and save MP4 outputs. It is a real GPU/model job when executed; use
the build helper for safe command construction first.
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from datetime import datetime
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run HunyuanVideo text-to-video sampling through bundled runner.")
    parser.add_argument("--repo-root", default=None, help="Optional HunyuanVideo source root containing hyvideo/. Omit when hyvideo is already importable.")
    parser.add_argument("--model-base", default="ckpts")
    parser.add_argument("--dit-weight", default="ckpts/hunyuan-video-t2v-720p/transformers/mp_rank_00_model_states.pt")
    parser.add_argument("--model", default="HYVideo-T/2-cfgdistill", choices=["HYVideo-T/2", "HYVideo-T/2-cfgdistill"])
    parser.add_argument("--vae", default="884-16c-hy")
    parser.add_argument("--latent-channels", type=int, default=16)
    parser.add_argument("--precision", default="bf16", choices=["fp32", "fp16", "bf16"])
    parser.add_argument("--vae-precision", default="fp16", choices=["fp32", "fp16", "bf16"])
    parser.add_argument("--video-size", type=int, nargs=2, metavar=("HEIGHT", "WIDTH"), default=[544, 960])
    parser.add_argument("--video-length", type=int, default=129)
    parser.add_argument("--infer-steps", type=int, default=50)
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--neg-prompt", default=None)
    parser.add_argument("--cfg-scale", type=float, default=1.0)
    parser.add_argument("--embedded-cfg-scale", type=float, default=6.0)
    parser.add_argument("--flow-shift", type=float, default=7.0)
    parser.add_argument("--flow-reverse", action="store_true")
    parser.add_argument("--flow-solver", default="euler")
    parser.add_argument("--use-cpu-offload", action="store_true")
    parser.add_argument("--use-fp8", action="store_true")
    parser.add_argument("--save-path", default="./results")
    parser.add_argument("--num-videos", type=int, default=1)
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--ulysses-degree", type=int, default=1)
    parser.add_argument("--ring-degree", type=int, default=1)
    parser.add_argument("--model-resolution", default="540p", choices=["540p", "720p"])
    parser.add_argument("--load-key", default="module")
    # Text encoder defaults needed by HYVideoDiffusionTransformer/TextEncoder.
    parser.add_argument("--text-encoder", default="llm")
    parser.add_argument("--text-encoder-precision", default="fp16")
    parser.add_argument("--text-states-dim", type=int, default=4096)
    parser.add_argument("--text-len", type=int, default=256)
    parser.add_argument("--tokenizer", default="llm")
    parser.add_argument("--prompt-template", default="dit-llm-encode")
    parser.add_argument("--prompt-template-video", default="dit-llm-encode-video")
    parser.add_argument("--hidden-state-skip-layer", type=int, default=2)
    parser.add_argument("--apply-final-norm", action="store_true")
    parser.add_argument("--text-encoder-2", default="clipL")
    parser.add_argument("--text-encoder-precision-2", default="fp16")
    parser.add_argument("--text-states-dim-2", type=int, default=768)
    parser.add_argument("--tokenizer-2", default="clipL")
    parser.add_argument("--text-len-2", type=int, default=77)
    parser.add_argument("--denoise-type", default="flow")
    parser.add_argument("--rope-theta", type=int, default=256)
    parser.add_argument("--vae-tiling", action="store_true", default=True)
    parser.add_argument("--disable-autocast", action="store_true")
    parser.add_argument("--reproduce", action="store_true")
    parser.add_argument("--save-path-suffix", default="")
    parser.add_argument("--name-suffix", default="")
    parser.add_argument("--seed-type", default="auto")
    parser.add_argument("--use-linear-quadratic-schedule", action="store_true")
    parser.add_argument("--linear-schedule-end", type=int, default=25)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if args.repo_root:
        repo_root = Path(args.repo_root).expanduser().resolve()
        if not (repo_root / "hyvideo").exists():
            raise SystemExit(f"--repo-root does not contain a hyvideo package: {repo_root}")
        sys.path.insert(0, str(repo_root))

    try:
        from loguru import logger
        from hyvideo.inference import HunyuanVideoSampler
        from hyvideo.utils.file_utils import save_videos_grid
    except ImportError as exc:
        raise SystemExit("Could not import HunyuanVideo. Install the package/source in the active environment or pass --repo-root to a source tree containing hyvideo/.") from exc

    model_root = Path(args.model_base)
    if not model_root.exists():
        raise SystemExit(f"`models_root` not exists: {model_root}")
    if args.video_length != 1 and (args.video_length - 1) % 4 != 0:
        raise SystemExit("default 884 VAE requires video_length == 1 or (video_length - 1) % 4 == 0")
    if args.ulysses_degree > 1 or args.ring_degree > 1:
        if args.use_cpu_offload:
            raise SystemExit("--use-cpu-offload is incompatible with distributed xDiT mode")
        expected = args.ulysses_degree * args.ring_degree
        world_size = int(os.environ.get("WORLD_SIZE", expected))
        if world_size != expected:
            raise SystemExit(f"WORLD_SIZE ({world_size}) must equal ulysses_degree * ring_degree ({expected})")

    save_path = args.save_path if args.save_path_suffix == "" else f"{args.save_path}_{args.save_path_suffix}"
    Path(save_path).mkdir(parents=True, exist_ok=True)

    sampler = HunyuanVideoSampler.from_pretrained(model_root, args=args)
    args = sampler.args
    outputs = sampler.predict(
        prompt=args.prompt,
        height=args.video_size[0],
        width=args.video_size[1],
        video_length=args.video_length,
        seed=args.seed,
        negative_prompt=args.neg_prompt,
        infer_steps=args.infer_steps,
        guidance_scale=args.cfg_scale,
        num_videos_per_prompt=args.num_videos,
        flow_shift=args.flow_shift,
        batch_size=args.batch_size,
        embedded_guidance_scale=args.embedded_cfg_scale,
    )

    if "LOCAL_RANK" not in os.environ or int(os.environ["LOCAL_RANK"]) == 0:
        for i, sample in enumerate(outputs["samples"]):
            sample = outputs["samples"][i].unsqueeze(0)
            stamp = datetime.fromtimestamp(time.time()).strftime("%Y-%m-%d-%H:%M:%S")
            prompt_part = outputs["prompts"][i][:100].replace("/", "") if i < len(outputs["prompts"]) else "prompt"
            out_path = f"{save_path}/{stamp}_seed{outputs['seeds'][i]}_{prompt_part}.mp4"
            save_videos_grid(sample, out_path, fps=24)
            logger.info(f"Sample save to: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
