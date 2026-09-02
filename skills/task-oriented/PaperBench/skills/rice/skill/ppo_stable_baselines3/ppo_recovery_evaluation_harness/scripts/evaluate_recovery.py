from __future__ import annotations

import json
from pathlib import Path

REQUIRED_CHECKS = [
    "gae_executed",
    "clipped_surrogate_executed",
    "value_loss_executed",
    "optimizer_step_executed",
    "parameters_changed",
]


def evaluate_recovery_evidence(training_trace: dict, source_manifest: dict | None = None, is_proxy: bool = True) -> dict:
    mechanism = dict(training_trace.get("mechanism_checks", {}))
    params_changed = training_trace.get("params_before") != training_trace.get("params_after")
    mechanism.setdefault("parameters_changed", params_changed)
    missing = [name for name in REQUIRED_CHECKS if mechanism.get(name) is not True]
    forbidden = []
    if source_manifest:
        forbidden = list(source_manifest.get("forbidden_sources_detected", []) or [])
    passed_count = len(REQUIRED_CHECKS) - len(missing)
    pass_rate = passed_count / len(REQUIRED_CHECKS)
    return {
        "mechanism_pass_rate": pass_rate,
        "passed": pass_rate == 1.0 and not forbidden and is_proxy is True,
        "missing": missing,
        "forbidden_sources_detected": forbidden,
        "required_checks": REQUIRED_CHECKS,
    }


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("training_trace")
    parser.add_argument("--source-manifest", default="")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    trace = json.loads(Path(args.training_trace).read_text(encoding="utf-8"))
    manifest = json.loads(Path(args.source_manifest).read_text(encoding="utf-8")) if args.source_manifest else None
    result = evaluate_recovery_evidence(trace, manifest, is_proxy=True)
    Path(args.output).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
