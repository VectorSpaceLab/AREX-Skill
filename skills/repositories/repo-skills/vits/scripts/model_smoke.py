#!/usr/bin/env python3
"""Run a tiny VITS model smoke check on synthetic inputs.

Prereqs:
- `build_monotonic_align.py` should already have placed the compiled extension
  where `models` can import it.
- GPU mode requires CUDA. CPU mode is useful only for shape/import checks.

Example:
  python scripts/model_smoke.py --repo-root /path/to/vits --config configs/ljs_nosdp.json --mode infer
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a synthetic VITS smoke check.")
    parser.add_argument("--repo-root", required=True, help="Path to the VITS checkout.")
    parser.add_argument("--config", required=True, help="Config JSON relative to the repo root or an absolute path.")
    parser.add_argument("--mode", choices=("forward", "infer", "voice-conversion"), default="forward")
    parser.add_argument("--device", choices=("cuda", "cpu"), default="cuda")
    parser.add_argument("--seed", type=int, default=1234)
    parser.add_argument("--max-len", type=int, default=128, help="Max decoder length for inference mode.")
    parser.add_argument("--speaker-id", type=int, default=1, help="Speaker id for multi-speaker inference.")
    parser.add_argument("--source-speaker-id", type=int, default=1)
    parser.add_argument("--target-speaker-id", type=int, default=2)
    return parser.parse_args()


def load_config(repo_root: Path, config_arg: str):
    config_path = Path(config_arg)
    if not config_path.is_absolute():
        config_path = repo_root / config_path
    with config_path.open("r", encoding="utf-8") as handle:
        return json.load(handle), config_path


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).expanduser().resolve()
    sys.path.insert(0, str(repo_root))

    import torch
    import utils
    from models import SynthesizerTrn
    from text.symbols import symbols

    config, config_path = load_config(repo_root, args.config)
    hps = utils.HParams(**config)
    device = torch.device(args.device)
    if device.type == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA device requested but not available")

    torch.manual_seed(args.seed)
    if device.type == "cuda":
        torch.cuda.manual_seed_all(args.seed)

    spec_channels = hps.data.filter_length // 2 + 1
    segment_frames = hps.train.segment_size // hps.data.hop_length
    model_kwargs = dict(hps.model.items())
    if getattr(hps.data, "n_speakers", 0) > 0:
        model_kwargs["n_speakers"] = hps.data.n_speakers
    model = SynthesizerTrn(
        len(symbols),
        spec_channels,
        segment_frames,
        **model_kwargs,
    ).to(device)
    model.eval()

    text_len = 10
    x = torch.randint(0, len(symbols), (1, text_len), device=device, dtype=torch.long)
    x_lengths = torch.tensor([text_len], device=device, dtype=torch.long)
    spec = torch.randn(1, spec_channels, segment_frames, device=device)
    spec_lengths = torch.tensor([segment_frames], device=device, dtype=torch.long)

    sid = None
    if getattr(hps.data, "n_speakers", 0) > 0:
        sid = torch.tensor([args.speaker_id], device=device, dtype=torch.long)

    with torch.no_grad():
        if args.mode == "forward":
            outputs = model(x, x_lengths, spec, spec_lengths, sid=sid)
            print(f"config={config_path}")
            print(f"mode=forward device={device}")
            print(f"audio_shape={tuple(outputs[0].shape)}")
            print(f"length_loss_shape={tuple(outputs[1].shape)}")
            print(f"attn_shape={tuple(outputs[2].shape)}")
            print(f"slice_ids_shape={tuple(outputs[3].shape)}")
        elif args.mode == "infer":
            outputs = model.infer(x, x_lengths, sid=sid, max_len=args.max_len)
            print(f"config={config_path}")
            print(f"mode=infer device={device}")
            print(f"audio_shape={tuple(outputs[0].shape)}")
            print(f"attn_shape={tuple(outputs[1].shape)}")
            print(f"mask_shape={tuple(outputs[2].shape)}")
        else:
            if getattr(hps.data, "n_speakers", 0) <= 0:
                raise RuntimeError("voice-conversion mode requires a multi-speaker config")
            sid_src = torch.tensor([args.source_speaker_id], device=device, dtype=torch.long)
            sid_tgt = torch.tensor([args.target_speaker_id], device=device, dtype=torch.long)
            outputs = model.voice_conversion(spec, spec_lengths, sid_src=sid_src, sid_tgt=sid_tgt)
            print(f"config={config_path}")
            print(f"mode=voice-conversion device={device}")
            print(f"audio_shape={tuple(outputs[0].shape)}")
            print(f"mask_shape={tuple(outputs[1].shape)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
