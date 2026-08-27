# Standard Distiller Run Prompt

Use this file as the reusable prompt for running the Paper2Skills Distiller workflow on one or more papers to generate and verify skills for paper replication. Prefer giving DisCo, Codex, or Claude Code a filled TOML config based on `create-paper-skills/assets/distiller-run-config-template.toml` from the installed Distiller skills directory; use inline fields only for quick one-off runs.

The agent must not silently guess high-impact experiment boundaries. If required information is missing, the agent should ask concise clarification questions before starting long-running recovery work.

For a shorter copy/paste template, use `create-paper-skills/assets/distiller-copy-prompt.md`.

## Preferred Config File

Use `create-paper-skills/assets/distiller-run-config-template.toml` as the standard input contract. Fill one or more `[[runs]]` entries, then give the agent:

```text
Use Distiller to generate and verify paper-replication skills for each run in this config.

config_path: /path/to/distiller_run_config.toml
```

In shell commands below, replace `<skills_root>` with the directory that
contains the installed Distiller skill folders, for example
`cli/packages/coding-agent/src/disco/skills` in an AREX-Skill source checkout,
`cli/packages/coding-agent/dist/disco-resources/skills` in a built npm checkout,
or `~/.agents/skills` for the current Codex user-level install. Treat
`~/.codex/skills` as an explicit legacy compatibility path only.

Before starting source downloads or distillation initialization, the agent must validate the config:

```bash
python <skills_root>/paper-skills-distiller/scripts/read_run_config.py \
  <config_path> \
  --output <workspace_root>/distiller_run_config.normalized.json
```

For a batch config, process each normalized run separately. When initializing a specific run, write a selected-run JSON with:

```bash
python <skills_root>/paper-skills-distiller/scripts/read_run_config.py \
  <config_path> \
  --slug <paper_slug> \
  --run-only \
  --output <workspace_root>/<paper_slug>/distillation/source/run_config.normalized.json
```

Pass that selected JSON to `init_run.py --run-config` and preserve it as `run_config.normalized.json` in the corresponding distillation directory.

## Prompt To Give The Agent

You are running a complete Paper2Skills distillation to generate and verify skills for paper replication using the Distiller workflow skills.

Use these skills in order, and explicitly open each `SKILL.md` before using it:

1. `paper-skills-distiller`
2. `plan-paper-skill-modules`
3. `create-paper-module-skill`
4. `prepare-paper-recovery-env`
5. `recover-paper-result`
6. `analyze-paper-recovery`

Your job is to convert an AI research paper into reusable module-level skills for paper replication, validate those skills, prepare an auditable recovery runtime, run a recovery experiment without reading the original source repository, analyze the result, and iterate if needed.

## Required User Inputs

Before doing substantial work, inspect the local workspace and ask the user for any missing required information. Ask only for information that cannot be safely inferred from local files. If `config_path` is provided, treat the normalized config as the authoritative input and ask only for missing or ambiguous config values.

Required information:

- `config_path`: preferred path to a filled TOML config. If absent, collect the fields below from the prompt.
- `workspace_root`: repository root for Paper2Skills.
- `paper_source`: local path to the paper PDF/text, direct PDF URL, arXiv abs/pdf URL, arXiv id, or paper title.
- `paper_slug`: stable snake_case identifier for this paper/version, such as `search_o1_v4`.
- `original_repo_source`: optional source repository for the paper implementation; use a local path, Git/GitHub URL, `none`, or `unknown`.
- `source_acquisition`: whether remote paper/repo sources may be downloaded or cloned, network timeouts, whether title-search top hits may be selected automatically, and whether implementation repo discovery is allowed.
- `repo_discovery_mode`: `ask`, `auto`, or `disabled` when `original_repo_source` is `unknown`.
- `attempt_dir`: target distillation artifact directory, or permission to use the default `<workspace_root>/<paper_slug>/distillation`.
- `generated_skills_root`: directory where generated paper-replication skills should be written.
- `recovery_target`: dataset, split, metric, paper reference value, and whether proxy recovery is allowed.
- `recovery_mode`: `hard` or `soft`. Default is `hard`; users may set it per run.
- `runtime_constraints`: model path, environment path, GPU ids, API keys, network/VPN setup, search endpoint, and package mutation rules when relevant.
- `iteration_budget`: optional maximum refinement cycles after the first recovery. Default is `10`; the user may set another non-negative integer.
- `language_preference`: user-facing summary language.

If the user has not chosen a recovery target, read the paper first, propose the fastest faithful recovery target, and ask for confirmation before running expensive recovery. If the user explicitly permits automatic target selection, record the rationale in `module_plan.json.fast_recovery_target`.

If the user has not supplied an original repository, proceed paper-only and record that no repo evidence was used. If `original_repo_source` is `unknown`, follow `repo_discovery_mode`: `ask` means ask whether to proceed paper-only or search; `auto` means run bounded repo discovery and clone the top candidate while logging all candidates; `disabled` means proceed paper-only.

If the user has supplied an original repository, it may be used only during modularization and module-skill creation. It must not be read during recovery.

## Clarification Questions

Ask these questions when their answers are missing or ambiguous:

1. What paper source should be distilled, and what slug should identify this run?
2. Is there an original implementation repository source, and may it be used before recovery?
3. Should recovery run in `hard` mode, where reduced/proxy/fallback recovery cannot be accepted as success, or `soft` mode, where a validated reduced/proxy recovery may be accepted when full runtime is blocked?
4. What model/runtime/GPU/network constraints should recovery use?
5. May the agent create or modify Python environments, or should it only use existing environments?
6. Should the distillation directory be newly created, or should an existing run be repaired/resumed?

Do not ask these questions if the values are already explicit in the user's prompt or discoverable from `run_manifest.json`.

## Copy Prompt

Use this compact prompt when starting routine runs:

```text
Use Distiller to generate and verify paper-replication skills for each run in this config.

config_path: /path/to/distiller_run_config.toml
```

## Source Acquisition

The paper and optional repo do not have to be local at the start. Accept these source forms:

- Local paper PDF/text path.
- Direct PDF URL.
- arXiv abs URL, PDF URL, or arXiv id.
- Paper title. Search scholarly sources such as arXiv, OpenReview, ACL Anthology, PMLR, conference proceedings, or the authors' official project page, and ask the user to choose when candidates are ambiguous.
- Local implementation repo path.
- Git/GitHub implementation repo URL.
- `none` when there is no implementation repo.
- `unknown` when the user does not know whether a repo exists.

Before `init_run.py`, resolve remote sources into local paths. Prefer the deterministic resolver for local paths, direct URLs, arXiv URLs/ids, and arXiv title search:

```bash
python <skills_root>/paper-skills-distiller/scripts/resolve_sources.py \
  --workspace-root <workspace_root> \
  --paper-source <paper_source> \
  --slug <paper_slug> \
  --repo-source <original_repo_source> \
  --network-timeout <network_timeout_seconds> \
  --command-timeout <command_timeout_seconds> \
  --repo-discovery-mode <repo_discovery_mode>
```

Add `--allow-title-top-hit` only when the normalized config has `allow_title_top_hit: true`.
If `repo_discovery_mode=auto` and you have a better paper-specific query than
the paper title or slug, add `--repo-search-query "<query>"`.

This writes:

```text
<workspace_root>/<paper_slug>/distillation/source/source_resolution.json
<workspace_root>/<paper_slug>/distillation/source/<paper_slug>.pdf      # when downloaded
<workspace_root>/<paper_slug>/distillation/source/repo/                 # when a Git repo URL or discovered repo is cloned
```

After successful resolution, set:

```text
paper_path=<source_resolution.paper.path>
original_repo_path=<source_resolution.repo.path or empty>
```

If the deterministic resolver cannot identify the paper from a title, use web search to find an official or scholarly paper page/PDF. Prefer stable sources over mirrors. Save the chosen URL, search evidence, and any blockers in `source/source_resolution.json` or `reports/final/final_report.md` before continuing. If title search returns multiple plausible candidates and no exact match, stop and ask the user to choose. Do not silently select a paper by title unless the user explicitly set `source_acquisition` to allow top-hit selection.

Repo discovery is separate from paper resolution. Prefer code links in the paper, arXiv/OpenReview metadata, official project pages, or author GitHub pages when visible. If the deterministic resolver runs GitHub discovery, inspect `source_resolution.repo.candidates` before trusting the selected repo. Ask the user to choose when multiple candidates are plausible, when the top candidate is not clearly tied to the paper, or when using the repo would materially change module boundaries. If a remote paper or repo cannot be fetched, record the blocker in `source_resolution.json` and ask whether to retry, provide a local path, or proceed paper-only when possible.

## Default Paths

Use these defaults only when they match the current workspace:

```text
workspace_root=<current repository root>
distiller_skills_root=<skills_root>
run_root=<workspace_root>/<paper_slug>
distillation_root=<run_root>/distillation
test_root=<run_root>
generated_skills_root=<run_root>/skills
attempt_dir=<run_root>/distillation
```

If `attempt_dir` is not fixed by the user, use the default distillation directory:

```bash
python <skills_root>/paper-skills-distiller/scripts/init_run.py \
  --paper <paper_path> \
  --slug <paper_slug> \
  --test-root <workspace_root>/<paper_slug> \
  --skills-root <workspace_root>/<paper_slug>/skills \
  --generated-skills-root <generated_skills_root> \
  --distiller-skills-root <skills_root> \
  --iteration-budget <iteration_budget> \
  --recovery-mode <recovery_mode> \
  --run-config <selected_normalized_run_json>
```

Add `--repo <original_repo_path>` only when an original repo exists and the user permits using it before recovery. Add `--run-config` when a config was used or when inline prompt fields have been normalized into a JSON file. Add `--attempt-dir <attempt_dir>` only when the normalized config fixed an exact distillation directory.

## Required Workflow

1. Verify the six Distiller skills are visible to the agent. If not, stop and ask the user to install them.
2. Open and follow `paper-skills-distiller/SKILL.md`.
3. If `config_path` is provided, validate it with `read_run_config.py`; otherwise normalize the inline prompt fields into the same schema mentally and record them in `run_config.normalized.json`.
4. For each normalized run, resolve `paper_source` and `original_repo_source` into local paths when needed. Save or preserve `source_resolution.json`.
5. Initialize or repair the distillation directory contract using the resolved local `paper_path`, optional `original_repo_path`, `iteration_budget`, and `recovery_mode`.
6. Copy the selected normalized run into `<attempt_dir>/run_config.normalized.json`.
7. If source resolution ran, copy or reference `source_resolution.json` from `source/source_resolution.json` and include it as acquisition evidence. It is not recovery evidence for using the original repo.
8. Open and follow `plan-paper-skill-modules/SKILL.md`.
9. Extract or read the paper text. Write `paper_text.txt` when useful for auditability.
10. Produce:
   - `paper_profile.md`
   - `module_plan.json`
   - no more than five `modules/<module_id>.md` files
   Keep each internal `module_id` in snake_case. Give each deployable
   `skill_name` a unique canonical lowercase-hyphen id of at most 64 characters;
   it must also be the generated skill directory basename and frontmatter name.
11. Validate the module plan:

```bash
python <skills_root>/plan-paper-skill-modules/scripts/validate_module_plan.py \
  <attempt_dir>/module_plan.json \
  --modules-dir <attempt_dir>/modules
```

Do not perform heavyweight runtime probing, model cache scans, package installs, dataset downloads, or GPU setup before this modularization validation succeeds.

12. Open and follow `create-paper-module-skill/SKILL.md`.
13. For each module in `module_plan.json`, create or refine one generated skill under `<generated_skills_root>/<skill_name>/`.
    When module generation is decomposable, use the DisCo workflow tool or
    subagents in the same style as package/repo sub-skill extraction: one
    module agent per generated skill, each with the module id, exact output
    path, paper evidence, optional pre-recovery repo evidence, forbidden
    recovery sources, required scripts/tests, cross-module contracts, and
    acceptance rubric. Module agents must write files directly under
    `<generated_skills_root>` and return only concise handoff manifests.
    The main agent still owns integration and validation.
14. Each generated module skill must contain:
    - `SKILL.md`
    - `metadata.disco-role: operating` in its `SKILL.md` frontmatter
    - `scripts/` when deterministic behavior is useful
    - `tests/` or another deterministic smoke check for non-trivial behavior
    - At least one real assertion-backed test or smoke command that the validator attempts; do not satisfy this step with prose-only inspection.
15. Validate each generated skill and save the validation JSON:

```bash
python <skills_root>/create-paper-module-skill/scripts/validate_skill_tree.py \
  <generated_skills_root>/<skill_name> \
  --run-tests \
  > <attempt_dir>/generated_skills_validation/<module_id>.json
```

Generated tests must be compatible with the validator's simple runner when pytest is absent: plain test functions, standard-library fixtures, and no required `import pytest` unless pytest is explicitly installed by the skill. The saved validation JSON must report `ok: true`, `tests.attempted: true`, and no failing tests before the run can proceed to recovery.

Prompt-separation tests should assert absence of privileged-only markers, skill field names, hidden answers, and training-only sections from the student view. They should not forbid ordinary task words or environment object names that are visible in the task itself.

16. Open and follow `prepare-paper-recovery-env/SKILL.md`.
17. Write `environment/runtime_handoff.json` from bounded package, model/cache, GPU, benchmark, dataset, and active environment preparation. Do this after module skill validation and before recovery. Do not perform heavyweight runtime probing before modularization succeeds.
    Also write `environment/logs/command_log.json` with the subprocess commands run by environment preparation. If runtime constraints say isolated env only, create or reuse the private recovery env under `$DISCO_CODING_AGENT_DIR/envs/` or `~/.disco/agent/envs/` and set recovery to use that Python.
18. Open and follow `recover-paper-result/SKILL.md`.
19. Run a fast, meaningful recovery experiment using only allowed sources:
    - paper or extracted paper text
    - `paper_profile.md`
    - `module_plan.json`
    - `modules/*.md`
    - generated module skills
    - `environment/runtime_handoff.json`
    - datasets and general package documentation
    - web/search APIs only when required by the paper method
20. During recovery, do not read the original source repository.
21. Write:
    - `recovery/experiment_plan.md`
    - `recovery/source_manifest.json`
    - `recovery/recovery_result.json`
    - detailed logs under `recovery/logs/`
22. `recovery_result.json` must be produced by an executable experiment command, not hand-written as primary evidence. Save command, return code, elapsed time, and stdout/stderr tails under `recovery/logs/experiment_command_log.json`.
23. For reduced data-generation/training recoveries, write the main item as `recovery/logs/generated_data_item.json` and the primary training trace as `recovery/logs/training_trace.json`. The trace must include before/after loss or metric values and evidence that parameters or optimizer state changed. Use `params_before` and `params_after` for validator-compatible parameter snapshots; optional aliases such as `parameters_before` and `parameters_after` are fine but not a replacement.
24. Enforce `recovery_mode`: in `hard` mode, reduced/proxy/toy/fallback recovery may be logged only as diagnostics and must not be accepted as success; in `soft` mode, reduced/proxy recovery may be accepted only if it is explicitly declared, justified, executable, and passes validation.
25. Include mechanism checks for proxy recoveries and for any method whose core contribution is algorithmic rather than only metric output.
26. Exercise every generated core module that the recovery claims to validate, or explain why a module is not applicable. If a standalone generated loss, scoring, retrieval, or prompt-construction skill exists, call it or write a cross-check log instead of silently duplicating its logic inside the recovery harness. Save this evidence as `recovery/logs/generated_skill_invocations.json`.
27. Run the recovery experiment gate:

```bash
python <skills_root>/recover-paper-result/scripts/validate_recovery_experiment.py \
  <attempt_dir> \
  --output <attempt_dir>/recovery/experiment_validation.json
```

If this returns `ok: false`, fix the recovery artifacts or mark the run as refine/blocked. Do not accept a run with a failing experiment gate.
28. Open and follow `analyze-paper-recovery/SKILL.md`.
29. Write:
    - `analysis/analysis_report.json`
    - `analysis/feedback.md`
30. If the analysis decision is `refine`, update the relevant module docs, generated skills, tests, runtime handoff usage, and recovery harness. Then rerun skill validation, environment preparation, recovery, and analysis within the configured refinement budget.
31. Stop only when the analysis decision is `accept`, the configured refinement budget is exhausted with clear artifacts, or a concrete blocker is recorded.
32. Run final validation, then write the organized final report:

```bash
python <skills_root>/paper-skills-distiller/scripts/validate_distillation_run.py \
  <attempt_dir> \
  --stage analyzed \
  --output <attempt_dir>/final_validation.json

python <skills_root>/paper-skills-distiller/scripts/write_final_report.py \
  <attempt_dir> \
  --language-preference "<language_preference>"

python <skills_root>/paper-skills-distiller/scripts/validate_distillation_run.py \
  <attempt_dir> \
  --stage reported
```
33. When the run is accepted and the reported stage passes, assess the whole
    generated module graph's reuse. Choose project scope at
    `<project-dir>/.agents/skills/` for task/project/private-data/evaluator/
    benchmark/environment-bound output and whenever broader reuse is uncertain.
    Choose managed scope at `~/.disco/agent/skills/` only for a self-contained,
    provenance-backed graph that is independent of transient run state, verified
    on representative uses, and expected to apply across projects or research
    tasks. Use the Creator session working directory as `<project-dir>` unless
    the user explicitly selected another project, and keep every module in one
    scope.
34. Show the reuse evidence, exact graph revision, scope, every destination,
    entry skill, validation results, unresolved limits, collisions, and shadowing
    impact. Obtain approval for that import; overwrite always needs separate
    approval.
35. After approval, resolve the visible `distill-ml-knowledge` directory and call
    its importer once with all top-level module skill roots:

```bash
node <distill-ml-knowledge-root>/scripts/import_operating_skill_graph.mjs \
  --scope project \
  --project-dir <project-dir> \
  <generated-skill-root> [<generated-skill-root> ...]
```

or:

```bash
node <distill-ml-knowledge-root>/scripts/import_operating_skill_graph.mjs \
  --scope managed \
  --agent-dir ~/.disco/agent \
  <generated-skill-root> [<generated-skill-root> ...]
```

    Do not import distillation, recovery, analysis, test, or report artifacts.
36. Write `<attempt_dir>/researcher-handoff.md` with the task, paper
    source/version, reusability rationale, selected scope, exact imported paths,
    module ids, graph entry point, recovery/validation evidence, and unresolved
    limits. Suggest `/researcher` after import. If import is declined, state that
    the graph remains staged and do not claim the live paths exist.

## Required Distillation Artifacts

A complete analyzed distillation directory must contain:

```text
run_manifest.json
run_config.normalized.json
paper_text.txt
paper_profile.md
module_plan.json
modules/
generated_skills_validation/
environment/
  runtime_handoff.json
  logs/
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

`paper_text.txt` is expected for formal runs. If it is omitted, explain why in `reports/final/final_report.md`.

Run final validation:

```bash
python <skills_root>/paper-skills-distiller/scripts/validate_distillation_run.py \
  <attempt_dir> \
  --stage analyzed \
  --output <attempt_dir>/final_validation.json
```

The final response to the user must report whether final validation and the `reported` stage returned `ok: true`, point to `reports/final/final_report.md`, and report the operating graph's project/managed/staged deployment status plus its handoff path.

## Source Boundary Rules

- The original source repository is allowed only during modularization and create-paper-module-skill creation.
- The original source repository is forbidden during recovery.
- A source repo cloned from `original_repo_source` is still the original source repository. It remains forbidden during recovery even if it was downloaded by `resolve_sources.py`.
- Paper acquisition artifacts such as `source_resolution.json` may be used for provenance. They do not make the original repo an allowed recovery source.
- `recovery/source_manifest.json` must list every path, URL, dataset, model, package environment, and generated skill used during recovery.
- `recovery/source_manifest.json` must include `environment/runtime_handoff.json` when the environment stage ran.
- `environment/logs/command_log.json` must record environment preparation commands, including failed or timed-out clone/install/probe commands.
- If any original repo path appears in the recovery source manifest, the recovery is invalid and analysis must return `refine`.
- Do not copy original repo code into generated skills unless the user explicitly asks for repo-specific tooling. The default goal is transferable paper insight.
- Do not use previous run generated data items, prompts, outputs, training logs, or recovery results as evidence for the current recovery.
- If a fresh benchmark or dataset fetch is blocked and a local checkout from another run or workspace path is reused, record it as a fallback benchmark source: include the fresh-fetch command and blocker, reused path, commit/version if available, exact resource files used, and a snapshot or copy of those files inside the current distillation directory.

## Runtime Rules

- Prefer the user's requested runtime when supplied.
- If a model path, GPU id list, environment path, or search endpoint is supplied, record whether it was used.
- Use `prepare-paper-recovery-env` to produce `environment/runtime_handoff.json` before recovery. `recover-paper-result` should consume that handoff rather than repeating expensive discovery.
- Do not mutate shared environments unless the user explicitly permits it.
- If package changes are needed, create/reuse a separate private recovery environment under `$DISCO_CODING_AGENT_DIR/envs/` or `~/.disco/agent/envs/` and record its path. Missing packages, model caches, datasets, or required credentials are setup work to attempt before marking the run blocked.
- Do not silently replace a required runtime with a smaller model, deterministic fallback, or subset proxy.
- If fallback is necessary, record it as a limitation and ask the user before treating it as acceptance evidence unless the user pre-authorized fallback.
- In `hard` mode, do not treat reduced data, proxy metrics, smaller models, toy harnesses, or deterministic fallbacks as acceptance evidence even if the user allowed them for diagnostics. Final validation should fail rather than marking the run accepted.
- In `soft` mode, reduced or proxy recovery may count only after it passes the recovery experiment gate and records why full recovery was blocked.
- Keep runtime discovery bounded: search only user-supplied paths, the workspace, and known cache roots; do not run broad recursive scans over `/share/project` or other NFS roots.
- Put timeouts around package installs, model downloads, network probes, and benchmark setup commands. If a command stalls, stop it, record the blocker, and continue only with an honest reduced recovery.
- For reduced data-generation/training runs, at least one data item must be built and at least one real training or optimizer step must run when the required runtime is available. If only a scalar or fake-model fallback runs, mark it as a fallback and do not count it as requested training.
- If the user explicitly permits a reduced run and the required model stack is unavailable, a tiny parameterized student may be trained with available local packages or the Python standard library. This is acceptable only as `reduced_training_executed`: it must consume the constructed data item, compute the paper-inspired loss or closest faithful proxy, update parameters, and log before/after loss and parameter values. Keep full-stack and required-model success booleans false; set `optimizer_step_executed` true only when trainable parameters or optimizer state actually changed.
- When benchmark code or data is obtained, the recovery item should record resource-file provenance and derive at least one field from those files when feasible. If only benchmark-style construction is possible, label it explicitly and explain the limitation.
- Reduced training logs should use stable names: `recovery/logs/generated_data_item.json` for the data item and `recovery/logs/training_trace.json` for the primary before/after training trace.

## Recovery Target Rules

The recovery target in `module_plan.json.fast_recovery_target` must include:

```json
{
  "dataset": "dataset name",
  "split": "split or subset",
  "metric": "metric name",
  "paper_value": 0.0,
  "proxy": true,
  "rationale": "why this target is the fastest faithful recovery"
}
```

Use an object for `paper_value` when the paper target has multiple metrics.

`recovery/recovery_result.json.paper_target` must match `module_plan.json.fast_recovery_target`. Do not hard-code a different target in the recovery harness.

## Quality Bar

Generated skills are acceptable only if:

- The paper's main method and evaluation pathway are covered by no more than five modules.
- Each generated skill has clear trigger frontmatter, input/output contracts, workflow, limitations, and validation guidance.
- Each generated skill declares `metadata.disco-role: operating` in frontmatter.
- Deterministic scripts have deterministic tests.
- Future agents can use the skills without rereading the original repository.
- Recovery exercises the generated skills rather than a hand-written one-off solution.
- Recovery has numeric metrics or clearly recorded failure artifacts.
- Proxy recovery includes explicit mechanism checks that demonstrate the paper mechanism ran.
- Analysis explains metric gaps and gives module-level feedback when refinement is needed.

## Final Response Requirements

In the final user-facing response:

- State the distillation directory.
- State the generated skills root.
- List generated module skills.
- State recovery target and metric result.
- State analysis decision.
- State final validation result.
- State the reusability classification, approved project/managed scope or staged-only status, exact imported paths when applicable, and `researcher-handoff.md` path.
- Mention any blockers, fallbacks, or deviations from the requested runtime.
- Keep the response in the user's preferred language.
