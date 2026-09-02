---
name: sbi_recovery_diagnostics
description: Validate reduced or full SBI recovery artifacts, source boundaries, mechanism checks, and metric reporting.
---

# SBI Recovery Diagnostics

Use this skill when a Paper2Skills recovery for the `sbi` toolkit needs to declare whether it is full or reduced, prove that the original repository was not used, and validate that the simulator-training-posterior mechanism was actually exercised.

Do not use this skill as a replacement for running the recovery experiment. It checks artifacts produced by executable recovery commands.

## Inputs

- Runtime handoff with full-runtime readiness and blockers.
- Recovery result with metrics, target metadata, and mechanism checks.
- Training trace and generated-data item for reduced recovery.
- Source manifest and generated-skill invocation logs.

## Outputs

- Diagnostic JSON with `ok`, `errors`, and `warnings`.
- A concise interpretation of whether the recovery scope is valid for soft or hard mode.

## Workflow

1. Check that full-runtime claims match the runtime handoff.
2. For reduced recovery, require data-item provenance, before/after loss, and parameter or optimizer-state changes.
3. Confirm that posterior API checks and generated skill invocations were recorded.
4. Scan the source manifest for forbidden original-repository paths.
5. Confirm that the recovery metric is numeric and tied to the declared target.

## Validation

Run:

```bash
python /share/project/yuyang/workspace/Paper2Skills/Distiller/skills/module-to-skill/scripts/validate_skill_tree.py /share/project/yuyang/workspace/Paperbench/record/case15/extracted_skills_attempt_001/sbi_toolkit/sbi_recovery_diagnostics --run-tests
```

For standalone validation of an attempt:

```bash
python scripts/recovery_diagnostics.py --attempt-dir /path/to/attempt
```

## Limitations

The diagnostic script checks artifact consistency. It cannot prove that a full `sbi` package result is scientifically accurate without the underlying executable recovery logs and metrics.
