---
name: analyze-paper-recovery
description: "Analyze the gap between a recovered paper result and the paper target, decide whether generated skills are acceptable, and produce actionable module-level feedback for another distillation cycle."
metadata:
  disco-role: meta
---

# Analyze Paper Recovery

Use this skill after `recover-paper-result` has produced `recovery/recovery_result.json`. The goal is to decide whether the generated skills are good enough or whether specific module skills need refinement.

Write all analysis artifacts in English.

## Inputs

- `paper_profile.md`
- `module_plan.json`
- `modules/*.md`
- generated skill validation JSON files
- `environment/runtime_handoff.json`
- `environment/logs/command_log.json`
- `recovery/source_manifest.json`
- `recovery/recovery_result.json`
- `recovery/experiment_validation.json`

## Outputs

- `analysis/analysis_report.json`
- `analysis/feedback.md`

## Workflow

1. Confirm the recovery respected the source boundary. If the source manifest includes the original repo, return `refine`.
2. Confirm `recovery/recovery_result.json.paper_target` matches `module_plan.json.fast_recovery_target` for dataset, metric, and target value. If the recovery target drifted, return `refine` until the plan or recovery is corrected.
3. Compare recovered metrics against the target declared in `module_plan.json.fast_recovery_target`.
4. Inspect `recovery_result.json.mechanism_checks` when present. Metric success is not sufficient if the recovery skipped required searches, injected unsupported facts, or failed to exercise a core module contract.
5. Separate full-result gaps from proxy-result gaps:
   - Full result: compare directly to the paper metric.
   - Proxy result: evaluate whether the proxy exercised the method contracts and whether the proxy metric passed its declared threshold.
6. Inspect generated skill validation logs for failures or weak coverage.
7. Inspect `recovery/experiment_validation.json` or run `recover-paper-result/scripts/validate_recovery_experiment.py`. Do not accept a run whose experiment gate fails.
8. Produce a decision:
   - `accept`: skills are usable and recovery/proxy evidence is sufficient.
   - `refine`: skills need another cycle.
9. When refining, assign feedback to concrete module ids and explain what to change.

## Decision Heuristics

Accept if all are true:

- Source boundary is valid.
- The declared module-plan target and the recovered-result target metadata match.
- All module skill validations passed.
- Recovery produced a numeric metric.
- `recovery/experiment_validation.json` reports `ok: true`.
- Recovery has executable command evidence, not only hand-written result JSON.
- The generated skill invocation log proves each claimed core module was called, imported, or cross-checked.
- Mechanism checks pass when the recovery harness records them.
- For full reproduction, the primary metric gap is within the configured tolerance.
- For proxy reproduction, the proxy is justified and exercises the core paper mechanism.

Refine if any are true:

- A module skill test failed.
- The run reports missing packages, model cache, dataset, benchmark files, or
  search credentials as a blocker, but `environment/logs/command_log.json` does
  not show the allowed setup attempts first: isolated environment
  creation/reuse under the DisCo-private env root, targeted package installs,
  permitted model/dataset downloads, configured network/VPN or mirror retries,
  or a user credential/permission request when credentials are genuinely
  required. Treat this as `refine` of environment preparation, not a terminal
  blocker.
- `environment/runtime_handoff.json` points to a private recovery Python, but
  the recovery experiment command log or source manifest shows the experiment
  used the host/shared conda Python instead.
- The recovery result targets a different dataset, metric, or paper value than the module plan.
- A proxy recovery omits `mechanism_checks`; proxy acceptance requires explicit evidence that the paper mechanism was exercised.
- A nontrivial recovery run lacks `environment/runtime_handoff.json`, or recovery ignores a handoff blocker by claiming a full runtime succeeded without matching package/model evidence.
- Environment preparation lacks `environment/logs/command_log.json`, or that file does not contain a command list for subprocess probes, installs, downloads, clone attempts, and version checks.
- `recovery/experiment_plan.md`, `recovery/logs/experiment_command_log.json`, `recovery/logs/generated_skill_invocations.json`, or `recovery/experiment_validation.json` is missing.
- The experiment command log has no successful command, no command strings, or cannot be tied to the produced recovery result.
- A benchmark/runtime source was obtained, but the recovery item is only described as benchmark-style and does not record concrete resource-file provenance when resource-derived construction was feasible.
- A recovery reuses a benchmark checkout from another attempt or workspace path without recording the fresh-fetch blocker, reused path, commit/version, concrete files used, and a current-attempt snapshot or copy of those resource files. Reusing previous attempt generated data, prompts, outputs, training logs, or recovery results as evidence should return `refine`.
- A reduced data-generation/training recovery lacks `recovery/logs/generated_data_item.json` or a discoverable primary training trace with loss/metric before and after, parameter or optimizer-change evidence, and fallback/full-runtime booleans. Prefer `params_before` and `params_after` in the trace; `parameters_before` and `parameters_after` may appear as readable aliases.
- The recovery claims to exercise a generated loss, scoring, retrieval, or prompting module but bypasses that module with duplicate harness logic and provides no cross-check or equivalence log.
- A trajectory-derived skill puts failed or invalid actions into `golden_workflow` instead of keeping them in `mistake_analysis`, unless the paper requires retaining failed attempts in the ideal plan.
- A prompt-separation test rejects ordinary task/environment words instead of privileged-only skill content; refine the test contract rather than weakening the prompt-separation invariant.
- The recovery metric passes but the mechanism check shows missing required searches, unsupported Reason-in-Documents facts, or no live search events.
- Recovery skipped a core method component.
- The result relies on original repo code.
- The metric gap is large and unexplained.
- The raw answer is semantically correct but the extracted/evaluated answer fails due to a missing answer-formatting or canonicalization rule.
- A retrieval/document-refinement module injects final-answer text or other downstream-control text that is outside its output contract.
- The run used a mutable environment change that was not authorized or not recorded.
- The artifacts are not sufficient for a future agent run to repeat the experiment.

## Scripts

- `scripts/compare_recovery.py`: compare recovery metrics and produce `analysis_report.json`.
