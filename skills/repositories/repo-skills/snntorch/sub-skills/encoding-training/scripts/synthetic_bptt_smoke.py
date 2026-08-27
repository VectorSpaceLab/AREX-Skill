#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
import warnings

warnings.filterwarnings('ignore', category=DeprecationWarning)

import torch
from torch import nn
from torch.utils.data import DataLoader, TensorDataset

import snntorch as snn
import snntorch.functional as SF
from snntorch import backprop, surrogate, utils
from snntorch.functional import probe


def build_net() -> nn.Sequential:
    spike_grad = surrogate.fast_sigmoid(slope=25)
    net = nn.Sequential(
        nn.Linear(4, 2, bias=False),
        snn.Leaky(beta=0.5, spike_grad=spike_grad, init_hidden=True, output=True),
    )
    with torch.no_grad():
        net[0].weight.zero_()
    return net


def main() -> int:
    parser = argparse.ArgumentParser(
        description='Smoke-test one-step BPTT with fast_sigmoid and mse_count_loss.'
    )
    parser.add_argument('--seed', type=int, default=0)
    parser.add_argument('--device', default='cpu')
    args = parser.parse_args()

    torch.manual_seed(args.seed)
    device = torch.device(args.device)

    net = build_net().to(device)
    optimizer = torch.optim.SGD(net.parameters(), lr=0.2)
    loss_fn = SF.mse_count_loss(correct_rate=1.0, incorrect_rate=0.0)

    inputs = torch.tensor(
        [[1.0, 0.0, 0.5, 0.2], [0.0, 1.0, 0.2, 0.8]],
        dtype=torch.float32,
    )
    targets = torch.tensor([0, 1], dtype=torch.long)
    loader = DataLoader(TensorDataset(inputs, targets), batch_size=2, shuffle=False)

    out_mon = probe.OutputMonitor(net, instance=snn.Leaky)
    grad_mon = probe.GradOutputMonitor(net, instance=snn.Leaky)

    before = net[0].weight.detach().clone()
    utils.reset(net)
    loss = backprop.BPTT(
        net,
        loader,
        optimizer=optimizer,
        criterion=loss_fn,
        num_steps=1,
        time_var=False,
        device=device,
    )
    after = net[0].weight.detach().clone()

    weight_delta = after - before
    assert torch.isfinite(loss)
    assert not torch.allclose(before, after)
    assert len(out_mon.records) > 0
    assert len(grad_mon.records) > 0

    summary = {
        'loss': float(loss.item()),
        'weight_delta_max': float(weight_delta.abs().max().item()),
        'weight_delta': [[float(v) for v in row] for row in weight_delta.tolist()],
        'output_records': len(out_mon.records),
        'grad_output_records': len(grad_mon.records),
        'monitored_layers': out_mon.monitored_layers,
    }
    print(json.dumps(summary, indent=2, sort_keys=True))

    out_mon.remove_hooks()
    grad_mon.remove_hooks()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
