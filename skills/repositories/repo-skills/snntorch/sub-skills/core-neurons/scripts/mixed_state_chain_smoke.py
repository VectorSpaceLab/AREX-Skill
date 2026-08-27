#!/usr/bin/env python3
"""Difficult synthetic core-neuron smoke.

Combines a stateful stepwise Leaky cell with time-major LinearLeaky and
StateLeaky layers, resets the hidden state between identical batches, and adds
small BatchNormTT/GradedSpikes sanity checks.
"""

from __future__ import annotations

import argparse
import json

import torch
import torch.nn as nn
import snntorch as snn


class MixedStateNet(nn.Module):
    def __init__(self, input_features: int, output_features: int):
        super().__init__()
        self.leaky = snn.Leaky(
            beta=torch.full((input_features,), 0.65),
            threshold=0.35,
            init_hidden=True,
            output=True,
            learn_beta=True,
            learn_threshold=True,
        )
        self.linear = snn.LinearLeaky(
            beta=torch.full((output_features,), 0.8),
            in_features=input_features,
            out_features=output_features,
            output=True,
            learn_beta=True,
            learn_threshold=True,
        )
        self.state = snn.StateLeaky(
            beta=torch.full((output_features,), 0.75),
            channels=output_features,
            output=True,
            learn_beta=True,
            learn_threshold=True,
        )

    def forward(self, x: torch.Tensor) -> dict[str, torch.Tensor]:
        leaky_spk, leaky_mem = [], []
        for step in range(x.shape[0]):
            spk_t, mem_t = self.leaky(x[step])
            leaky_spk.append(spk_t)
            leaky_mem.append(mem_t)

        leaky_spk_seq = torch.stack(leaky_spk)
        leaky_mem_seq = torch.stack(leaky_mem)
        linear_spk, linear_mem = self.linear(leaky_spk_seq)
        state_spk, state_mem = self.state(linear_spk)
        return {
            "leaky_spk": leaky_spk_seq,
            "leaky_mem": leaky_mem_seq,
            "linear_spk": linear_spk,
            "linear_mem": linear_mem,
            "state_spk": state_spk,
            "state_mem": state_mem,
        }


def _device(name: str) -> torch.device:
    dev = torch.device(name)
    if dev.type == "cuda" and not torch.cuda.is_available():
        raise SystemExit("CUDA was requested but torch.cuda.is_available() is False")
    return dev


def assert_allclose_dict(a: dict[str, torch.Tensor], b: dict[str, torch.Tensor]) -> None:
    for key in a:
        assert torch.allclose(a[key], b[key], atol=1e-6), f"Mismatch after reset for {key}"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--device", default="cpu", help="Torch device, e.g. cpu or cuda:0")
    args = parser.parse_args()

    device = _device(args.device)
    torch.manual_seed(19)

    time_steps, batch_size, input_features, output_features = 5, 3, 4, 3
    x = torch.linspace(0.0, 1.0, time_steps * batch_size * input_features)
    x = x.reshape(time_steps, batch_size, input_features).to(device)

    net = MixedStateNet(input_features, output_features).to(device)

    first = net(x)
    assert tuple(net.leaky.mem.shape) == (batch_size, input_features)
    reset_mem = net.leaky.reset_mem()
    assert tuple(reset_mem.shape) == (batch_size, input_features)
    assert torch.count_nonzero(reset_mem).item() == 0

    second = net(x)
    assert_allclose_dict(first, second)

    expected_shapes = {
        "leaky_spk": (time_steps, batch_size, input_features),
        "leaky_mem": (time_steps, batch_size, input_features),
        "linear_spk": (time_steps, batch_size, output_features),
        "linear_mem": (time_steps, batch_size, output_features),
        "state_spk": (time_steps, batch_size, output_features),
        "state_mem": (time_steps, batch_size, output_features),
    }
    for key, shape in expected_shapes.items():
        assert tuple(second[key].shape) == shape, (key, tuple(second[key].shape), shape)
        assert torch.isfinite(second[key]).all().item(), key

    # Prove learnable beta/threshold paths are connected. StateLeaky/LinearLeaky
    # expose learnable decay through tau, not beta.
    loss = second["leaky_mem"].sum() + second["linear_mem"].sum() + second["state_mem"].sum()
    net.zero_grad(set_to_none=True)
    loss.backward()
    assert isinstance(net.leaky.beta, nn.Parameter) and net.leaky.beta.grad is not None
    assert isinstance(net.linear.tau, nn.Parameter) and net.linear.tau.grad is not None
    assert isinstance(net.state.tau, nn.Parameter) and net.state.tau.grad is not None
    assert isinstance(net.leaky.threshold, nn.Parameter) and net.leaky.threshold.grad is not None

    # BatchNorm-through-time and GradedSpikes helpers.
    bntt1d = snn.BatchNormTT1d(output_features, time_steps).to(device)
    bntt1d_out = torch.stack([bntt1d[t](second["linear_mem"][t]) for t in range(time_steps)])
    assert tuple(bntt1d_out.shape) == expected_shapes["linear_mem"]
    assert all(module.bias is None for module in bntt1d)

    bntt2d = snn.BatchNormTT2d(2, time_steps).to(device)
    feature_map = torch.randn(time_steps, batch_size, 2, 4, 4, device=device)
    bntt2d_out = torch.stack([bntt2d[t](feature_map[t]) for t in range(time_steps)])
    assert tuple(bntt2d_out.shape) == tuple(feature_map.shape)
    assert all(module.bias is None for module in bntt2d)

    graded = snn.GradedSpikes(size=output_features, constant_factor=1.5).to(device)
    graded_input = torch.ones(output_features, 1, device=device)
    graded_output = graded(graded_input)
    assert tuple(graded_output.shape) == tuple(graded_input.shape)
    assert torch.allclose(graded_output, torch.full_like(graded_input, 1.5))

    summary = {
        "status": "ok",
        "device": str(device),
        "shapes": {k: list(v.shape) for k, v in second.items()},
        "leaky_hidden_shape": list(net.leaky.mem.shape),
        "bntt1d_shape": list(bntt1d_out.shape),
        "bntt2d_shape": list(bntt2d_out.shape),
        "graded_output": graded_output.detach().cpu().flatten().tolist(),
    }
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
