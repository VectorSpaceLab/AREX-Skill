#!/usr/bin/env python3
"""Build a VAE recovery_result.json from a module plan and training trace."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

REQUIRED_CHECKS = [
    "encoder_executed",
    "reparameterization_executed",
    "decoder_executed",
    "reconstruction_loss_computed",
    "kl_divergence_computed",
    "optimizer_step_executed",
]


def build_result(module_plan: dict, trace: dict, command: str = "", artifacts: list[str] | None = None) -> dict:
    target = module_plan["fast_recovery_target"]
    checks = dict(trace.get("mechanism_checks", {}))
    missing = [key for key in REQUIRED_CHECKS if checks.get(key) is not True]
    if missing:
        raise ValueError("missing true mechanism checks: " + ", ".join(missing))
    total_before = float(trace["total_loss_before"])
    total_after = float(trace["total_loss_after"])
    loss_delta = float(trace.get("loss_delta", total_before - total_after))
    paper_target = {
        "dataset": target.get("dataset"),
        "split": target.get("split"),
        "metric": target.get("metric"),
        "value": target.get("paper_value"),
        "proxy": bool(target.get("proxy")),
        "rationale": target.get("rationale", ""),
    }
    checks.update({
        "loss_delta_numeric": isinstance(loss_delta, float),
        "params_before_after_recorded": bool(trace.get("params_before")) and bool(trace.get("params_after")),
        "target_metadata_preserved": True,
    })
    return {
        "schema_version": 1,
        "paper_id": module_plan.get("paper_id", "vae_cifar_variational_inference"),
        "experiment": f"{target.get('dataset')}:{target.get('split')}",
        "is_proxy": bool(target.get("proxy")),
        "sample_count": int(trace.get("sample_count", 0)),
        "metrics": {
            "loss_delta": loss_delta,
            "total_loss_before": total_before,
            "total_loss_after": total_after,
            "reconstruction_loss_before": float(trace["reconstruction_loss_before"]),
            "reconstruction_loss_after": float(trace["reconstruction_loss_after"]),
            "kl_loss_before": float(trace["kl_loss_before"]),
            "kl_loss_after": float(trace["kl_loss_after"]),
        },
        "paper_target": paper_target,
        "commands": [command] if command else [],
        "artifacts": artifacts or [],
        "mechanism_checks": checks,
        "notes": "Soft-mode reduced proxy: executes VAE encoder, reparameterization, decoder, BCE/KL loss, and optimizer step on deterministic synthetic binary images; does not claim full MNIST/CIFAR training.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--module-plan", required=True)
    parser.add_argument("--trace", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--command", default="")
    parser.add_argument("--artifact", action="append", default=[])
    args = parser.parse_args()
    module_plan = json.loads(Path(args.module_plan).read_text(encoding="utf-8"))
    trace = json.loads(Path(args.trace).read_text(encoding="utf-8"))
    result = build_result(module_plan, trace, args.command, args.artifact)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({"ok": True, "output": str(output), "metric": result["metrics"]["loss_delta"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
