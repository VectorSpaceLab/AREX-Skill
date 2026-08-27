#!/usr/bin/env python3
"""Parameterized LatentSync evaluation runner.

This helper wraps the repo-maintained evaluation entry points while adding
explicit repo-root resolution, prerequisite checks, isolated temp directories,
and machine-readable JSON summaries.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from statistics import fmean
from typing import Any

ANSI_RED = "\033[91m"
ANSI_END = "\033[0m"


def add_repo_root(repo_root: str) -> Path:
    root = Path(repo_root).expanduser().resolve()
    if not root.exists():
        raise FileNotFoundError(f"Repo root does not exist: {root}")
    if not (root / "latentsync").is_dir() or not (root / "eval").is_dir():
        raise FileNotFoundError(f"Repo root does not look like a LatentSync checkout: {root}")
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    os.chdir(root)
    return root


def resolve_path(path: str | None, repo_root: Path) -> Path | None:
    if path in (None, ""):
        return None
    candidate = Path(path).expanduser()
    return candidate if candidate.is_absolute() else (repo_root / candidate)


def require_path(path: Path | None, label: str) -> Path:
    if path is None:
        raise ValueError(f"{label} path is required")
    if not path.exists():
        raise FileNotFoundError(f"{label} not found: {path}")
    return path


def require_executable(name: str) -> str:
    executable = shutil.which(name)
    if executable is None:
        raise FileNotFoundError(f"Required executable not found on PATH: {name}")
    return executable


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def clean_error(exc: BaseException) -> str:
    return str(exc).replace(ANSI_RED, "").replace(ANSI_END, "")


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("value must be a positive integer")
    return parsed


def nonnegative_int(value: str) -> int:
    parsed = int(value)
    if parsed < 0:
        raise argparse.ArgumentTypeError("value must be a non-negative integer")
    return parsed


def choose_device(torch_module: Any, requested: str, *, require_cuda: bool = False) -> str:
    if requested == "auto":
        device = "cuda" if torch_module.cuda.is_available() else "cpu"
    else:
        device = requested

    if device.startswith("cuda"):
        if not torch_module.cuda.is_available():
            raise RuntimeError("CUDA was requested but torch.cuda.is_available() is false")
        if ":" in device:
            try:
                index = int(device.split(":", 1)[1])
            except ValueError as exc:  # noqa: PERF203
                raise ValueError(f"Invalid CUDA device specifier: {device}") from exc
            if index >= torch_module.cuda.device_count():
                raise RuntimeError(f"CUDA device {device} is not available; device_count={torch_module.cuda.device_count()}")

    if require_cuda and not device.startswith("cuda"):
        raise RuntimeError(
            "SyncNet accuracy should be run on CUDA for this LatentSync skill. "
            "The source path validates float16 tensors and CPU-only accuracy is not a useful substitute."
        )
    return device


def video_paths_from_input(input_path: Path, *, label: str) -> list[Path]:
    if input_path.is_file():
        if input_path.suffix.lower() != ".mp4":
            raise ValueError(f"{label} must be an .mp4 file or a directory of .mp4 files: {input_path}")
        return [input_path]
    if not input_path.is_dir():
        raise FileNotFoundError(f"{label} is neither a file nor a directory: {input_path}")
    return [path for path in sorted(input_path.iterdir()) if path.suffix.lower() == ".mp4"]


def make_temp_paths(temp_base_dir: Path, stem: str) -> tuple[Path, Path, Path]:
    ensure_dir(temp_base_dir)
    temp_root = Path(tempfile.mkdtemp(prefix=f"{stem}_", dir=str(temp_base_dir)))
    return temp_root, temp_root / "temp", temp_root / "detect_results"


def torch_load(torch_module: Any, path: Path, *, map_location: Any) -> Any:
    try:
        return torch_module.load(path, map_location=map_location, weights_only=True)
    except TypeError:
        return torch_module.load(path, map_location=map_location)


def run_sync_conf(args: argparse.Namespace) -> dict[str, Any]:
    repo_root = add_repo_root(args.repo_root)
    require_executable("ffmpeg")

    import torch
    from eval.eval_sync_conf import syncnet_eval
    from eval.syncnet import SyncNetEval
    from eval.syncnet_detect import SyncNetDetector

    device = choose_device(torch, args.device)
    ckpt_path = require_path(
        resolve_path(args.initial_model or "checkpoints/auxiliary/syncnet_v2.model", repo_root),
        "SyncNet confidence checkpoint",
    )
    # S3FD uses this fixed path internally, so validate it before constructing the detector.
    require_path(resolve_path("checkpoints/auxiliary/sfd_face.pth", repo_root), "S3FD face detector checkpoint")

    video_path = resolve_path(args.video_path, repo_root)
    videos_dir = resolve_path(args.videos_dir, repo_root)
    if video_path is not None and videos_dir is not None:
        raise ValueError("Pass either --video-path or --videos-dir, not both")
    if video_path is None and videos_dir is None:
        raise ValueError("One of --video-path or --videos-dir is required")

    input_path = require_path(video_path or videos_dir, "SyncNet confidence input")
    video_paths = video_paths_from_input(input_path, label="SyncNet confidence input")
    if args.max_videos is not None:
        video_paths = video_paths[: args.max_videos]
    if not video_paths:
        raise ValueError("No .mp4 videos found for SyncNet confidence evaluation")

    temp_base_dir = resolve_path(args.temp_base_dir or "temp/evaluation", repo_root)
    assert temp_base_dir is not None

    syncnet = SyncNetEval(device=device)
    syncnet.loadParameters(str(ckpt_path))
    syncnet_detector = SyncNetDetector(device=device, detect_results_dir=str(temp_base_dir / "detect_results_placeholder"))

    scores: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []

    for path in video_paths:
        temp_root, temp_dir, detect_results_dir = make_temp_paths(temp_base_dir, "sync_conf")
        syncnet_detector.detect_results_dir = str(detect_results_dir)
        try:
            av_offset, confidence = syncnet_eval(
                syncnet,
                syncnet_detector,
                str(path),
                str(temp_dir),
                detect_results_dir=str(detect_results_dir),
            )
            scores.append({"video": str(path), "av_offset": int(av_offset), "confidence": float(confidence)})
        except Exception as exc:  # noqa: BLE001 - report per-video metric failures.
            message = clean_error(exc)
            errors.append({"video": str(path), "error": message})
            print(f"{path}: {message}")
        finally:
            if not args.keep_temp:
                shutil.rmtree(temp_root, ignore_errors=True)

    if not scores:
        first_error = f" First failure: {errors[0]['video']}: {errors[0]['error']}" if errors else ""
        raise RuntimeError(f"No SyncNet confidence scores were produced.{first_error}")

    summary: dict[str, Any] = {
        "mode": "sync-conf",
        "device": device,
        "checkpoint": str(ckpt_path),
        "num_videos": len(video_paths),
        "scored": len(scores),
        "failed": len(errors),
        "average_confidence": float(fmean(item["confidence"] for item in scores)),
        "average_av_offset": float(fmean(item["av_offset"] for item in scores)),
        "results": scores,
    }
    if errors:
        summary["errors"] = errors
    return summary


def apply_syncnet_acc_overrides(config: Any, args: argparse.Namespace, repo_root: Path) -> None:
    if args.val_data_dir is not None:
        config.data.val_data_dir = str(resolve_path(args.val_data_dir, repo_root))
    if args.val_fileslist is not None:
        config.data.val_fileslist = str(resolve_path(args.val_fileslist, repo_root))
    if args.audio_mel_cache_dir is not None:
        config.data.audio_mel_cache_dir = str(resolve_path(args.audio_mel_cache_dir, repo_root))
    if args.batch_size is not None:
        config.data.batch_size = args.batch_size
    if args.num_workers is not None:
        config.data.num_workers = args.num_workers
    if args.num_val_samples is not None:
        config.data.num_val_samples = args.num_val_samples


def run_syncnet_acc(args: argparse.Namespace) -> dict[str, Any]:
    repo_root = add_repo_root(args.repo_root)

    import torch
    import torch.nn.functional as F
    from accelerate.utils import set_seed
    from diffusers import AutoencoderKL
    from einops import rearrange
    from omegaconf import OmegaConf
    from latentsync.data.syncnet_dataset import SyncNetDataset
    from latentsync.models.stable_syncnet import StableSyncNet

    device = choose_device(torch, args.device, require_cuda=True)
    config_path = require_path(resolve_path(args.config_path, repo_root), "SyncNet config")
    config = OmegaConf.load(config_path)
    apply_syncnet_acc_overrides(config, args, repo_root)
    set_seed(config.run.seed)

    ckpt_path = resolve_path(args.inference_ckpt_path or config.ckpt.inference_ckpt_path, repo_root)
    if ckpt_path is None:
        raise ValueError("SyncNet accuracy needs config.ckpt.inference_ckpt_path or --inference-ckpt-path")
    ckpt_path = require_path(ckpt_path, "SyncNet inference checkpoint")

    val_fileslist = str(config.data.val_fileslist or "")
    val_data_dir = str(config.data.val_data_dir or "")
    if val_fileslist:
        require_path(Path(val_fileslist).expanduser(), "SyncNet validation fileslist")
    elif val_data_dir:
        require_path(Path(val_data_dir).expanduser(), "SyncNet validation data directory")
    else:
        raise ValueError("SyncNet accuracy needs either data.val_fileslist or data.val_data_dir")

    audio_mel_cache_dir = Path(str(config.data.audio_mel_cache_dir)).expanduser()
    audio_mel_cache_dir.mkdir(parents=True, exist_ok=True)

    vae = None
    if bool(config.data.latent_space):
        try:
            vae = AutoencoderKL.from_pretrained(
                "runwayml/stable-diffusion-inpainting",
                subfolder="vae",
                revision="fp16",
                torch_dtype=torch.float16,
            )
            vae.requires_grad_(False)
            vae.to(device)
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(
                "Latent-space SyncNet accuracy needs the Stable Diffusion inpainting VAE cache or approved network access. "
                "Use a pixel-space config for a simpler smoke check."
            ) from exc

    dataset = SyncNetDataset(str(config.data.val_data_dir), str(config.data.val_fileslist), config)
    if len(dataset) == 0:
        raise ValueError("SyncNet validation dataset is empty; check val_data_dir or val_fileslist")
    if int(config.data.num_workers) == 0:
        dataset.worker_id = 0

    dataloader = torch.utils.data.DataLoader(
        dataset,
        batch_size=int(config.data.batch_size),
        shuffle=False,
        num_workers=int(config.data.num_workers),
        drop_last=False,
        worker_init_fn=dataset.worker_init_fn,
    )

    syncnet = StableSyncNet(OmegaConf.to_container(config.model)).to(device)
    checkpoint = torch_load(torch, ckpt_path, map_location=device)
    state_dict = checkpoint["state_dict"] if isinstance(checkpoint, dict) and "state_dict" in checkpoint else checkpoint
    syncnet.load_state_dict(state_dict)
    syncnet.to(dtype=torch.float16)
    syncnet.requires_grad_(False)
    syncnet.eval()

    default_batches = max(1, int(config.data.num_val_samples) // int(config.data.batch_size))
    target_batches = args.max_batches or default_batches
    num_correct = 0
    num_total = 0
    processed_batches = 0
    batch_iter = iter(dataloader)

    while processed_batches < target_batches:
        try:
            batch = next(batch_iter)
        except StopIteration:
            batch_iter = iter(dataloader)
            continue

        frames = batch["frames"].to(device, dtype=torch.float16)
        audio_samples = batch["audio_samples"].to(device, dtype=torch.float16)
        y = batch["y"].to(device, dtype=torch.float16).squeeze(1)

        if bool(config.data.latent_space):
            frames = rearrange(frames, "b f c h w -> (b f) c h w")
            with torch.no_grad():
                frames = vae.encode(frames).latent_dist.sample() * 0.18215
            frames = rearrange(frames, "(b f) c h w -> b (f c) h w", f=int(config.data.num_frames))
        else:
            frames = rearrange(frames, "b f c h w -> b (f c) h w")

        if bool(config.data.lower_half):
            height = frames.shape[2]
            frames = frames[:, :, height // 2 :, :]

        with torch.no_grad():
            vision_embeds, audio_embeds = syncnet(frames, audio_samples)

        sims = F.cosine_similarity(vision_embeds, audio_embeds)
        preds = (sims > 0.5).to(dtype=torch.float16)
        num_correct += (preds == y).sum().item()
        num_total += len(sims)
        processed_batches += 1
        print(f"Testing accuracy batch {processed_batches}/{target_batches}")

    accuracy_pct = num_correct / num_total * 100.0
    print(f"SyncNet Accuracy: {accuracy_pct:.2f}%")
    return {
        "mode": "syncnet-acc",
        "device": device,
        "config": str(config_path),
        "checkpoint": str(ckpt_path),
        "target_batches": target_batches,
        "num_correct": int(num_correct),
        "num_total": int(num_total),
        "accuracy_pct": float(accuracy_pct),
    }


def load_fvd_video(fvd: Any, video_path: Path) -> Any:
    import cv2
    import numpy as np
    import torch
    from decord import VideoReader

    vr = VideoReader(str(video_path))
    video_frames = vr[20:36].asnumpy()
    vr.seek(0)
    if len(video_frames) < 16:
        raise RuntimeError(f"insufficient frames for FVD: need frames 20:36, got {len(video_frames)}")

    faces = []
    for frame_index, frame in enumerate(video_frames, start=20):
        face = fvd.detect_face(frame)
        if getattr(face, "size", 0) == 0:
            raise RuntimeError(f"empty face crop at frame {frame_index}")
        face = cv2.resize(face, (fvd.resolution[1], fvd.resolution[0]), interpolation=cv2.INTER_AREA)
        faces.append(face)

    if len(faces) != 16:
        raise RuntimeError(f"insufficient consecutive face crops for FVD: need 16, got {len(faces)}")
    return torch.from_numpy(np.stack(faces, axis=0))


def compute_fvd_from_tensors(fake_tensor: Any, real_tensor: Any, i3d_path: Path) -> float:
    import torch
    from eval.fvd import compute_fvd

    i3d_kwargs = dict(rescale=False, resize=False, return_features=True)
    with torch.no_grad():
        with open(i3d_path, "rb") as file_obj:
            i3d_model = torch.jit.load(file_obj).eval().to("cpu")
        videos_fake = fake_tensor.permute(0, 4, 1, 2, 3).to("cpu")
        videos_real = real_tensor.permute(0, 4, 1, 2, 3).to("cpu")
        feats_fake = i3d_model(videos_fake, **i3d_kwargs).cpu().numpy()
        feats_real = i3d_model(videos_real, **i3d_kwargs).cpu().numpy()
    return float(compute_fvd(feats_fake, feats_real))


def run_fvd(args: argparse.Namespace) -> dict[str, Any]:
    repo_root = add_repo_root(args.repo_root)

    import torch
    from eval.eval_fvd import FVD

    i3d_path = require_path(
        resolve_path(args.i3d_path or "checkpoints/auxiliary/i3d_torchscript.pt", repo_root),
        "FVD I3D checkpoint",
    )
    real_path = require_path(resolve_path(args.real_dir, repo_root), "Real video input")
    fake_path = require_path(resolve_path(args.fake_dir, repo_root), "Fake video input")

    real_videos = video_paths_from_input(real_path, label="Real video input")
    fake_videos = video_paths_from_input(fake_path, label="Fake video input")
    if args.max_videos is not None:
        real_videos = real_videos[: args.max_videos]
        fake_videos = fake_videos[: args.max_videos]
    if not real_videos or not fake_videos:
        raise ValueError("FVD needs at least one .mp4 in both the real and fake inputs")
    if (len(real_videos) < 2 or len(fake_videos) < 2) and not args.allow_singleton_fvd:
        raise ValueError(
            "FVD covariance is unstable with fewer than two videos per side. "
            "Add more videos or pass --allow-singleton-fvd for smoke-only backend checks."
        )

    fvd = FVD()
    real_faces = []
    fake_faces = []
    for path in real_videos:
        try:
            real_faces.append(load_fvd_video(fvd, path))
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(f"Real video failed FVD face extraction: {path}: {clean_error(exc)}") from exc
    for path in fake_videos:
        try:
            fake_faces.append(load_fvd_video(fvd, path))
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(f"Fake video failed FVD face extraction: {path}: {clean_error(exc)}") from exc

    real_tensor = torch.stack(real_faces) / 255.0
    fake_tensor = torch.stack(fake_faces) / 255.0
    value = compute_fvd_from_tensors(fake_tensor, real_tensor, i3d_path)
    print(f"FVD: {value:.3f}" if math.isfinite(value) else f"FVD: {value}")

    summary: dict[str, Any] = {
        "mode": "fvd",
        "device": "cpu",
        "checkpoint": str(i3d_path),
        "real_count": len(real_videos),
        "fake_count": len(fake_videos),
        "fvd": value,
    }
    if len(real_videos) < 2 or len(fake_videos) < 2:
        summary["warning"] = "singleton/small-set FVD is a smoke check only and may be unstable or NaN"
    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="LatentSync evaluation runner")
    parser.add_argument("--repo-root", default=".", help="LatentSync checkout used to resolve imports and relative paths")
    subparsers = parser.add_subparsers(dest="command", required=True)

    sync_conf = subparsers.add_parser("sync-conf", help="Score one video or a directory with SyncNet confidence")
    sync_conf.add_argument("--video-path", default=None, help="Single .mp4 to score")
    sync_conf.add_argument("--videos-dir", default=None, help="Directory of .mp4 files to score")
    sync_conf.add_argument("--initial-model", default=None, help="Override SyncNet confidence checkpoint path")
    sync_conf.add_argument("--device", default="auto", help="Device for SyncNet confidence: auto, cpu, cuda, cuda:0, ...")
    sync_conf.add_argument("--temp-base-dir", default=None, help="Base directory for isolated temp roots")
    sync_conf.add_argument("--max-videos", type=positive_int, default=None, help="Limit .mp4 files scored in batch mode")
    sync_conf.add_argument("--keep-temp", action="store_true", help="Keep per-run temp directories for detector debugging")

    sync_acc = subparsers.add_parser("syncnet-acc", help="Run SyncNet checkpoint accuracy evaluation")
    sync_acc.add_argument("--config-path", default="configs/syncnet/syncnet_16_pixel_attn.yaml", help="SyncNet config path")
    sync_acc.add_argument("--inference-ckpt-path", default=None, help="Override config.ckpt.inference_ckpt_path")
    sync_acc.add_argument("--val-data-dir", default=None, help="Override config.data.val_data_dir")
    sync_acc.add_argument("--val-fileslist", default=None, help="Override config.data.val_fileslist")
    sync_acc.add_argument("--audio-mel-cache-dir", default=None, help="Override config.data.audio_mel_cache_dir")
    sync_acc.add_argument("--batch-size", type=positive_int, default=None, help="Override config.data.batch_size")
    sync_acc.add_argument("--num-workers", type=nonnegative_int, default=None, help="Override config.data.num_workers")
    sync_acc.add_argument("--num-val-samples", type=positive_int, default=None, help="Override config.data.num_val_samples")
    sync_acc.add_argument("--max-batches", type=positive_int, default=None, help="Limit validation batches for smoke checks")
    sync_acc.add_argument("--device", default="auto", help="CUDA device for SyncNet accuracy: auto, cuda, cuda:0, ...")

    fvd = subparsers.add_parser("fvd", help="Run CPU-backed FVD on real and fake video sets")
    fvd.add_argument("--real-dir", required=True, help="Real .mp4 directory or file")
    fvd.add_argument("--fake-dir", required=True, help="Fake/generated .mp4 directory or file")
    fvd.add_argument("--i3d-path", default=None, help="Override FVD I3D checkpoint path")
    fvd.add_argument("--max-videos", type=positive_int, default=None, help="Limit .mp4 files scored in each set")
    fvd.add_argument("--allow-singleton-fvd", action="store_true", help="Allow one-video-per-side smoke checks despite unstable covariance")

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "sync-conf":
        summary = run_sync_conf(args)
    elif args.command == "syncnet-acc":
        summary = run_syncnet_acc(args)
    elif args.command == "fvd":
        summary = run_fvd(args)
    else:  # pragma: no cover - argparse enforces choices.
        raise ValueError(f"Unknown command: {args.command}")

    print(json.dumps(summary, indent=2, sort_keys=True, allow_nan=True))


if __name__ == "__main__":
    main()
