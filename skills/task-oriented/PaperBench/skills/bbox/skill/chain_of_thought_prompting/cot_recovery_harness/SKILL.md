---
name: cot_recovery_harness
description: Run a bounded standard-versus-chain-of-thought proxy recovery experiment and emit auditable recovery artifacts.
---

# Chain-of-Thought Recovery Harness

Use this skill when recovering a fast, mechanism-faithful result for the chain-of-thought prompting paper under bounded runtime. The harness is designed for soft-mode proxy recovery when proprietary or very large model paths are unavailable. Do not use it to claim full PaLM 540B reproduction unless the runtime handoff proves such a model is actually ready.

## Inputs

- Attempt directory with `module_plan.json`.
- Generated skill root containing `cot_prompt_templates`, `cot_answer_extraction`, and `cot_equation_calculator`.
- `environment/runtime_handoff.json`.
- Optional mini dataset JSON. If omitted, the harness creates deterministic GSM8K-style items in the current attempt.

## Outputs

- `recovery/logs/generated_data_item.json`
- `recovery/logs/predictions.json`
- `recovery/logs/training_trace.json`
- `recovery/logs/generated_skill_invocations.json`
- `recovery/recovery_result.json`

## Workflow

1. Read the module-plan target and runtime handoff.
2. Choose full recovery only if the runtime handoff says a suitable model is ready; otherwise declare reduced proxy recovery.
3. Build standard and chain-of-thought prompts through `cot_prompt_templates`.
4. Run a bounded deterministic predictor for proxy mode. It solves multi-step arithmetic only on the chain-of-thought path and uses a weaker direct baseline for standard prompting.
5. Extract final answers through `cot_answer_extraction`.
6. Verify reasoning equations through `cot_equation_calculator`.
7. Score accuracy, write mechanism checks, and save a small parameter-update trace that documents the proxy baseline refinement.
8. Emit recovery result metadata whose `paper_target` exactly matches `module_plan.fast_recovery_target`.

## Validation

Run:

```bash
python scripts/run_cot_proxy_recovery.py --self-test
python -m unittest discover -s tests
```

In a Distiller attempt, run the script with `--attempt-dir`, `--skill-root`, and `--runtime-handoff`, then validate the attempt with `validate_recovery_experiment.py`.

## Limitations

The proxy uses deterministic arithmetic logic rather than an LLM. It is evidence that the generated skills preserve the paper mechanism, not evidence that a particular large language model reaches the paper's reported accuracy.
