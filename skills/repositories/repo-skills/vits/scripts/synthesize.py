#!/usr/bin/env python3
"""Synthesize speech or run voice conversion from a VITS checkpoint.

Prereqs:
- CUDA is required for the default device.
- The monotonic-alignment extension must already be built.
- Supply a checkpoint that matches the chosen config family.

Examples:
  python scripts/synthesize.py --repo-root /path/to/vits --config configs/ljs_base.json --checkpoint /path/to/checkpoint.pth --text "VITS is awesome" --output-wav out.wav
  python scripts/synthesize.py --repo-root /path/to/vits --config configs/vctk_base.json --checkpoint /path/to/checkpoint.pth --mode voice-conversion --source-audio source.wav --source-speaker-id 1 --target-speaker-id 2 --output-wav vc.wav
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from scipy.io.wavfile import write as write_wav


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Synthesize audio from a VITS checkpoint.")
    parser.add_argument("--repo-root", required=True, help="Path to the VITS checkout.")
    parser.add_argument("--config", required=True, help="Config JSON relative to the repo root or an absolute path.")
    parser.add_argument("--checkpoint", required=True, help="Checkpoint path to load.")
    parser.add_argument("--mode", choices=("tts", "voice-conversion"), default="tts")
    parser.add_argument("--text", help="Text to synthesize for TTS mode.")
    parser.add_argument("--speaker-id", type=int, default=1, help="Speaker id for multi-speaker TTS.")
    parser.add_argument("--source-audio", help="Source WAV file for voice-conversion mode.")
    parser.add_argument("--source-speaker-id", type=int, default=1)
    parser.add_argument("--target-speaker-id", type=int, default=2)
    parser.add_argument("--output-wav", required=True, help="Path to the output WAV file.")
    parser.add_argument("--device", choices=("cuda", "cpu"), default="cuda")
    parser.add_argument("--noise-scale", type=float, default=0.667)
    parser.add_argument("--noise-scale-w", type=float, default=0.8)
    parser.add_argument("--length-scale", type=float, default=1.0)
    parser.add_argument("--max-len", type=int, default=1000)
    return parser.parse_args()


def resolve_path(repo_root: Path, value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return repo_root / path


def load_config(repo_root: Path, config_arg: str):
    config_path = resolve_path(repo_root, config_arg)
    with config_path.open("r", encoding="utf-8") as handle:
        return json.load(handle), config_path


def build_model(repo_root: Path, config: dict, checkpoint: Path, device):
    import utils
    from models import SynthesizerTrn
    from text.symbols import symbols

    hps = utils.HParams(**config)
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
    utils.load_checkpoint(str(checkpoint), model, None)
    model.eval()
    return hps, model


def write_audio(path: Path, sample_rate: int, audio: np.ndarray) -> None:
    audio = np.asarray(audio, dtype=np.float32)
    write_wav(str(path), sample_rate, audio)


def spectrogram_torch_compat(y, n_fft, sampling_rate, hop_size, win_size, center=False):
    """Compute the repo's linear spectrogram across old and new PyTorch APIs.

    The original `mel_processing.spectrogram_torch` calls `torch.stft` without
    `return_complex`, which fails on modern PyTorch for real inputs. This helper
    keeps the same padding/window/magnitude contract while selecting the API that
    the active PyTorch accepts. `sampling_rate` is kept for call-shape parity.
    """
    import torch

    _ = sampling_rate
    if torch.min(y) < -1.0:
        print("min value is", torch.min(y))
    if torch.max(y) > 1.0:
        print("max value is", torch.max(y))

    window = torch.hann_window(win_size).to(dtype=y.dtype, device=y.device)
    pad = int((n_fft - hop_size) / 2)
    y = torch.nn.functional.pad(y.unsqueeze(1), (pad, pad), mode="reflect").squeeze(1)
    stft_kwargs = dict(
        n_fft=n_fft,
        hop_length=hop_size,
        win_length=win_size,
        window=window,
        center=center,
        pad_mode="reflect",
        normalized=False,
        onesided=True,
    )
    try:
        spec = torch.stft(y, return_complex=True, **stft_kwargs)
        return torch.sqrt(spec.real.pow(2) + spec.imag.pow(2) + 1e-6)
    except TypeError:
        spec = torch.stft(y, **stft_kwargs)
        return torch.sqrt(spec.pow(2).sum(-1) + 1e-6)


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).expanduser().resolve()
    sys.path.insert(0, str(repo_root))

    import torch
    import commons
    import utils
    from text import text_to_sequence

    if args.device == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA device requested but not available")

    config, config_path = load_config(repo_root, args.config)
    checkpoint = resolve_path(repo_root, args.checkpoint)
    if not checkpoint.exists():
        raise FileNotFoundError(f"checkpoint not found: {checkpoint}")

    device = torch.device(args.device)
    torch.manual_seed(1234)
    if device.type == "cuda":
        torch.cuda.manual_seed_all(1234)

    hps, model = build_model(repo_root, config, checkpoint, device)
    output_wav = resolve_path(repo_root, args.output_wav)
    output_wav.parent.mkdir(parents=True, exist_ok=True)

    if args.mode == "tts":
        if not args.text:
            raise ValueError("tts mode requires --text")
        text_norm = text_to_sequence(args.text, hps.data.text_cleaners)
        if hps.data.add_blank:
            text_norm = commons.intersperse(text_norm, 0)
        x = torch.LongTensor(text_norm).unsqueeze(0).to(device)
        x_lengths = torch.LongTensor([len(text_norm)]).to(device)
        sid = None
        if getattr(hps.data, "n_speakers", 0) > 0:
            sid = torch.LongTensor([args.speaker_id]).to(device)
        with torch.no_grad():
            audio = model.infer(
                x,
                x_lengths,
                sid=sid,
                noise_scale=args.noise_scale,
                length_scale=args.length_scale,
                noise_scale_w=args.noise_scale_w,
                max_len=args.max_len,
            )[0][0, 0].detach().cpu().numpy()
        write_audio(output_wav, hps.data.sampling_rate, audio)
        print(f"config={config_path}")
        print(f"mode=tts output={output_wav}")
        print(f"audio_shape={audio.shape}")
        return 0

    if getattr(hps.data, "n_speakers", 0) <= 0:
        raise RuntimeError("voice-conversion mode requires a multi-speaker config")
    if not args.source_audio:
        raise ValueError("voice-conversion mode requires --source-audio")

    source_wav = resolve_path(repo_root, args.source_audio)
    if not source_wav.exists():
        raise FileNotFoundError(f"source audio not found: {source_wav}")

    source_audio, sampling_rate = utils.load_wav_to_torch(str(source_wav))
    if sampling_rate != hps.data.sampling_rate:
        raise ValueError(
            f"sampling_rate mismatch: source={sampling_rate} config={hps.data.sampling_rate}"
        )
    source_audio = source_audio / hps.data.max_wav_value
    source_audio = source_audio.unsqueeze(0).to(device)
    spec = spectrogram_torch_compat(
        source_audio,
        hps.data.filter_length,
        hps.data.sampling_rate,
        hps.data.hop_length,
        hps.data.win_length,
        center=False,
    )
    spec_lengths = torch.LongTensor([spec.size(2)]).to(device)
    sid_src = torch.LongTensor([args.source_speaker_id]).to(device)
    sid_tgt = torch.LongTensor([args.target_speaker_id]).to(device)
    with torch.no_grad():
        audio = model.voice_conversion(spec, spec_lengths, sid_src=sid_src, sid_tgt=sid_tgt)[0][0, 0].detach().cpu().numpy()
    write_audio(output_wav, hps.data.sampling_rate, audio)
    print(f"config={config_path}")
    print(f"mode=voice-conversion output={output_wav}")
    print(f"audio_shape={audio.shape}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
