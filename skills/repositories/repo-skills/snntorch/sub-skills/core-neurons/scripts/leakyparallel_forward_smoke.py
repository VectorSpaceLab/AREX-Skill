#!/usr/bin/env python3
"""Synthetic LeakyParallel forward/gradient smoke.

The script uses only generated tensors. It constructs the module on CPU and
then moves it to the requested device to avoid constructor-time device-mask
edge cases in this snnTorch release.
"""

from __future__ import annotations

import argparse
import json

import torch
import snntorch as snn


def _device(name: str) -> torch.device:
    dev = torch.device(name)
    if dev.type == "cuda" and not torch.cuda.is_available():
        raise SystemExit("CUDA was requested but torch.cuda.is_available() is False")
    return dev


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--device", default="cpu", help="Torch device, e.g. cpu or cuda:0")
    parser.add_argument("--time-steps", type=int, default=6)
    parser.add_argument("--batch-size", type=int, default=3)
    args = parser.parse_args()

    device = _device(args.device)
    torch.manual_seed(7)

    input_size = 4
    hidden_size = 5
    x = torch.linspace(0.0, 1.0, args.time_steps * args.batch_size * input_size)
    x = x.reshape(args.time_steps, args.batch_size, input_size).to(device)

    lif = snn.LeakyParallel(
        input_size=input_size,
        hidden_size=hidden_size,
        beta=0.8,
        threshold=0.2,
        learn_beta=True,
        learn_threshold=True,
    ).to(device)

    spk = lif(x)
    expected_shape = (args.time_steps, args.batch_size, hidden_size)
    assert tuple(spk.shape) == expected_shape, (tuple(spk.shape), expected_shape)
    assert torch.isfinite(spk).all().item()

    loss = spk.sum()
    loss.backward()

    recurrent_grad = lif.rnn.weight_hh_l0.grad
    assert recurrent_grad is not None, "Expected gradient on rnn.weight_hh_l0"
    off_diagonal = recurrent_grad - torch.diag(torch.diagonal(recurrent_grad))
    assert torch.allclose(off_diagonal, torch.zeros_like(off_diagonal), atol=1e-6)
    assert lif.threshold.requires_grad and lif.threshold.grad is not None

    summary = {
        "status": "ok",
        "device": str(device),
        "spike_shape": list(spk.shape),
        "spike_sum": float(spk.detach().sum().cpu()),
        "recurrent_grad_offdiag_max": float(off_diagonal.detach().abs().max().cpu()),
        "threshold_grad": float(lif.threshold.grad.detach().cpu()),
    }
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
