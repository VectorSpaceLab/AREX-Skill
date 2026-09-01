---
name: recovery_evaluation_harness
description: Run a bounded soft-mode IMPALA V-trace recovery harness and emit validator-compatible evidence.
---

Use this skill for soft-mode recovery of IMPALA/V-trace when full distributed Atari or DMLab training is unavailable. Inputs are an attempt directory and generated skills root. Outputs are validator-compatible recovery artifacts and mechanism checks.

Workflow: read the module plan, construct a tiny policy-lagged trajectory, call the actor-learner protocol skill, cross-check the V-trace target skill, call the actor-critic update skill, save command and invocation evidence, and run the Distiller recovery gate. It must not read any original source repository.

Validation: execute `python scripts/run_recovery.py <attempt_dir> <skills_root>` from the skill root or through the attempt-level wrapper. Limitations: this is reduced recovery only and cannot be reported as full IMPALA benchmark reproduction.

