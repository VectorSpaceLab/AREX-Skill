#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path
from typing import Any

import torch
from torch import nn
from spikingjelly.activation_based import memopt, op_counter, precision


class ToyBlock(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.seq = nn.Sequential(nn.Linear(4, 4), nn.ReLU(), nn.Linear(4, 4))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.seq(x)


class ToyNet(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.blocks = nn.Sequential(ToyBlock(), ToyBlock())
        self.head = nn.Linear(4, 2)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.head(self.blocks(x))


def compact_capability(model: nn.Module, device: torch.device, mode: str) -> dict[str, Any]:
    try:
        report = precision.build_capability_report(model, device, mode)
        try:
            precision.validate_capability(report)
            validation = "passed"
        except Exception as exc:  # expected for unsupported optional modes
            validation = f"failed: {type(exc).__name__}: {exc}"
        return {
            "requested_mode": mode,
            "device": str(device),
            "can_convert": report.get("can_convert"),
            "can_execute": report.get("can_execute"),
            "execution_note": report.get("execution_note"),
            "validation": validation,
        }
    except Exception as exc:  # pragma: no cover - environment dependent
        return {"requested_mode": mode, "error": f"{type(exc).__name__}: {exc}"}


def run_precision(device_name: str) -> dict[str, Any]:
    device = torch.device(device_name)
    model = nn.Sequential(nn.Linear(4, 4), nn.ReLU(), nn.Linear(4, 2)).to(device)
    cfg = precision.PrecisionConfig(mode="fp32", strictness="warn", device=str(device))
    artifacts = precision.prepare_model_for_precision(model, device, cfg)

    opt = torch.optim.SGD(artifacts.model.parameters(), lr=0.01)
    opt.zero_grad(set_to_none=True)
    x = torch.randn(2, 4, device=device)
    loss = artifacts.model(x).square().mean()
    grad_norm = artifacts.backward(loss, opt, step_optimizer=True)

    with tempfile.TemporaryDirectory() as tmpdir:
        precision.save_precision_reports(artifacts, tmpdir)
        report_files = sorted(path.name for path in Path(tmpdir).glob("*.json"))

    capability_modes = ["fp32", "bf16", "fp8-torchao", "fp8-te"]
    capabilities = {
        mode: compact_capability(artifacts.model, device, mode)
        for mode in capability_modes
    }

    return {
        "status": "passed",
        "effective_mode": artifacts.effective_config.mode,
        "fallback_reason": artifacts.fallback_reason,
        "loss": float(loss.detach().cpu().item()),
        "grad_norm": grad_norm,
        "report_files": report_files,
        "capabilities": capabilities,
    }


def compact_summary(summary: Any) -> dict[str, Any]:
    fields = [
        "profile",
        "checkpoint_budget",
        "prefer",
        "requested_level",
        "applied_level",
        "compress_x",
        "allow_expensive_profiling",
        "gc_wrap_count",
        "gc_selected_count",
        "notes",
        "recommendation",
    ]
    return {field: getattr(summary, field, None) for field in fields}


def run_memopt_and_energy(device_name: str) -> dict[str, Any]:
    device = torch.device(device_name)
    model = ToyNet().to(device)
    x = torch.randn(2, 4, device=device, requires_grad=True)

    energy = op_counter.estimate_compute_energy(model, x)
    optimized, summary = memopt.memory_optimization(
        model,
        ToyBlock,
        profile="balanced",
        return_summary=True,
    )
    y = optimized(x)

    return {
        "status": "passed",
        "optimized_shape": list(y.shape),
        "memopt_summary": compact_summary(summary),
        "energy_total_pj": float(energy.energy_total_pj),
        "energy_counts": energy.counts,
        "energy_warnings": energy.warnings,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Safe precision, memopt, and op-counter smoke for SpikingJelly."
    )
    parser.add_argument(
        "--case",
        choices=["precision", "memopt", "all"],
        default="all",
        help="which smoke case to run",
    )
    parser.add_argument(
        "--device",
        default="cpu",
        help="device for the tiny probes; defaults to cpu",
    )
    parser.add_argument("--json", action="store_true", help="print JSON report")
    args = parser.parse_args()

    report: dict[str, Any] = {"device": args.device}
    if args.case in {"precision", "all"}:
        report["precision"] = run_precision(args.device)
    if args.case in {"memopt", "all"}:
        report["memopt_and_energy"] = run_memopt_and_energy(args.device)

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(report)


if __name__ == "__main__":
    main()
