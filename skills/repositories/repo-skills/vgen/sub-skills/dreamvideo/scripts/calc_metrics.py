#!/usr/bin/env python3
"""Calculate DreamVideo metrics with explicit checkpoint arguments.

This is a runtime-friendly wrapper around the repository's DreamVideo metric
formula. It keeps the original CLIP-T / CLIP-I / DINO-I / Temporal Consistency
logic, but replaces the hard-coded DINO placeholder with an explicit checkpoint
argument and adds clearer dependency failures for CLIP and DINO setup.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import cv2
import imageio.v2 as imageio
import numpy as np
import torch
import torch.nn.functional as F
import torchvision.transforms as T
from PIL import Image

SUPPORTED_VIDEO_EXTENSIONS = {".mp4", ".gif"}
SUPPORTED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


REPO_ROOT = Path('.')


@dataclass(frozen=True)
class MetricEntry:
    video_name: str
    reference_dir: Path
    prompt: str


def resolve_repo_relative(raw: str) -> Path:
    path = Path(raw).expanduser()
    if path.is_absolute():
        return path
    return (REPO_ROOT / path).resolve()


def split_into_chunks(items: Sequence, chunk_size: int) -> Iterable[Sequence]:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be a positive integer")
    for start in range(0, len(items), chunk_size):
        yield items[start : start + chunk_size]


def parse_prompts(prompts_path: Path) -> Dict[str, MetricEntry]:
    entries: Dict[str, MetricEntry] = {}
    for line_number, raw_line in enumerate(prompts_path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        parts = [part.strip() for part in line.split("|||")]
        if len(parts) != 3:
            raise ValueError(
                f"Invalid prompts line {line_number} in {prompts_path}: expected 'video|||reference_dir|||prompt'."
            )
        video_name = Path(parts[0]).name
        if video_name in entries:
            raise ValueError(f"Duplicate video entry {video_name!r} in {prompts_path}")
        reference_dir = resolve_repo_relative(parts[1])
        entries[video_name] = MetricEntry(video_name=video_name, reference_dir=reference_dir, prompt=parts[2])
    return entries


def discover_video_files(videos_dir_path: Path) -> List[Path]:
    if not videos_dir_path.is_dir():
        raise FileNotFoundError(f"Videos directory not found: {videos_dir_path}")
    video_files = [path for path in sorted(videos_dir_path.iterdir()) if path.is_file() and path.suffix.lower() in SUPPORTED_VIDEO_EXTENSIONS]
    if not video_files:
        raise FileNotFoundError(
            f"No .mp4 or .gif videos were found in {videos_dir_path}"
        )
    return video_files


def discover_reference_images(reference_dir: Path) -> List[Path]:
    if not reference_dir.is_dir():
        raise FileNotFoundError(f"Reference image directory not found: {reference_dir}")
    return [
        path
        for path in sorted(reference_dir.iterdir())
        if path.is_file() and path.suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS
    ]


def decode_video_frames(video_path: Path) -> List[Image.Image]:
    frames: List[Image.Image] = []
    capture = cv2.VideoCapture(str(video_path))
    try:
        while True:
            ok, frame = capture.read()
            if not ok or frame is None:
                break
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frames.append(Image.fromarray(frame))
    finally:
        capture.release()

    if frames:
        return frames

    if video_path.suffix.lower() == ".gif":
        try:
            for frame in imageio.mimread(str(video_path)):
                array = np.asarray(frame)
                if array.ndim == 2:
                    array = np.stack([array, array, array], axis=-1)
                if array.shape[-1] > 3:
                    array = array[..., :3]
                frames.append(Image.fromarray(array.astype(np.uint8), mode="RGB"))
        except Exception as exc:  # pragma: no cover - fallback path
            raise RuntimeError(f"Unable to decode GIF {video_path}: {exc}") from exc

    if not frames:
        raise RuntimeError(f"No frames could be decoded from {video_path}")
    return frames


def load_clip_backend(device: torch.device, clip_source: str):
    try:
        import clip as openai_clip
    except ImportError as exc:  # pragma: no cover - dependency gate
        raise RuntimeError(
            "OpenAI CLIP is required. Install it with `pip install git+https://github.com/openai/CLIP.git`."
        ) from exc

    if clip_source.startswith("/") or Path(clip_source).expanduser().is_file():
        clip_input = str(Path(clip_source).expanduser())
    else:
        clip_input = clip_source

    try:
        clip_model, clip_preprocess = openai_clip.load(clip_input, device=device, jit=False)
    except Exception as exc:  # pragma: no cover - dependency gate
        raise RuntimeError(
            f"Failed to load CLIP source {clip_source!r}. If you want an offline run, pass `--clip-checkpoint-path` to a local checkpoint; otherwise verify that the requested CLIP model is available in the OpenAI CLIP package cache."
        ) from exc

    clip_model.eval()
    return openai_clip, clip_model, clip_preprocess


def load_dino_backend(device: torch.device, checkpoint_path: Path):
    try:
        from dino.vision_transformer import vit_small
    except ImportError as exc:  # pragma: no cover - dependency gate
        raise RuntimeError(
            "The bundled DINO backbone is not importable. Make sure the VGen checkout is on PYTHONPATH so `metric/dino` can be imported."
        ) from exc

    if not checkpoint_path.is_file():
        raise FileNotFoundError(
            f"DINO checkpoint not found: {checkpoint_path}. Pass `--dino-checkpoint-path` to a real ViT-S/16 backbone checkpoint."
        )

    dino_model = vit_small()
    raw_state = torch.load(str(checkpoint_path), map_location="cpu")
    state_dict = extract_state_dict(raw_state)
    state_dict = strip_common_prefixes(state_dict)
    load_result = dino_model.load_state_dict(state_dict, strict=False)
    if load_result.missing_keys or load_result.unexpected_keys:
        raise RuntimeError(
            "The DINO checkpoint did not match the vit_small backbone. "
            f"Missing keys: {load_result.missing_keys[:10]} ; unexpected keys: {load_result.unexpected_keys[:10]}"
        )

    dino_model = dino_model.to(device)
    dino_model.eval()
    return dino_model


def extract_state_dict(raw_state) -> Dict:
    if isinstance(raw_state, dict):
        for candidate_key in ("state_dict", "model", "student", "teacher", "backbone"):
            candidate = raw_state.get(candidate_key)
            if isinstance(candidate, dict):
                return candidate
    if not isinstance(raw_state, dict):
        raise TypeError(f"Unsupported DINO checkpoint type: {type(raw_state).__name__}")
    return raw_state


def strip_common_prefixes(state_dict: Dict) -> Dict:
    prefixes = ("module.", "backbone.", "student.", "teacher.", "dino.")
    cleaned: Dict = {}
    for key, value in state_dict.items():
        new_key = key
        changed = True
        while changed:
            changed = False
            for prefix in prefixes:
                if new_key.startswith(prefix):
                    new_key = new_key[len(prefix) :]
                    changed = True
        cleaned[new_key] = value
    return cleaned


def encode_items(items: Sequence[Image.Image], preprocess, encode_fn, device: torch.device, chunk_size: int) -> torch.Tensor:
    if not items:
        raise ValueError("encode_items received an empty item sequence")

    features: List[torch.Tensor] = []
    with torch.inference_mode():
        for chunk in split_into_chunks(items, chunk_size):
            batch = torch.stack([preprocess(item) for item in chunk]).to(device)
            feature = encode_fn(batch)
            feature = F.normalize(feature, p=2, dim=1)
            features.append(feature)
    return torch.cat(features, dim=0)


def score_entry(
    entry: MetricEntry,
    videos_dir: Path,
    clip_module,
    clip_model,
    clip_preprocess,
    dino_model,
    dino_preprocess,
    device: torch.device,
    chunk_size: int,
) -> Dict[str, float]:
    video_path = videos_dir / entry.video_name
    if not video_path.is_file():
        raise FileNotFoundError(f"Video file not found: {video_path}")

    frames = decode_video_frames(video_path)
    clip_frame_features = encode_items(frames, clip_preprocess, clip_model.encode_image, device, chunk_size)
    dino_frame_features = encode_items(frames, dino_preprocess, dino_model, device, chunk_size)

    text_tokens = clip_module.tokenize([entry.prompt]).to(device)
    text_features = F.normalize(clip_model.encode_text(text_tokens), p=2, dim=1)

    gen_clip_mean = clip_frame_features.mean(dim=0, keepdim=True)
    gen_dino_mean = dino_frame_features.mean(dim=0, keepdim=True)

    clip_t = torch.sum(text_features * gen_clip_mean, dim=1).item()
    if clip_frame_features.shape[0] > 1:
        temporal = torch.sum(clip_frame_features[:-1] * clip_frame_features[1:], dim=1).mean().item()
    else:
        temporal = 0.0

    reference_images = discover_reference_images(entry.reference_dir)
    if reference_images:
        ref_clip_features = encode_items(reference_images, clip_preprocess, clip_model.encode_image, device, chunk_size)
        ref_dino_features = encode_items(reference_images, dino_preprocess, dino_model, device, chunk_size)
        clip_i = torch.sum(ref_clip_features * gen_clip_mean, dim=1).mean().item()
        dino_i = torch.sum(ref_dino_features * gen_dino_mean, dim=1).mean().item()
    else:
        clip_i = 0.0
        dino_i = 0.0

    return {
        "video": entry.video_name,
        "clip_t": clip_t,
        "clip_i": clip_i,
        "dino_i": dino_i,
        "temporal_consistency": temporal,
    }


def resolve_device(value: str) -> torch.device:
    value = value.lower()
    if value == "auto":
        value = "cuda" if torch.cuda.is_available() else "cpu"
    if value.startswith("cuda") and not torch.cuda.is_available():
        raise RuntimeError("CUDA was requested but torch.cuda.is_available() is false in this environment.")
    return torch.device(value)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Calculate DreamVideo CLIP-T, CLIP-I, DINO-I, and temporal consistency metrics.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--repo-root", default=".", help="VGen checkout root that contains configs/ and metric/.")
    parser.add_argument("--videos-dir-path", required=True, help="Directory containing generated .mp4 or .gif videos.")
    parser.add_argument("--prompts-path", required=True, help="Prompt file with 'video|||reference_dir|||prompt' lines.")
    parser.add_argument(
        "--dino-checkpoint-path",
        required=True,
        help="Path to a DINO ViT-S/16 backbone checkpoint.",
    )
    parser.add_argument(
        "--clip-model",
        default="ViT-B/32",
        help="OpenAI CLIP model name to load when no local checkpoint is provided.",
    )
    parser.add_argument(
        "--clip-checkpoint-path",
        default=None,
        help="Optional local CLIP checkpoint or JIT archive path.",
    )
    parser.add_argument(
        "--device",
        default="auto",
        help="Execution device for CLIP and DINO.",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=1,
        help="Number of frames or reference images to encode per batch.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    global REPO_ROOT
    REPO_ROOT = Path(args.repo_root).resolve()
    sys.path.insert(0, str(REPO_ROOT))
    sys.path.insert(0, str(REPO_ROOT / "metric"))
    videos_dir_path = resolve_repo_relative(args.videos_dir_path)
    prompts_path = resolve_repo_relative(args.prompts_path)
    dino_checkpoint_path = resolve_repo_relative(args.dino_checkpoint_path)
    device = resolve_device(args.device)

    if not prompts_path.is_file():
        raise SystemExit(f"error: prompts file not found: {prompts_path}")

    video_files = discover_video_files(videos_dir_path)
    prompt_map = parse_prompts(prompts_path)

    video_names = {path.name for path in video_files}
    prompt_names = set(prompt_map.keys())
    if video_names != prompt_names:
        missing_prompts = sorted(video_names - prompt_names)
        missing_videos = sorted(prompt_names - video_names)
        raise SystemExit(
            "error: videos and prompts do not match by basename. "
            f"Missing prompt entries for: {missing_prompts}; missing video files for: {missing_videos}"
        )

    clip_source = args.clip_checkpoint_path or args.clip_model
    if args.clip_checkpoint_path is not None:
        clip_source_path = resolve_repo_relative(args.clip_checkpoint_path)
        if not clip_source_path.is_file():
            raise SystemExit(f"error: CLIP checkpoint not found: {clip_source_path}")
        clip_source = str(clip_source_path)

    try:
        clip_module, clip_model, clip_preprocess = load_clip_backend(device, clip_source)
        dino_model = load_dino_backend(device, dino_checkpoint_path)
    except Exception as exc:
        raise SystemExit(f"error: {exc}") from exc

    dino_preprocess = T.Compose(
        [
            T.Resize(256, interpolation=T.InterpolationMode.BICUBIC),
            T.CenterCrop(224),
            T.ToTensor(),
            T.Normalize((0.485, 0.456, 0.406), (0.229, 0.224, 0.225)),
        ]
    )

    print(f"Loaded CLIP source: {clip_source}")
    print(f"Loaded DINO checkpoint: {dino_checkpoint_path}")
    print(f"Evaluating {len(video_files)} videos from {videos_dir_path}")

    clip_t_scores: List[float] = []
    clip_i_scores: List[float] = []
    dino_i_scores: List[float] = []
    temporal_scores: List[float] = []

    for index, video_path in enumerate(video_files, start=1):
        entry = prompt_map[video_path.name]
        print(f"[{index}/{len(video_files)}] {video_path.name} -> {entry.reference_dir}")
        result = score_entry(
            entry=entry,
            videos_dir=videos_dir_path,
            clip_module=clip_module,
            clip_model=clip_model,
            clip_preprocess=clip_preprocess,
            dino_model=dino_model,
            dino_preprocess=dino_preprocess,
            device=device,
            chunk_size=args.chunk_size,
        )
        clip_t_scores.append(result["clip_t"])
        clip_i_scores.append(result["clip_i"])
        dino_i_scores.append(result["dino_i"])
        temporal_scores.append(result["temporal_consistency"])
        print(
            f"  CLIP-T={result['clip_t']:.4f} CLIP-I={result['clip_i']:.4f} "
            f"DINO-I={result['dino_i']:.4f} TemporalConsistency={result['temporal_consistency']:.4f}"
        )

    def mean(values: Sequence[float]) -> float:
        return float(sum(values) / len(values)) if values else 0.0

    clip_t_mean = mean(clip_t_scores)
    clip_i_mean = mean(clip_i_scores)
    dino_i_mean = mean(dino_i_scores)
    temporal_mean = mean(temporal_scores)

    print(
        "Final CLIP-T: {:.4f}, CLIP-I: {:.4f}, DINO-I: {:.4f}, TemporalConsistency: {:.4f}".format(
            clip_t_mean, clip_i_mean, dino_i_mean, temporal_mean
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
