#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def build_proxy_result(attempt_dir: Path, skills_root: Path, runtime_handoff: Path) -> dict:
    plan = load_json(attempt_dir / "module_plan.json")
    trace = load_json(attempt_dir / "recovery" / "logs" / "training_trace.json")
    compression = load_json(attempt_dir / "recovery" / "logs" / "latent_contract.json")
    attention = load_json(attempt_dir / "recovery" / "logs" / "cross_attention.json")
    spatial = load_json(attempt_dir / "recovery" / "logs" / "spatial_plan.json")
    handoff = load_json(runtime_handoff) if runtime_handoff.exists() else {"blockers": ["runtime handoff missing"]}
    mechanism_checks = dict(trace.get("mechanism_checks", {}))
    mechanism_checks.update({
        "perceptual_compression_contract_validated": compression.get("ok") is True,
        "cross_attention_conditioning_executed": bool(attention.get("conditioned")),
        "attention_rows_normalized": all(abs(value - 1.0) < 1e-6 for value in attention.get("row_sums", [])),
        "convolutional_latent_grid_validated": spatial.get("ok") is True,
        "full_runtime_blocked": bool(handoff.get("blockers")) or handoff.get("runtime_ready") is False,
    })
    metric = trace["loss_before"] - trace["loss_after"]
    result = {
        "schema_version": 1,
        "paper_id": plan["paper_id"],
        "experiment": plan["fast_recovery_target"]["dataset"],
        "is_proxy": True,
        "sample_count": 1,
        "metrics": {"ldm_loss_reduction": metric, "loss_before": trace["loss_before"], "loss_after": trace["loss_after"]},
        "paper_target": plan["fast_recovery_target"],
        "commands": ["python recovery/run_recovery.py"],
        "artifacts": [
            "recovery/logs/generated_data_item.json",
            "recovery/logs/training_trace.json",
            "recovery/logs/latent_contract.json",
            "recovery/logs/cross_attention.json",
            "recovery/logs/spatial_plan.json",
        ],
        "mechanism_checks": mechanism_checks,
        "notes": "Declared soft-mode reduced proxy: full LDM checkpoints and datasets are unavailable for bounded recovery, but latent compression shape, noising/loss, cross-attention, spatial grid, and optimizer update were executed through generated skills.",
    }
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--attempt-dir", required=True)
    parser.add_argument("--skills-root", required=True)
    parser.add_argument("--runtime-handoff", required=True)
    parser.add_argument("--output", default="")
    args = parser.parse_args()
    attempt_dir = Path(args.attempt_dir).resolve()
    result = build_proxy_result(attempt_dir, Path(args.skills_root).resolve(), Path(args.runtime_handoff).resolve())
    output = Path(args.output).resolve() if args.output else attempt_dir / "recovery" / "recovery_result.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if result["metrics"]["ldm_loss_reduction"] > 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
