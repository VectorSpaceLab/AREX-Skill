#!/usr/bin/env python3
"""Synthetic AssociativeLeaky shape and chunked-gradient smoke."""

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


def _make_input(time_steps: int, batch_size: int, in_dim: int, device: torch.device) -> torch.Tensor:
    x = torch.arange(time_steps * batch_size * in_dim, dtype=torch.float32, device=device)
    return (x / x.numel()).reshape(time_steps, batch_size, in_dim)


def check_variant(use_q_projection: bool, device: torch.device) -> dict[str, object]:
    torch.manual_seed(23 if use_q_projection else 29)
    time_steps, batch_size, in_dim, num_spiking_neurons, chunk_size = 6, 6, 16, 16, 2
    x = _make_input(time_steps, batch_size, in_dim, device)
    pre = torch.nn.Linear(in_dim, in_dim, bias=False).to(device)
    model = snn.AssociativeLeaky.from_num_spiking_neurons(
        in_dim=in_dim,
        num_spiking_neurons=num_spiking_neurons,
        use_q_projection=use_q_projection,
    ).to(device)

    pre.zero_grad(set_to_none=True)
    model.zero_grad(set_to_none=True)
    y_full = model(pre(x))
    loss_full = y_full.sum()
    loss_full.backward()
    grad_full = pre.weight.grad.detach().clone()
    model_grad_names_full = sorted(name for name, p in model.named_parameters() if p.grad is not None)

    pre.zero_grad(set_to_none=True)
    model.zero_grad(set_to_none=True)
    y_chunks = []
    for start in range(0, batch_size, chunk_size):
        end = min(start + chunk_size, batch_size)
        y_chunk = model(pre(x[:, start:end, :]))
        y_chunks.append(y_chunk)
        y_chunk.sum().backward()
    y_chunked = torch.cat(y_chunks, dim=1)
    grad_chunked = pre.weight.grad.detach().clone()
    model_grad_names_chunked = sorted(name for name, p in model.named_parameters() if p.grad is not None)

    expected_shape = (time_steps, batch_size, num_spiking_neurons)
    assert tuple(y_full.shape) == expected_shape
    assert tuple(y_chunked.shape) == expected_shape
    assert torch.allclose(y_full, y_chunked, atol=1e-6)
    assert torch.allclose(grad_full, grad_chunked, atol=1e-6)
    if use_q_projection:
        assert model.to_q is not None and "to_q.weight" in model_grad_names_chunked
    else:
        assert model.to_q is None

    return {
        "use_q_projection": use_q_projection,
        "output_shape": list(y_full.shape),
        "full_chunked_maxdiff": float((y_full - y_chunked).detach().abs().max().cpu()),
        "grad_maxdiff": float((grad_full - grad_chunked).detach().abs().max().cpu()),
        "model_grad_names_full": model_grad_names_full,
        "model_grad_names_chunked": model_grad_names_chunked,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--device", default="cpu", help="Torch device, e.g. cpu or cuda:0")
    args = parser.parse_args()
    device = _device(args.device)

    results = [check_variant(True, device), check_variant(False, device)]
    print(json.dumps({"status": "ok", "device": str(device), "variants": results}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
