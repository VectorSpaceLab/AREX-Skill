---
name: apt_recovery_evaluation_harness
description: Build bounded APT recovery experiments with executable evidence, generated-skill invocation logs, source manifests, and mechanism checks.
---

# APT Recovery Evaluation Harness

Use this skill when a Distiller recovery run needs to test whether generated APT skills can recover the paper's mechanism without reading the original implementation repository. The harness is especially useful in soft mode, where a declared reduced/proxy experiment may be accepted only after executable evidence and validation pass.

## Inputs

- Attempt directory with `module_plan.json`, `paper_profile.md`, and `environment/runtime_handoff.json`.
- Generated skills root containing the APT protocol, transformation, and atomic-loss skills.
- Recovery mode from the normalized run config.
- Bounded command budget and source-boundary constraints.

## Outputs

- `recovery/experiment_plan.md`.
- `recovery/source_manifest.json`.
- `recovery/logs/experiment_command_log.json`.
- `recovery/logs/generated_skill_invocations.json`.
- `recovery/logs/generated_data_item.json`.
- `recovery/logs/training_trace.json`.
- `recovery/recovery_result.json`.

## Workflow

1. Read the fast recovery target from the module plan.
2. Read the runtime handoff and decide whether full neural recovery is available.
3. If full recovery is blocked and soft mode allows proxy recovery, declare the reduced target.
4. Invoke generated helper scripts for sequential proposal records, posterior transformation, and atomic loss.
5. Run an executable experiment command that computes numeric metrics and mechanism checks.
6. Write a source manifest that lists allowed sources and excludes original repositories.
7. Run the Distiller recovery gate after the command completes.

## Validation

The script `scripts/check_recovery_artifacts.py` performs a lightweight local check for key files and mechanism fields. The Distiller gate remains authoritative:

```bash
python scripts/check_recovery_artifacts.py --attempt-dir <attempt_dir>
```

The same script also checks that `source_manifest.json` does not list forbidden sources and that it mentions `runtime_handoff.json`, which catches common source-boundary mistakes before full analysis.

## Limitations

- This skill does not choose ambiguous paper sources.
- It cannot turn a proxy experiment into hard-mode success.
- It should not silently create data from a previous attempt; every recovery run must produce its own command-generated artifacts.
