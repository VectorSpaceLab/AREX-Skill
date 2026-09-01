---
name: pope_recovery_harness
description: Run a bounded POPE proxy recovery experiment with auditable generated-skill invocations and metrics.
---

# POPE Recovery Harness

Use this skill during Paper2Skills recovery for the POPE hallucination-evaluation paper when full LVLM evaluation is too expensive or unavailable and soft-mode proxy recovery is allowed. It must be used with the protocol builder, negative sampling, and answer evaluator skills.

Do not use this skill to read the original POPE repository during recovery. It should consume only the paper artifacts, module plan, generated skills, runtime handoff, and current recovery data.

## Inputs

- Attempt directory containing `module_plan.json` and `environment/runtime_handoff.json`.
- Generated skill root containing POPE protocol, sampling, and evaluator skills.
- Optional tiny annotation records; otherwise the harness creates a mechanism-faithful synthetic dataset.

## Outputs

- `recovery/recovery_result.json` with metrics and mechanism checks.
- `recovery/logs/generated_data_item.json` with records, questions, answers, and per-strategy metrics.
- `recovery/logs/generated_skill_invocations.json` proving generated skills were imported and called.
- `recovery/source_manifest.json` identifying allowed sources.

## Workflow

1. Read the module plan target and runtime handoff.
2. Create or load a tiny annotation-style object dataset.
3. Import and call `pope_protocol_builder` for random, popular, and adversarial strategies.
4. Use a deterministic answerer that answers positives correctly and introduces one controlled false positive to exercise hallucination metrics.
5. Import and call `pope_answer_evaluator` for every strategy.
6. Aggregate F1, accuracy, yes ratio, and mechanism checks.
7. Write all recovery artifacts and leave validation to Distiller's recovery experiment validator.

## Validation

Run:

```bash
python scripts/run_pope_recovery.py --self-test
python tests/test_recovery_harness.py
```

A full Distiller attempt should then run `recover-paper/scripts/validate_recovery_experiment.py` on the attempt directory.

## Limitations

This harness is a reduced proxy, not full LVLM inference on COCO. It is acceptable only when soft recovery is configured and the proxy is declared in the recovery plan and result.