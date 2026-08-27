#!/usr/bin/env python3
"""Tiny synthetic LeakyParallel optimization smoke.

This is a safe adaptation of the example LeakyParallel training pattern: it
uses random tensors and a generic PyTorch classification loss only to prove
that gradients and optimizer steps work. It is not a training recipe.
"""

from __future__ import annotations

import argparse
import json

import torch
import torch.nn as nn
import torch.nn.functional as F
import snntorch as snn


class TinyLeakyParallelNet(nn.Module):
    def __init__(self, input_size: int, hidden_size: int, num_classes: int):
        super().__init__()
        self.lif = snn.LeakyParallel(
            input_size=input_size,
            hidden_size=hidden_size,
            beta=0.85,
            threshold=0.25,
            learn_beta=True,
        )
        self.readout = nn.Linear(hidden_size, num_classes)

    def forward(self, x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        spk = self.lif(x)                 # (T, B, hidden_size)
        logits = self.readout(spk.mean(0)) # (B, num_classes)
        return spk, logits


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
    torch.manual_seed(11)

    time_steps, batch_size, input_size, hidden_size, num_classes = 7, 5, 4, 6, 3
    x = torch.rand(time_steps, batch_size, input_size, device=device)
    targets = (torch.arange(batch_size, device=device) % num_classes).long()

    net = TinyLeakyParallelNet(input_size, hidden_size, num_classes).to(device)
    opt = torch.optim.SGD(net.parameters(), lr=0.05)

    old_readout = net.readout.weight.detach().clone()
    old_recurrent = net.lif.rnn.weight_hh_l0.detach().clone()

    spk, logits = net(x)
    assert tuple(spk.shape) == (time_steps, batch_size, hidden_size)
    assert tuple(logits.shape) == (batch_size, num_classes)

    loss = F.cross_entropy(logits, targets)
    opt.zero_grad(set_to_none=True)
    loss.backward()

    assert net.readout.weight.grad is not None
    assert net.lif.rnn.weight_hh_l0.grad is not None
    opt.step()

    readout_delta = (net.readout.weight.detach() - old_readout).abs().max()
    recurrent_delta = (net.lif.rnn.weight_hh_l0.detach() - old_recurrent).abs().max()
    assert readout_delta.item() > 0, "Readout parameters did not update"
    assert recurrent_delta.item() > 0, "LeakyParallel recurrent weights did not update"

    with torch.no_grad():
        _, logits_after = net(x)
        loss_after = F.cross_entropy(logits_after, targets)

    summary = {
        "status": "ok",
        "device": str(device),
        "spike_shape": list(spk.shape),
        "logits_shape": list(logits.shape),
        "loss_before_step": float(loss.detach().cpu()),
        "loss_after_step": float(loss_after.detach().cpu()),
        "readout_delta_max": float(readout_delta.detach().cpu()),
        "recurrent_delta_max": float(recurrent_delta.detach().cpu()),
    }
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
