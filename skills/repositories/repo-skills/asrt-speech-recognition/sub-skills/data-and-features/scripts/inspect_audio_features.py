#!/usr/bin/env python3
"""Inspect WAV metadata and ASRT-style feature shapes without importing ASRT.

The implementations here are compact, self-contained adaptations of ASRT's
WAV decoding and feature-smoke behavior. They are intended for diagnostics, not
as a replacement training frontend.
"""

from __future__ import annotations

import argparse
import json
import math
import random
import sys
import wave
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Union

import numpy as np

try:
    from scipy.fftpack import dct, fft
except Exception as exc:  # noqa: BLE001
    dct = None
    fft = None
    SCIPY_IMPORT_ERROR = exc
else:
    SCIPY_IMPORT_ERROR = None


def read_wav_data(filename: Path) -> tuple[np.ndarray, int, int, int]:
    with wave.open(str(filename), "rb") as wav:
        num_frame = wav.getnframes()
        num_channel = wav.getnchannels()
        framerate = wav.getframerate()
        num_sample_width = wav.getsampwidth()
        raw_data = wav.readframes(num_frame)
    return decode_wav_bytes(raw_data, channels=num_channel, byte_width=num_sample_width), framerate, num_channel, num_sample_width


def decode_wav_bytes(samples_data: bytes, channels: int = 1, byte_width: int = 2) -> np.ndarray:
    if byte_width == 2:
        numpy_type = np.int16
    elif byte_width == 4:
        # ASRT source used deprecated np.int; int32 is the typical 4-byte PCM choice.
        numpy_type = np.int32
    elif byte_width == 1:
        numpy_type = np.int8
    else:
        raise ValueError(f"unsupported byte width {byte_width!r}; ASRT source supports 2 and deprecated 4-byte paths")
    wave_data = np.frombuffer(samples_data, dtype=numpy_type)
    if channels <= 0:
        raise ValueError("channels must be positive")
    if wave_data.size % channels != 0:
        raise ValueError(f"decoded sample count {wave_data.size} is not divisible by channels={channels}")
    wave_data = wave_data.reshape(-1, channels).T
    return wave_data


def synthesize_zero(seconds: float, sample_rate: int, channels: int) -> np.ndarray:
    if seconds <= 0:
        raise ValueError("--synthesize-zero must be positive")
    frames = int(round(seconds * sample_rate))
    return np.zeros((channels, frames), dtype=np.int16)


def asrt_spectrogram(wavsignal: np.ndarray, fs: int = 16000) -> np.ndarray:
    require_scipy()
    if fs != 16000:
        raise ValueError(
            f"[Error] ASRT currently only supports wav audio files with a sampling rate of 16000 Hz, but this audio is {fs} Hz."
        )
    time_window = 25
    window_length = int(fs / 1000 * time_window)
    x = np.linspace(0, 400 - 1, 400, dtype=np.int64)
    window = 0.54 - 0.46 * np.cos(2 * np.pi * x / (400 - 1))
    wav_arr = np.array(wavsignal)
    frame_count = int(len(wavsignal[0]) / fs * 1000 - time_window) // 10 + 1
    if frame_count <= 0:
        raise ValueError(f"audio is too short for ASRT 25 ms spectrogram window: computed frame_count={frame_count}")
    data_input = np.zeros((frame_count, window_length // 2), dtype=np.float64)
    for i in range(frame_count):
        start = i * 160
        end = start + 400
        data_line = wav_arr[0, start:end]
        if data_line.shape[0] != 400:
            raise ValueError(f"short frame at index {i}: expected 400 samples, got {data_line.shape[0]}")
        data_line = data_line * window
        data_line = np.abs(fft(data_line))
        data_input[i] = data_line[: window_length // 2]
    return np.log(data_input + 1)


def asrt_specaugment(wavsignal: np.ndarray, fs: int = 16000, seed: Optional[int] = None) -> np.ndarray:
    if seed is not None:
        random.seed(seed)
    data_input = asrt_spectrogram(wavsignal, fs)
    mode = random.randint(1, 100)
    h_start = random.randint(1, data_input.shape[0])
    h_width = random.randint(1, 100)
    v_start = random.randint(1, data_input.shape[1])
    v_width = random.randint(1, 100)
    if mode <= 60:
        pass
    elif 60 < mode <= 75:
        data_input[h_start : h_start + h_width, :] = 0
    elif 75 < mode <= 90:
        data_input[:, v_start : v_start + v_width] = 0
    else:
        data_input[h_start : h_start + h_width, :v_start:v_start + v_width] = 0
    return data_input


def framesig(signal: np.ndarray, frame_len: float, frame_step: float) -> np.ndarray:
    signal = np.asarray(signal)
    slen = len(signal)
    frame_len = int(round(frame_len))
    frame_step = int(round(frame_step))
    if slen <= frame_len:
        numframes = 1
    else:
        numframes = 1 + int(math.ceil((1.0 * slen - frame_len) / frame_step))
    padlen = int((numframes - 1) * frame_step + frame_len)
    zeros = np.zeros((padlen - slen,))
    padsignal = np.concatenate((signal, zeros))
    indices = (
        np.tile(np.arange(0, frame_len), (numframes, 1))
        + np.tile(np.arange(0, numframes * frame_step, frame_step), (frame_len, 1)).T
    )
    frames = padsignal[indices.astype(np.int32, copy=False)]
    return frames


def magspec(frames: np.ndarray, nfft: int) -> np.ndarray:
    require_scipy()
    complex_spec = np.fft.rfft(frames, nfft)
    return np.absolute(complex_spec)


def powspec(frames: np.ndarray, nfft: int) -> np.ndarray:
    return 1.0 / nfft * np.square(magspec(frames, nfft))


def preemphasis(signal: np.ndarray, coeff: float = 0.97) -> np.ndarray:
    return np.append(signal[0], signal[1:] - coeff * signal[:-1])


def calculate_nfft(samplerate: int, winlen: float) -> int:
    window_length_samples = winlen * samplerate
    nfft = 1
    while nfft < window_length_samples:
        nfft *= 2
    return nfft


def hz2mel(hz: Union[np.ndarray, float]) -> Union[np.ndarray, float]:
    return 2595 * np.log10(1 + np.asarray(hz) / 700.0)


def mel2hz(mel: Union[np.ndarray, float]) -> Union[np.ndarray, float]:
    return 700 * (10 ** (np.asarray(mel) / 2595.0) - 1)


def get_filterbanks(nfilt: int = 20, nfft: int = 512, samplerate: int = 16000, lowfreq: int = 0, highfreq: Optional[int] = None) -> np.ndarray:
    highfreq = highfreq or samplerate / 2
    if highfreq > samplerate / 2:
        raise ValueError("highfreq is greater than samplerate/2")
    lowmel = hz2mel(lowfreq)
    highmel = hz2mel(highfreq)
    melpoints = np.linspace(lowmel, highmel, nfilt + 2)
    bins = np.floor((nfft + 1) * mel2hz(melpoints) / samplerate)
    fbank = np.zeros([nfilt, nfft // 2 + 1])
    for j in range(nfilt):
        for i in range(int(bins[j]), int(bins[j + 1])):
            fbank[j, i] = (i - bins[j]) / (bins[j + 1] - bins[j])
        for i in range(int(bins[j + 1]), int(bins[j + 2])):
            fbank[j, i] = (bins[j + 2] - i) / (bins[j + 2] - bins[j + 1])
    return fbank


def fbank(signal: np.ndarray, samplerate: int = 16000, winlen: float = 0.025, winstep: float = 0.01, nfilt: int = 26, nfft: Optional[int] = None, preemph: float = 0.97) -> tuple[np.ndarray, np.ndarray]:
    nfft = nfft or calculate_nfft(samplerate, winlen)
    emphasized = preemphasis(signal, preemph)
    frames = framesig(emphasized, winlen * samplerate, winstep * samplerate)
    pspec = powspec(frames, nfft)
    energy = np.sum(pspec, 1)
    energy = np.where(energy == 0, np.finfo(float).eps, energy)
    fb = get_filterbanks(nfilt=nfilt, nfft=nfft, samplerate=samplerate)
    feat = np.dot(pspec, fb.T)
    feat = np.where(feat == 0, np.finfo(float).eps, feat)
    return feat, energy


def lifter(cepstra: np.ndarray, lift_value: int = 22) -> np.ndarray:
    if lift_value <= 0:
        return cepstra
    _, ncoeff = np.shape(cepstra)
    n = np.arange(ncoeff)
    lift = 1 + (lift_value / 2.0) * np.sin(np.pi * n / lift_value)
    return lift * cepstra


def delta(feat: np.ndarray, n: int) -> np.ndarray:
    if n < 1:
        raise ValueError("N must be an integer >= 1")
    numframes = len(feat)
    denominator = 2 * sum(i**2 for i in range(1, n + 1))
    delta_feat = np.empty_like(feat)
    padded = np.pad(feat, ((n, n), (0, 0)), mode="edge")
    for t in range(numframes):
        delta_feat[t] = np.dot(np.arange(-n, n + 1), padded[t : t + 2 * n + 1]) / denominator
    return delta_feat


def asrt_mfcc(wavsignal: np.ndarray, fs: int = 16000, numcep: int = 13, nfilt: int = 26) -> np.ndarray:
    require_scipy()
    signal = np.array(wavsignal, dtype=np.float64)[0]
    feat, energy = fbank(signal, samplerate=fs, nfilt=nfilt)
    feat = np.log(feat)
    feat = dct(feat, type=2, axis=1, norm="ortho")[:, :numcep]
    feat = lifter(feat, 22)
    feat[:, 0] = np.log(energy)
    feat_d = delta(feat, 2)
    feat_dd = delta(feat_d, 2)
    return np.column_stack((feat, feat_d, feat_dd))


def asrt_logfbank(wavsignal: np.ndarray, fs: int = 16000, nfilt: int = 26) -> np.ndarray:
    signal = np.array(wavsignal, dtype=np.float64)[0]
    feat, _ = fbank(signal, samplerate=fs, nfilt=nfilt)
    return np.log(feat)


def require_scipy() -> None:
    if SCIPY_IMPORT_ERROR is not None:
        raise RuntimeError(f"scipy is required for feature computation but could not be imported: {SCIPY_IMPORT_ERROR}")


def parse_features(text: str) -> List[str]:
    allowed = {"spectrogram", "mfcc", "logfbank", "specaugment"}
    features = [item.strip().lower() for item in text.split(",") if item.strip()]
    unknown = sorted(set(features) - allowed)
    if unknown:
        raise argparse.ArgumentTypeError(f"unknown feature(s): {', '.join(unknown)}")
    return features


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Inspect WAV metadata and ASRT-style feature shapes; useful for diagnosing 16 kHz and shape issues.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--wav", help="WAV file to inspect")
    source.add_argument("--synthesize-zero", type=float, metavar="SECONDS", help="Use in-memory zero waveform of this duration instead of a WAV file")
    parser.add_argument("--sample-rate", type=int, default=16000, help="Sample rate for synthesized audio")
    parser.add_argument("--channels", type=int, default=1, help="Channel count for synthesized audio")
    parser.add_argument("--features", type=parse_features, default=parse_features("spectrogram"), help="Comma-separated feature list: spectrogram,mfcc,logfbank,specaugment")
    parser.add_argument("--expect-sample-rate", type=int, default=None, help="Return failure if audio sample rate differs from this value")
    parser.add_argument("--seed", type=int, default=None, help="Random seed for SpecAugment-style masking")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    return parser


def feature_summary(name: str, wavsignal: np.ndarray, sample_rate: int, seed: Optional[int]) -> Dict[str, Any]:
    try:
        if name == "spectrogram":
            arr = asrt_spectrogram(wavsignal, sample_rate)
        elif name == "mfcc":
            arr = asrt_mfcc(wavsignal, sample_rate)
        elif name == "logfbank":
            arr = asrt_logfbank(wavsignal, sample_rate)
        elif name == "specaugment":
            arr = asrt_specaugment(wavsignal, sample_rate, seed=seed)
        else:  # pragma: no cover - parse_features prevents this
            raise ValueError(f"unknown feature {name}")
    except Exception as exc:  # noqa: BLE001 - diagnostics should continue for other features
        return {"name": name, "ok": False, "error": str(exc)}
    return {
        "name": name,
        "ok": True,
        "shape": list(arr.shape),
        "dtype": str(arr.dtype),
        "min": float(np.min(arr)) if arr.size else None,
        "max": float(np.max(arr)) if arr.size else None,
    }


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    issues: List[str] = []

    if args.wav:
        wav_path = Path(args.wav).expanduser().resolve()
        try:
            wavsignal, sample_rate, channels, byte_width = read_wav_data(wav_path)
        except Exception as exc:  # noqa: BLE001
            print(f"ERROR: could not read WAV {wav_path}: {exc}", file=sys.stderr)
            return 2
        source = str(wav_path)
    else:
        sample_rate = args.sample_rate
        channels = args.channels
        byte_width = 2
        wavsignal = synthesize_zero(args.synthesize_zero, sample_rate, channels)
        source = f"synthetic-zero:{args.synthesize_zero}s"

    if args.expect_sample_rate is not None and sample_rate != args.expect_sample_rate:
        issues.append(f"sample_rate {sample_rate} != expected {args.expect_sample_rate}")
    if byte_width != 2:
        issues.append(
            f"byte_width {byte_width} is not the usual ASRT 16-bit PCM path; stock read_wav_data decodes with int16 and "
            "decode_wav_bytes only explicitly handles 2-byte and deprecated 4-byte paths"
        )

    result: Dict[str, Any] = {
        "source": source,
        "sample_rate": sample_rate,
        "channels": channels,
        "byte_width": byte_width,
        "samples_per_channel": int(wavsignal.shape[1]),
        "duration_seconds": float(wavsignal.shape[1] / sample_rate) if sample_rate else None,
        "features": [feature_summary(name, wavsignal, sample_rate, args.seed) for name in args.features],
        "issues": issues,
    }
    has_feature_error = any(not item["ok"] for item in result["features"])
    failed = bool(issues) or has_feature_error

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"Source: {source}")
        print(
            f"Audio: rate={sample_rate}Hz channels={channels} byte_width={byte_width} "
            f"samples_per_channel={wavsignal.shape[1]} duration={result['duration_seconds']:.3f}s"
        )
        for item in result["features"]:
            if item["ok"]:
                print(f"Feature {item['name']}: shape={tuple(item['shape'])} dtype={item['dtype']} min={item['min']:.6g} max={item['max']:.6g}")
            else:
                print(f"Feature {item['name']}: ERROR {item['error']}")
        if issues:
            print("Issues:")
            for issue in issues:
                print(f"  - {issue}")
        print("Result:", "FAIL" if failed else "PASS")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
