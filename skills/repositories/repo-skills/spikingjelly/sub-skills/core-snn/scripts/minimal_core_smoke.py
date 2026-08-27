#!/usr/bin/env python3
"""Tiny no-download smoke for the core SpikingJelly activation-based APIs."""

from __future__ import annotations

import argparse
import json
from typing import Any

import torch
import torch.nn as nn

from spikingjelly.activation_based import base, functional, layer, monitor, neuron, surrogate


def build_net(in_features: int, hidden_features: int, out_features: int) -> nn.Sequential:
    net = nn.Sequential(
        layer.Linear(in_features, hidden_features, bias=False),
        neuron.IFNode(
            v_threshold=0.5,
            surrogate_function=surrogate.Sigmoid(alpha=4.0),
            store_v_seq=True,
        ),
        layer.Linear(hidden_features, out_features, bias=False),
        neuron.LIFNode(
            tau=2.0,
            decay_input=True,
            v_threshold=1.0,
            surrogate_function=surrogate.ATan(alpha=2.0),
            store_v_seq=True,
        ),
    )

    with torch.no_grad():
        for module in net.modules():
            if isinstance(module, nn.Linear):
                module.weight.fill_(0.4)
    return net


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Tiny SpikingJelly core SNN smoke")
    parser.add_argument("--device", default="cpu", help="torch device, e.g. cpu or cuda:0")
    parser.add_argument("--time-steps", type=int, default=4)
    parser.add_argument("--batch-size", type=int, default=2)
    parser.add_argument("--in-features", type=int, default=3)
    parser.add_argument("--hidden-features", type=int, default=4)
    parser.add_argument("--out-features", type=int, default=2)
    return parser.parse_args()


def assert_reset_state(net: nn.Module) -> list[tuple[str, Any]]:
    snapshot: list[tuple[str, Any]] = []
    for name, value in base.named_memories(net):
        snapshot.append((name, value))
        if torch.is_tensor(value):
            if not torch.allclose(value, torch.zeros_like(value)):
                raise AssertionError(f"memory {name} was not reset: {value}")
        elif value != 0.0:
            raise AssertionError(f"memory {name} was not reset: {value!r}")
    return snapshot


def run_surrogate_probe(device: torch.device) -> float:
    x = torch.linspace(-1.0, 1.0, steps=7, device=device, requires_grad=True)
    sg = surrogate.Sigmoid(alpha=4.0)
    y = sg(x)
    y.sum().backward()
    if x.grad is None:
        raise AssertionError("surrogate gradient did not propagate")
    if not torch.isfinite(x.grad).all():
        raise AssertionError(f"surrogate gradient had non-finite values: {x.grad}")
    return float(x.grad.norm().item())


def main() -> None:
    args = parse_args()
    device = torch.device(args.device)
    if device.type == "cuda" and not torch.cuda.is_available():
        raise SystemExit("CUDA was requested but is not available.")

    torch.manual_seed(0)
    net = build_net(args.in_features, args.hidden_features, args.out_features).to(device)
    x_seq = torch.full(
        (args.time_steps, args.batch_size, args.in_features),
        0.5,
        device=device,
    )

    # 1) Single-step network driven through the multi-step helper.
    functional.set_step_mode(net, "s")
    functional.reset_net(net)
    loop_out = functional.multi_step_forward(x_seq, net)
    loop_memories = assert_reset_state(net)

    # 2) Multi-step network driven directly.
    functional.reset_net(net)
    functional.set_step_mode(net, "m")
    direct_out = net(x_seq)
    torch.testing.assert_close(loop_out, direct_out)

    v_seq_shapes: list[list[int]] = []
    for module in net.modules():
        if isinstance(module, neuron.BaseNode):
            if module.v_seq is None:
                raise AssertionError(f"{module.__class__.__name__}.v_seq was not stored")
            v_seq_shapes.append(list(module.v_seq.shape))
            if module.v_seq.shape[0] != args.time_steps:
                raise AssertionError(
                    f"unexpected v_seq length for {module.__class__.__name__}: {module.v_seq.shape}"
                )

    # 3) Monitor output spikes/voltages and exercise enable/disable/clear.
    functional.reset_net(net)
    output_monitor = monitor.OutputMonitor(net, instance=neuron.BaseNode)
    try:
        with torch.no_grad():
            net(x_seq)
        if output_monitor.monitored_layers != ["1", "3"]:
            raise AssertionError(
                f"unexpected monitored layers: {output_monitor.monitored_layers}"
            )
        if len(output_monitor.records) != 2:
            raise AssertionError(
                f"expected two monitored outputs, got {len(output_monitor.records)}"
            )

        output_monitor.disable()
        functional.reset_net(net)
        with torch.no_grad():
            net(x_seq)
        if len(output_monitor.records) != 2:
            raise AssertionError("disabled monitor recorded extra data")

        output_monitor.clear_recorded_data()
        if output_monitor.records != []:
            raise AssertionError("monitor.clear_recorded_data() did not clear records")

        output_monitor.enable()
        functional.reset_net(net)
        with torch.no_grad():
            net(x_seq)
        if len(output_monitor.records) != 2:
            raise AssertionError("reenabled monitor did not record data")
    finally:
        output_monitor.remove_hooks()

    functional.reset_net(net)
    reset_memories = assert_reset_state(net)
    if any(module.v_seq is not None for module in net.modules() if isinstance(module, neuron.BaseNode)):
        raise AssertionError("v_seq was not cleared by reset")

    surrogate_grad_norm = run_surrogate_probe(device)

    summary = {
        "device": str(device),
        "loop_shape": list(loop_out.shape),
        "direct_shape": list(direct_out.shape),
        "v_seq_shapes": v_seq_shapes,
        "reset_memories": [(name, float(value) if not torch.is_tensor(value) else float(value.sum().item())) for name, value in reset_memories],
        "surrogate_grad_norm": surrogate_grad_norm,
        "monitored_layers": ["1", "3"],
        "loop_memories": [(name, float(value) if not torch.is_tensor(value) else float(value.sum().item())) for name, value in loop_memories],
    }
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
