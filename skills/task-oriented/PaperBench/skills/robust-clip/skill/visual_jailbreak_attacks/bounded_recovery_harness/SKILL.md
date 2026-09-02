---
name: bounded_recovery_harness
description: Run auditable soft-mode visual jailbreak proxy recovery using generated skills and source-boundary logs.
---

# Bounded Recovery Harness

Use this skill when full visual-language-model attack recovery is blocked but soft-mode recovery allows a declared, executable, mechanism-faithful proxy. The harness must not read the original source repository during recovery; it uses only the paper artifacts, module plan, generated skills, runtime handoff, and safe proxy fixtures.

## Inputs

- `attempt_dir` containing `module_plan.json` and `environment/runtime_handoff.json`.
- `generated_skills_root` containing `safe_corpus_protocol`, `visual_pgd_prompt_optimizer`, and `jailbreak_proxy_evaluator`.
- Optional safe proxy parameters such as vector size, steps, and threshold.

## Outputs

- `recovery/recovery_result.json`.
- `recovery/logs/training_trace.json`.
- `recovery/logs/generated_data_item.json`.
- `recovery/logs/generated_skill_invocations.json`.
- `recovery/logs/experiment_command_log.json`.
- `recovery/source_manifest.json`.

## Workflow

1. Read the recovery target from `module_plan.json` and the runtime decision from `environment/runtime_handoff.json`.
2. Declare proxy recovery if full VLM packages, weights, or toxicity APIs are not available.
3. Use the safe corpus protocol to build a non-overlapping train/held-out proxy item.
4. Use the visual PGD optimizer to optimize a tiny continuous visual prompt.
5. Use the proxy evaluator to compute held-out `obedience_delta`.
6. Write mechanism checks showing loss decrease, prompt change, optimizer execution, source isolation, and threshold success.
7. Save all artifacts before running the Distiller recovery validator.

## Validation

Run:

```bash
python scripts/run_proxy_recovery.py --attempt-dir <attempt_dir> --skills-root <generated_skills_root>
```

Then run the bundled `validate_recovery_experiment.py` on the attempt directory.

## Limitations

This harness is a soft-mode proxy. It does not claim the original paper's harmful-content metrics or full VLM behavior. It verifies the core continuous visual prompt optimization and held-out generalization mechanism.
