#!/usr/bin/env python
from __future__ import annotations

import argparse
import json

import torch
from snntorch import spikegen


def main() -> int:
    parser = argparse.ArgumentParser(
        description='Smoke-test snnTorch spike encoders on synthetic tensors.'
    )
    parser.add_argument('--num-steps', type=int, default=6)
    parser.add_argument('--seed', type=int, default=7)
    args = parser.parse_args()

    torch.manual_seed(args.seed)

    x = torch.tensor(
        [[0.0, 0.25, 0.5, 1.0], [1.0, 0.0, 0.75, 0.125]],
        dtype=torch.float32,
    )
    rate = spikegen.rate(x, num_steps=args.num_steps, gain=0.5)
    latency = spikegen.latency(x, num_steps=args.num_steps, normalize=True, linear=True)
    tv = torch.stack([x, x * 0.5], dim=0)
    rate_tv = spikegen.rate(tv, time_var_input=True)
    delta = spikegen.delta(
        torch.tensor([1.0, 2.0, 0.0, 2.0, 2.9]),
        threshold=1.0,
        padding=True,
        off_spike=True,
    )
    labels = torch.tensor([0, 2], dtype=torch.long)
    target_rate = spikegen.targets_convert(labels, num_classes=4, code='rate')
    target_latency = spikegen.targets_convert(
        labels,
        num_classes=4,
        code='latency',
        num_steps=5,
        normalize=True,
        linear=True,
        bypass=True,
    )

    expected_delta = torch.tensor([0.0, 1.0, -1.0, 1.0, 0.0])
    assert rate.shape == (args.num_steps, 2, 4)
    assert latency.shape == (args.num_steps, 2, 4)
    assert rate_tv.shape == tv.shape
    assert target_rate.shape == (2, 4)
    assert target_latency.shape == (5, 2, 4)
    assert torch.all((rate == 0) | (rate == 1))
    assert torch.all((latency == 0) | (latency == 1))
    assert torch.allclose(delta, expected_delta)

    summary = {
        'rate_shape': list(rate.shape),
        'latency_shape': list(latency.shape),
        'rate_time_var_shape': list(rate_tv.shape),
        'delta': [float(v) for v in delta.tolist()],
        'target_rate_shape': list(target_rate.shape),
        'target_latency_shape': list(target_latency.shape),
        'rate_nonzero': int(rate.sum().item()),
        'latency_nonzero': int(latency.sum().item()),
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
