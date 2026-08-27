#!/usr/bin/env python3
"""Synthetic SLSTM and SConv2dLSTM state/shape smoke."""

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
    args = parser.parse_args()
    device = _device(args.device)
    torch.manual_seed(31)

    time_steps, batch_size, features = 4, 2, 3
    slstm = snn.SLSTM(features, features, threshold=0.2).to(device)
    syn, mem = slstm.reset_mem()
    slstm_spk = []
    x = torch.randn(time_steps, batch_size, features, device=device)
    for step in range(time_steps):
        spk, syn, mem = slstm(x[step], syn, mem)
        slstm_spk.append(spk)
    slstm_spk = torch.stack(slstm_spk)
    assert tuple(slstm_spk.shape) == (time_steps, batch_size, features)
    assert tuple(syn.shape) == (batch_size, features)
    assert tuple(mem.shape) == (batch_size, features)
    syn_reset, mem_reset = slstm.reset_mem()
    assert torch.count_nonzero(syn_reset).item() == 0
    assert torch.count_nonzero(mem_reset).item() == 0

    height = width = 6
    conv = snn.SConv2dLSTM(1, 2, kernel_size=3, max_pool=2, threshold=0.1).to(device)
    syn2, mem2 = conv.reset_mem()
    img = torch.randn(time_steps, batch_size, 1, height, width, device=device)
    conv_spk = []
    for step in range(time_steps):
        spk2, syn2, mem2 = conv(img[step], syn2, mem2)
        conv_spk.append(spk2)
    conv_spk = torch.stack(conv_spk)
    assert tuple(conv_spk.shape) == (time_steps, batch_size, 2, height // 2, width // 2)
    assert tuple(syn2.shape) == (batch_size, 2, height, width)
    assert tuple(mem2.shape) == (batch_size, 2, height, width)
    syn2_reset, mem2_reset = conv.reset_mem()
    assert torch.count_nonzero(syn2_reset).item() == 0
    assert torch.count_nonzero(mem2_reset).item() == 0

    summary = {
        "status": "ok",
        "device": str(device),
        "slstm_spike_shape": list(slstm_spk.shape),
        "slstm_state_shape": list(mem.shape),
        "sconv2dlstm_spike_shape": list(conv_spk.shape),
        "sconv2dlstm_state_shape": list(mem2.shape),
    }
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
