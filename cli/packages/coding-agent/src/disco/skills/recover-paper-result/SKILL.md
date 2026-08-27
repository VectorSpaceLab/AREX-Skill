---
name: recover-paper-result
description: "Reproduce a fast paper result using only the paper, module documents, generated module skills, and datasets, explicitly forbidding reads from the original source repository during recovery."
metadata:
  disco-role: meta
---

# Recover Paper Result

Use this skill after all module skills have been generated and validated. The goal is to test whether the skills can reconstruct the paper's behavior without relying on the original repository.

All recovery artifacts must be in English.

Before recovery, load `prepare-paper-recovery-env` when available and read `environment/runtime_handoff.json`. Treat the handoff as the authoritative runtime preflight: use its allowed sources, package/model blockers, benchmark snapshot paths, GPU notes, and environment mutation status instead of repeating broad discovery.

## Hard Source Boundary

During recovery, do not read the original paper repository. Allowed sources are:

- the paper PDF or extracted paper text
- `paper_profile.md`
- `module_plan.json`
- `modules/*.md`
- generated module skills under the output skill root
- `environment/runtime_handoff.json` and `environment/logs/*`
- downloaded datasets and general package documentation
- web search APIs only when the paper method requires web search

Write `recovery/source_manifest.json` listing every source path or URL used. If any original repo path appears, the recovery is invalid.

For independent evaluation runs, do not use prior attempt outputs as shortcuts. Prior generated data items, prompts, model outputs, training logs, or recovery results are not allowed recovery evidence for the current attempt. If a fresh benchmark or dataset fetch is blocked and a local benchmark checkout from another attempt or workspace path is the only practical source, treat it as a reused benchmark source: record the fresh-fetch command and blocker, the reused path, commit/version if available, why reuse was necessary, and copy or snapshot the concrete resource files used into the current attempt under `recovery/benchmark_sources/`. The current attempt must still derive its own data item and run its own recovery/training step.

## Runtime Boundary

If the user supplies a model path, GPU ids, or environment path, prefer that runtime for recovery. If the supplied environment has incompatible packages, do not modify it unless the user explicitly permits mutation. Use an existing compatible environment or create a separate one, and record:

- model path
- Python environment path
- GPU ids
- tensor/pipeline parallel settings
- package blocker if the requested environment could not be used
- whether any environment was modified

## Preflight and Time Budgets

Do a bounded preflight before expensive recovery:

- Check user-supplied paths first. Then check only known local cache roots such as `$HF_HOME`, `$TRANSFORMERS_CACHE`, `~/.cache/huggingface`, the workspace, and explicitly named project paths. Do not recursively scan broad NFS roots such as `/share/project`.
- Use short network probes for model and dataset endpoints and record the status, elapsed time, and error type in `recovery/logs/`.
- Stage package installation: first inspect whether required imports already exist, then install the smallest missing group. Put a timeout around each install attempt. If an install stalls, terminate it, record the partial command output and blocker, and continue only with a declared fallback.
- If the handoff says a package/model/dataset is missing but the command log
  does not show an allowed isolated environment setup, install attempt,
  permitted download, or user credential/permission request, go back to
  `prepare-paper-recovery-env` instead of accepting the blocker. Recovery
  should consume a prepared runtime handoff, not turn first-pass probes into a
  final blocked result.
- If the handoff provides `environment.python` or `python.executable` inside a
  private recovery environment, use that executable for the recovery harness and
  record it in `recovery/logs/experiment_command_log.json` and
  `recovery/source_manifest.json`. Do not silently run recovery with the
  host/shared conda Python after preparing a private env.
- Write the recovery harness, log schema, and source manifest before starting long installs or downloads, so an interrupted run still leaves auditable artifacts.
- Record process cleanup for any killed install, download, or benchmark command. A successful recovery must not leave stray package installers, model downloads, or benchmark runners alive.

## Workflow

1. Read the paper target from `module_plan.json.fast_recovery_target`.
2. Select the smallest meaningful dataset subset that exercises the paper mechanism.
3. Read `environment/runtime_handoff.json`. If it is missing, run
   `prepare-paper-recovery-env` first or record a blocker; do not continue to an
   accepted recovery with an unprepared or still-pending environment stage.
4. Write `recovery/experiment_plan.md` before running the experiment. It must name the full target, reduced target if any, chosen target, why it is the strongest feasible target, commands to run, expected artifacts, and minimum acceptance criteria.
5. Load the generated module skills needed for the experiment.
6. Build or run a recovery harness from the generated skills. Do not hand-write `recovery_result.json` as the primary evidence; it must be produced by an executable command such as `python recovery/run_recovery.py`.
7. Record the experiment command(s), return codes, elapsed time, and stdout/stderr tails in `recovery/logs/experiment_command_log.json`.
8. Exercise each core generated module that the proxy claims to validate, or record why a module is not applicable. If scoring/loss logic is split into a standalone generated skill and a training harness skill, call or cross-check the standalone skill and log the comparison.
9. Write `recovery/logs/generated_skill_invocations.json` listing each generated module exercised, the evidence type (`called script`, `imported helper`, `cross-check`, or `not applicable`), and the log/artifact path proving it.
10. Populate `recovery_result.json.paper_target` from `module_plan.json.fast_recovery_target`; do not hard-code a different dataset, metric, or target value in the recovery harness.
11. For proxy recovery, add `mechanism_checks` that show the selected run exercised the paper mechanism. Include required search/tool calls, grounding checks for intermediate evidence, and any module-specific invariants.
12. Record commands, parameters, sample count, predictions, labels, metrics, training traces, and the runtime handoff path.
13. Save `recovery/recovery_result.json`.
14. Run the experiment gate and save it:

```bash
python <skills_root>/recover-paper-result/scripts/validate_recovery_experiment.py \
  <attempt_dir> \
  --output <attempt_dir>/recovery/experiment_validation.json
```

15. If the gate fails, fix the recovery artifacts or mark the attempt as blocked/refine. Do not proceed to an `accept` analysis with a failing gate.
16. If the task is QA, use `scripts/evaluate_qa.py` for EM/F1.

## QA Recovery Requirements

- The final answer should be the shortest answer span/entity compatible with the dataset label.
- If the model returns a sentence-form answer, apply a documented extraction/canonicalization step and record both raw and extracted answers.
- Intermediate document-refinement modules must not inject final-answer markers into the main reasoning chain unless the paper explicitly requires it.
- Preserve raw model generations and the final trajectory under `recovery/logs/`.

## Recovery Result Schema

```json
{
  "schema_version": 1,
  "paper_id": "short_slug",
  "experiment": "dataset or table target",
  "is_proxy": true,
  "sample_count": 1,
  "metrics": {"em": 1.0, "f1": 1.0},
  "paper_target": {"metric": "f1", "value": 0.497},
  "commands": ["command used"],
  "artifacts": ["relative/path"],
  "mechanism_checks": {},
  "notes": "limitations and interpretation"
}
```

## Acceptance Criteria

- The recovery harness imports or follows the generated skills.
- `recovery/experiment_plan.md` exists and explains the selected experiment strength.
- `recovery/logs/experiment_command_log.json` contains the actual command(s) that produced `recovery_result.json`, including return code and output tails.
- `recovery/logs/generated_skill_invocations.json` proves generated skill scripts/helpers were called or cross-checked.
- `recovery/experiment_validation.json` exists and reports `ok: true`.
- The recovery source manifest includes `environment/runtime_handoff.json` when the environment stage ran.
- `run_manifest.json.stages.prepare_environment` is `complete` or `blocked`
  before recovery artifacts are accepted.
- The original source repo is absent from the source manifest.
- The recovery result target matches `module_plan.json.fast_recovery_target`.
- The result includes an actual metric, not just a qualitative claim.
- Proxy recovery includes explicit `mechanism_checks`; a high metric alone is not enough when the proxy is meant to validate an algorithmic loop.
- Metric failure caused by formatting must trigger refinement of the evaluation or prompting skill before acceptance.
- Heavy full-scale experiments may be replaced by a proxy only when the proxy is declared and justified.
- A toy smoke test may be logged as supporting evidence, but it cannot be accepted as reduced recovery unless it constructs data, runs the paper-relevant mechanism, and passes the experiment gate.
- Failure is acceptable if it is recorded clearly; `analyze-paper-recovery` will turn it into module-level feedback.

## Minimal Recovery Runs

When the user allows a reduced run for papers that require data generation or expensive training, the recovery must still perform real work:

- Build at least one dataset or task item from allowed sources and save the main item log as `recovery/logs/generated_data_item.json`.
- If a benchmark repository or dataset was obtained successfully, derive at least one field of the recovery item from a concrete benchmark resource file when feasible, and record the exact file paths in the item log and source manifest. If the item is only benchmark-style rather than resource-derived, label it clearly and explain why resource-derived construction was not practical.
- Execute at least one actual training or optimizer step when the required runtime is available, and record loss before/after or another numeric training signal. Save the primary trace as `recovery/logs/training_trace.json`; if another filename is also useful, duplicate or reference the same values rather than making the trace hard to find.
- If real model training is blocked, record the blocker and clearly separate any scalar, fake-model, or deterministic proxy step from the requested training. Keep full-stack or required-model booleans such as `training_step_executed` and `qwen3_model_loaded` false unless the required stack actually ran.
- When the user explicitly permits a reduced run and the required model stack is unavailable, an equivalent minimal training run may use a tiny parameterized student implemented with available local packages or the Python standard library. It must consume the constructed data item, compute the paper-inspired loss or its closest faithful proxy, update trainable parameters, and log before/after loss and parameter values. Mark it as `reduced_training_executed`, keep required-model booleans false, and explain that it is not full model training. Set `optimizer_step_executed` true only if trainable parameters or optimizer state actually changed in this approved reduced run.
- The primary training trace must use validator-compatible parameter fields: `params_before` and `params_after`. It may also include clearer aliases such as `parameters_before` and `parameters_after`, but the `params_*` fields must be present when `optimizer_step_executed` is true.
- For self-distillation methods, mechanism checks should distinguish prompt construction, teacher conditioning, student prompt separation, loss computation, and optimizer execution as separate booleans.

## Scripts

- `scripts/evaluate_qa.py`: compute exact match and token F1 for QA prediction files.
- `scripts/validate_recovery_experiment.py`: validate executable experiment evidence before analysis.
