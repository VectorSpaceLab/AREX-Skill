---
name: paper-skills-distiller
description: "Orchestrate a paper-to-skills distillation loop for AI research papers supplied as local files, URLs, arXiv ids, or titles, optionally with a local or remote repository, by resolving sources, modularizing the paper, creating module skills, preparing recovery runtime, recovering a paper result without the source repo, analyzing gaps, and iterating until acceptable."
metadata:
  disco-role: meta
---

# Paper Skills Distiller

Use this skill as the top-level controller when a user provides a research paper source, with or without an implementation repository source, and wants the paper converted into reusable Agent Skills. The paper source may already be local, or it may be a direct PDF URL, arXiv URL/id, or paper title that must be resolved before the run starts.

All generated skill content must be written in English. Keep user-facing status in the user's language if appropriate, but artifact names, schemas, `SKILL.md` files, scripts, and validation reports should be English.

The default refinement budget is 10 refine cycles after the first recovery. Use the user's supplied `iteration_budget` when present; otherwise record `iteration_budget: 10` in `run_manifest.json`. The user may set any non-negative integer. Stop before starting a refine cycle that would exceed this budget, and summarize the remaining feedback instead of continuing silently.

The default recovery mode is `hard`. In `hard` mode, the run must not accept reduced, proxy, toy, smaller-model, or fallback recovery as success; if the full requested standard cannot run, record a concrete blocker or return `refine`. In `soft` mode, a reduced or proxy recovery may be accepted only when it is explicitly declared, justified, executable, and passes the recovery experiment gate.

Prefer a TOML run config when the user provides one. Use
`../create-paper-skills/assets/distiller-run-config-template.toml` as the
fill-in template and validate it with `scripts/read_run_config.py` before
resolving sources or initializing runs. A config may contain one or more
`[[runs]]` entries for batch distillation.

Default outputs use one run directory with two main children:
`<workspace_root>/<paper_slug>/distillation/` for process artifacts and
`<workspace_root>/<paper_slug>/skills/` for generated reusable skills. Do not
create numbered attempt directories unless the user explicitly supplies a
custom `attempt_dir` for that purpose.

## Source Rules

- Paper: mandatory. Read the full paper or a faithful extracted text version. If the user gives a URL, arXiv id, or title instead of a local path, first resolve it to a local PDF/text artifact and save source acquisition evidence.
- Repository: optional. It may be a local path, Git URL, `none`, or `unknown`. Use it only during modularization and module skill creation. Treat it as implementation evidence, not as a substitute for paper understanding. If it is `unknown`, follow `repo_discovery_mode`: `ask` records candidates/blockers and asks before searching or selecting, `auto` may run bounded GitHub discovery and clone the top candidate, and `disabled` proceeds paper-only.
- Recovery: must not read the original source repository. During recovery, use only the paper, module documents, generated module skills, data, and general package documentation.
- Internet: use only when needed for source acquisition, repo discovery, datasets, package docs, or web-search experiments. If the environment provides a network setup script, source it before network commands. Keep downloads, title searches, repo discovery, and clones bounded and logged.
- Logs: every run must be recorded under its configured distillation directory.

## Required Loop

1. If a run config path is supplied, validate and normalize it with `scripts/read_run_config.py`; otherwise collect the same fields from the user's prompt. For batch configs, process each normalized run independently and keep separate source-resolution, attempt, and summary artifacts. Use `read_run_config.py --slug <paper_slug> --run-only` to write the selected normalized run JSON passed to `init_run.py --run-config`.
2. Resolve paper and optional repo sources when needed with `scripts/resolve_sources.py` or an equivalent bounded, logged procedure. The resolver covers local paths, direct URLs, arXiv URLs/ids, arXiv title search, Git repo URLs, and `repo_discovery_mode=auto` GitHub repo discovery. If a title is not found there, use web search for official or scholarly sources and record the chosen URL. If title or repo discovery is ambiguous, ask the user to choose before proceeding.
3. Initialize the distillation directory with `scripts/init_run.py` using the resolved local paper path, optional resolved repo path, configured `iteration_budget`, configured `recovery_mode`, configured `generated_skills_root`, optional exact `attempt_dir`, and `--run-config` when a normalized config JSON exists.
4. Load `plan-paper-skill-modules` and create:
   - `paper_profile.md`
   - `module_plan.json`
   - one module document per module in `modules/`
   - no more than five modules
5. Validate the module plan with `plan-paper-skill-modules/scripts/validate_module_plan.py`.
6. For each module, load `create-paper-module-skill` and create the module skill under the configured output skill root.
7. Validate every generated module skill with `create-paper-module-skill/scripts/validate_skill_tree.py` and run its tests or smoke checks.
8. Load `prepare-paper-recovery-env` and create `environment/runtime_handoff.json` from bounded package, model, GPU, benchmark, and dataset preparation. If required packages, datasets, or model caches are missing, run the active preparation path first: create/reuse an isolated recovery environment under `$DISCO_CODING_AGENT_DIR/envs/` or `~/.disco/agent/envs/`, install the smallest missing package set, and attempt permitted bounded model/data acquisition before treating the item as blocked.
9. Load `recover-paper-result` and reproduce one fast, meaningful paper result without reading the original repo, using the runtime handoff as recovery input.
10. Load `analyze-paper-recovery` and compare the recovery result with the paper target or an explicitly declared proxy target.
11. If analysis says `refine`, update the relevant workflow guidance, module documents, module skills, environment handoff usage, and recovery harness, then rerun steps 7-10. Stop when status is `accept` or the configured refinement budget is exhausted.
12. After an accepted run passes final and reported validation, classify the complete generated module graph for deployment. Default task-, project-, private-data-, evaluator-, benchmark-, or environment-bound output and all uncertain cases to project scope at `<project-dir>/.agents/skills/`. Use managed scope at `~/.disco/agent/skills/` only with evidence that the graph is self-contained, provenance-backed, independent of transient run state, representative-use verified, and reusable across projects or research tasks. Keep every module in the same scope.
13. Present the classification evidence, exact targets, entry point, verification, unresolved limits, collisions, and shadowing impact. After approval, use the visible `distill-ml-knowledge/scripts/import_operating_skill_graph.mjs` once with every top-level module root and the selected scope. Overwrite requires separate approval. Write `researcher-handoff.md` with the selected scope and exact imported paths, then suggest `/researcher`; if import is declined, record that the graph remains staged.

## Ordering and Runtime Discipline

- Finish and validate the modularization artifacts before heavyweight runtime probing. Do not delay `paper_profile.md`, `module_plan.json`, or `modules/*.md` while searching for models, package caches, datasets, or GPUs.
- Source acquisition happens before distillation initialization when needed, but it should stay bounded: direct local path checks first, then direct URL/arXiv download, then title search only if requested by the user's input, then repo discovery only when `repo_discovery_mode` or user confirmation permits it. Do not treat source acquisition as recovery evidence for reading the original repo.
- Keep filesystem discovery bounded. Do not run broad scans such as `find /share/project ...` or recursive searches across NFS roots. Search only the workspace, user-supplied paths, known cache roots, or a short explicit allowlist, and use timeouts for cache probes.
- Long package installs, model downloads, and benchmark setup commands must have a time budget. If they stall, stop them, record the exact blocker in recovery artifacts, and continue with the best valid lower-cost recovery allowed by the user.
- Missing local dependencies, model caches, datasets, or search credentials are
  not by themselves sufficient to end the run as blocked. First attempt the
  allowed setup path: isolated environment creation, targeted package
  installation, bounded dataset/model acquisition, configured VPN/proxy or
  mirror use, and keyless/public alternatives where valid. Only mark blocked
  after those actions are logged or after asking the user for required
  credentials/permissions that cannot be inferred.
- A fallback or proxy can be useful evidence, but it must not be counted as a successful required runtime unless the recorded mechanism checks prove that the required data item, model/runtime, loss, and optimizer or training step actually ran.
- In `hard` recovery mode, do not count fallback, proxy, reduced training, subset-only evaluation, or smaller-model execution as accepted recovery. Such artifacts may be logged as diagnostics, but analysis must return `refine` or `blocked` unless the full requested standard ran.
- In `soft` recovery mode, reduced or proxy recovery is allowed only as a declared target with executable evidence, generated-skill invocation logs, and `recovery/experiment_validation.json` passing.
- Independent runs must not silently depend on previous runs. Reuse immutable local datasets or benchmark checkouts only as recorded benchmark sources when fresh acquisition is blocked or the user supplied them. Do not reuse previous generated skills, data items, prompts, outputs, training logs, or recovery results as evidence for a new run.
- Runtime setup must produce a handoff before recovery. `recover-paper-result` should not repeat broad environment discovery or silently invent fallback state; it should consume `environment/runtime_handoff.json` and add that handoff to `recovery/source_manifest.json`.

## Distillation Directory Contract

Each distillation directory should contain:

```text
run_manifest.json
run_config.normalized.json   # optional but preferred when a config was used
source_resolution.json       # optional, when paper/repo source acquisition was needed
paper_profile.md
module_plan.json
modules/
  <module_id>.md
generated_skills_validation/
  <module_id>.json
environment/
  runtime_handoff.json
  logs/
    command_log.json
recovery/
  experiment_plan.md
  experiment_validation.json
  source_manifest.json
  recovery_result.json
  logs/
    experiment_command_log.json
    generated_skill_invocations.json
analysis/
  analysis_report.json
  feedback.md
final_validation.json
reports/
  generated-skills/
  verification/
  final/
    final_report.json
    final_report.md
```

Use additional files when useful, but do not omit the core contract. Record failures as artifacts instead of relying on terminal output.

## Quality Bar

A generated module skill is acceptable only if it has:

- A clear trigger description in frontmatter.
- A concise workflow that states when to use the skill and when not to use it.
- Explicit input/output contracts.
- At least one deterministic test, smoke script, or validation command.
- A saved validation JSON whose `ok` is true and whose `tests.attempted` is
  true. Prose-only inspection is not enough for either hard or soft mode.
- No dependence on the original paper repository unless the skill's purpose is explicitly to operate on that repository.
- Enough implementation detail for a future agent run to use the skill without rereading the entire paper.

The whole paper distillation is acceptable only if:

- The module split covers the paper's main method and evaluation pathway.
- `environment/runtime_handoff.json` records package availability, GPU status, model readiness or blockers, benchmark acquisition/reuse, environment mutation status, and allowed recovery sources.
- `environment/logs/command_log.json` records subprocess commands run during environment preparation, including timed-out or failed commands.
- The recovery run exercises the generated skills, not a hand-written one-off solution.
- The recovery result is produced by an executable experiment command whose command log is saved under `recovery/logs/experiment_command_log.json`.
- `recovery/experiment_plan.md` explains full/reduced/toy options and why the chosen target is the strongest feasible experiment.
- `recovery/logs/generated_skill_invocations.json` proves generated module skills were called, imported, or cross-checked.
- The recovery experiment gate is run and saved to `recovery/experiment_validation.json` with `ok: true`.
- The recovery run exercises every generated core module that the proxy claims to validate, or explicitly records why a module is not applicable. If a generated scoring/loss module exists separately from the training harness, the recovery cross-checks it rather than relying only on duplicated harness logic.
- Proxy recovery records explicit `mechanism_checks` that demonstrate the core paper mechanism ran. Do not accept a proxy solely because EM/F1 or another task metric is high.
- If recovery uses a benchmark or dataset repository, the item log and source manifest identify concrete resource files used to derive the sample whenever feasible. A benchmark-style item without resource-file provenance must be labeled as such and justified.
- If recovery reuses a local benchmark checkout from another run or workspace location, the source manifest records the fresh-fetch blocker, reused path, commit/version, concrete files used, and a snapshot or copy of those files inside the current distillation directory.
- At least one recovery run uses the strongest practical real runtime available in the workspace when the user provides one. If the user gives a model path, GPU ids, or an inference environment, record whether it was used; if it could not be used, record the exact blocker and run the best lower-cost fallback.
- The analysis report explains metric gaps and either accepts the result or gives actionable module-level feedback.
- The final artifact contract validator is run and its JSON output is saved to `final_validation.json`.
- The organized final report is written to `reports/final/final_report.md` and
  `reports/final/final_report.json`, and the `reported` validation stage passes.
- The complete module graph has a recorded reusability classification. Any live
  deployment uses one approved scope, excludes process/review artifacts, and is
  recorded with exact paths in `researcher-handoff.md`.
- `run_manifest.json` and `run_config.normalized.json` record `recovery_mode`, and hard-mode runs are not accepted if `recovery_result.json` marks `is_proxy: true` or `mechanism_checks.reduced_training_executed: true`.
- When paper/repo source acquisition was needed, the resolved local paths, commands/network operations, selected title/arXiv id, and blockers are recorded in `source/source_resolution.json` or `reports/final/final_report.md`.

## Refinement Rules From Real Runs

- Do not accept a semantically correct but metric-failing result without improving the relevant evaluation or answer-formatting skill.
- If an intermediate module output contaminates later stages, refine that module's output contract and add a regression test before rerunning recovery.
- If a runtime environment is incompatible, do not mutate it unless the user explicitly allows it. Prefer an existing compatible environment or create a separate environment under `$DISCO_CODING_AGENT_DIR/envs/` or `~/.disco/agent/envs/`, then record the choice in `source_manifest.json`.
- After any refinement, rerun module skill validation and recovery in the current distillation directory or a clearly versioned cycle subdirectory.

## Practical Guidance

Favor small, composable module skills over one monolithic "paper skill". A good split usually separates protocol/data formatting, retrieval/tool adapters, core algorithm loop, scoring/evaluation, and experiment recovery. Keep the number of modules below five by merging thin utility modules into the nearest substantive module.

If the full paper result requires heavy training or unavailable models, check `recovery_mode` before lowering the target. In `hard` mode, record the blocker and do not accept a proxy as success. In `soft` mode, recover a declared proxy result that preserves the paper's mechanism. The proxy must identify the dataset, sample size, metric, paper target, and why the proxy is the fastest faithful test.

## Scripts

- `scripts/read_run_config.py`: validate and normalize a TOML config with one or more Distiller runs.
- `scripts/resolve_sources.py`: resolve local or remote paper/repo sources into local paths before distillation initialization, including optional bounded repo discovery.
- `scripts/init_run.py`: create the distillation directory and manifest, optionally copying a selected normalized run config into the run.
- `scripts/validate_distillation_run.py`: validate that required artifacts exist at each stage.
- `scripts/write_final_report.py`: write `reports/final/final_report.json` and
  `reports/final/final_report.md` from the distillation artifacts.
