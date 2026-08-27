#!/usr/bin/env python
from __future__ import annotations

import argparse
import json

import torch
from torch import nn

import snntorch as snn
from snntorch.functional.stdp_learner import STDPLearner


class SpikeOnly(nn.Module):
    def __init__(self, neuron: nn.Module):
        super().__init__()
        self.neuron = neuron

    def forward(self, x):
        spk, _ = self.neuron(x)
        return spk


def main() -> int:
    parser = argparse.ArgumentParser(
        description='Smoke-test STDPLearner on a synthetic two-step spike sequence.'
    )
    parser.add_argument('--seed', type=int, default=3)
    args = parser.parse_args()

    torch.manual_seed(args.seed)

    syn = nn.Linear(2, 2, bias=False)
    with torch.no_grad():
        syn.weight.copy_(torch.tensor([[0.6, 0.0], [0.0, 0.6]]))

    spike_only = SpikeOnly(snn.Leaky(beta=0.9))
    learner = STDPLearner(syn, spike_only, tau_pre=2.0, tau_post=3.0)
    optimizer = torch.optim.SGD(syn.parameters(), lr=0.1)

    inputs = [
        torch.tensor([[1.0, 0.0]]),
        torch.tensor([[1.0, 0.0]]),
    ]
    spike_history = []
    for x in inputs:
        spike_history.append(spike_only(syn(x)).detach().cpu())

    before = syn.weight.detach().clone()
    learner.step(on_grad=True)
    grad = syn.weight.grad.detach().clone()
    optimizer.step()
    after = syn.weight.detach().clone()

    assert grad.abs().sum() > 0
    assert not torch.allclose(before, after)

    summary = {
        'spikes': [[float(v) for v in row] for row in spike_history[0].tolist()] + [[float(v) for v in row] for row in spike_history[1].tolist()],
        'grad': [[float(v) for v in row] for row in grad.tolist()],
        'weight_before': [[float(v) for v in row] for row in before.tolist()],
        'weight_after': [[float(v) for v in row] for row in after.tolist()],
        'weight_delta_max': float((after - before).abs().max().item()),
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
