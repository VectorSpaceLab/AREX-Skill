#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from types import SimpleNamespace

import torch

ALL_MODELS = ["Linear", "DLinear", "NLinear", "Informer", "Transformer", "Autoformer"]
FREQ_TO_MARK_DIM = {"h": 4, "t": 5, "s": 6, "m": 1, "a": 1, "w": 2, "d": 3, "b": 3}


def find_repo_root(anchor: Path) -> Path:
    for candidate in [anchor, *anchor.parents]:
        if (candidate / "run_longExp.py").is_file() and (candidate / "models").is_dir():
            return candidate
    raise FileNotFoundError(
        "Could not locate the repository root that contains run_longExp.py and models/."
    )


def import_models():
    from models.Linear import Model as LinearModel
    from models.DLinear import Model as DLinearModel
    from models.NLinear import Model as NLinearModel
    from models.Informer import Model as InformerModel
    from models.Transformer import Model as TransformerModel
    from models.Autoformer import Model as AutoformerModel

    return {
        "Linear": LinearModel,
        "DLinear": DLinearModel,
        "NLinear": NLinearModel,
        "Informer": InformerModel,
        "Transformer": TransformerModel,
        "Autoformer": AutoformerModel,
    }


def build_config(seq_len: int, label_len: int, pred_len: int, channels: int, freq: str):
    return SimpleNamespace(
        seq_len=seq_len,
        label_len=label_len,
        pred_len=pred_len,
        enc_in=channels,
        dec_in=channels,
        c_out=channels,
        individual=False,
        output_attention=False,
        embed_type=0,
        d_model=8,
        n_heads=2,
        e_layers=1,
        d_layers=1,
        d_ff=16,
        moving_avg=3,
        factor=1,
        distil=True,
        dropout=0.0,
        embed="timeF",
        activation="gelu",
        freq=freq,
        data_path="",
    )


def make_batch(device: torch.device, seq_len: int, label_len: int, pred_len: int, channels: int, freq: str):
    batch = 2
    x = torch.linspace(-1.0, 1.0, steps=batch * seq_len * channels, device=device).reshape(batch, seq_len, channels)
    y = torch.linspace(0.5, 1.5, steps=batch * (label_len + pred_len) * channels, device=device).reshape(
        batch, label_len + pred_len, channels
    )
    mark_dim = FREQ_TO_MARK_DIM[freq]
    x_mark = torch.zeros(batch, seq_len, mark_dim, device=device)
    y_mark = torch.zeros(batch, label_len + pred_len, mark_dim, device=device)
    dec_inp = torch.cat([y[:, :label_len, :], torch.zeros(batch, pred_len, channels, device=device)], dim=1)
    return x, y, x_mark, y_mark, dec_inp


def run_model(name: str, model_cls, cfg, device, x, y, x_mark, y_mark, dec_inp, pred_len, channels):
    model = model_cls(cfg).to(device)
    model.train()
    with torch.no_grad():
        if name in {"Linear", "DLinear", "NLinear"}:
            out = model(x)
        else:
            out = model(x, x_mark, dec_inp, y_mark)
            if isinstance(out, tuple):
                out = out[0]
    expected_shape = (x.shape[0], pred_len, channels)
    if tuple(out.shape) != expected_shape:
        raise AssertionError(f"{name} produced shape {tuple(out.shape)}, expected {expected_shape}")
    if not torch.isfinite(out).all():
        raise AssertionError(f"{name} produced non-finite values")
    print(f"{name}: ok {tuple(out.shape)} on {device.type}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a tiny deterministic forward smoke for the core forecasting models.")
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--models", default=",".join(ALL_MODELS), help="Comma-separated model list.")
    parser.add_argument("--seq-len", type=int, default=16)
    parser.add_argument("--label-len", type=int, default=8)
    parser.add_argument("--pred-len", type=int, default=4)
    parser.add_argument("--channels", type=int, default=3)
    parser.add_argument("--freq", default="h")
    args = parser.parse_args()

    if args.freq not in FREQ_TO_MARK_DIM:
        raise SystemExit(f"Unsupported freq {args.freq!r}. Known values: {sorted(FREQ_TO_MARK_DIM)}")

    if args.device == "cuda":
        if not torch.cuda.is_available():
            raise SystemExit("CUDA was requested but torch.cuda.is_available() is false.")
        device = torch.device("cuda")
    elif args.device == "cpu":
        device = torch.device("cpu")
    else:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    if device.type == "cuda":
        torch.cuda.manual_seed_all(0)
    torch.manual_seed(0)

    repo_root = find_repo_root(Path(__file__).resolve())
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    models = import_models()
    requested = [name.strip() for name in args.models.split(",") if name.strip()]
    unknown = [name for name in requested if name not in models]
    if unknown:
        raise SystemExit(f"Unknown model names: {unknown}. Expected a subset of {ALL_MODELS}.")

    cfg = build_config(args.seq_len, args.label_len, args.pred_len, args.channels, args.freq)
    x, y, x_mark, y_mark, dec_inp = make_batch(
        device, args.seq_len, args.label_len, args.pred_len, args.channels, args.freq
    )

    print(f"Running smoke on {device.type}")
    for name in requested:
        run_model(name, models[name], cfg, device, x, y, x_mark, y_mark, dec_inp, args.pred_len, args.channels)

    print("Smoke check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
