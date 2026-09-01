---
name: tabular_usfa_recovery
description: Run a bounded Trip-MDP proxy experiment that validates USFA TD learning and GPI transfer mechanics.
---

# Tabular USFA Recovery

Use this skill when full USFA navigation training is unavailable but soft-mode recovery permits a declared mechanism-faithful proxy. The experiment must still execute real TD updates, GPI candidate search, and metric computation.

## Inputs

- Training task weights and candidate encodings.
- Test preference grid.
- Output directory for recovery artifacts.
- Paths to the generated USFA helper skills.

## Outputs

- `recovery_result.json` with metric and mechanism checks.
- `logs/training_trace.json` with loss and parameter changes.
- `logs/generated_data_item.json` describing the Trip-MDP proxy item.
- `logs/generated_skill_invocations.json` showing helper skill usage.

## Workflow

1. Build the paper's Trip-MDP-style feature table.
2. Initialize a tabular USFA table with trainable entries for sampled encodings.
3. Run vector TD updates using the linear-reward successor-feature helper.
4. Evaluate interpolated tasks with the GPI helper.
5. Save metrics and mechanism checks from the executable script.

## Validation

Run:

```bash
python tests/test_trip_usfa.py
```

## Limitations

The script is a reduced proxy, not a full 3D navigation reproduction. It is valid only when the run is in soft recovery mode and full runtime blockers are recorded.
