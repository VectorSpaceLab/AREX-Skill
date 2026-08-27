---
name: create-paper-skills
description: "Creates reusable Agent Skills from an AI research paper using the Paper2Skills Distiller workflow. Use in Creator mode when the user provides a paper PDF, paper URL, arXiv id, paper title, or paper/repo pair, or asks to convert a scientific paper into skills with recovery experiments. Prefer a TOML run config; ask for missing paper, repo, recovery, runtime, and budget fields before expensive work."
metadata:
  disco-role: meta
---

# Create Paper Skills

## Purpose

Use this skill as the DisCo entry point for paper-to-skill construction in
Creator mode. It wraps the Paper2Skills Distiller workflow in the same peer
role that `create-repo-skill` plays for repository/package construction: collect
the input contract, route to the correct workflow skills, validate artifacts,
run at least a meaningful recovery smoke experiment when allowed, and produce
reusable module-level skills.

Prefer a filled TOML config over free-form prompt fields. The reusable template
is bundled at `assets/distiller-run-config-template.toml`; a longer reusable
agent prompt is bundled at `assets/standard-distiller-run-prompt.md`.

## Workflow Classification

- When the primary knowledge source is a software repository or package, use
  `create-repo-skill` instead.
- When the primary knowledge source is a paper, use this skill and then load
  `paper-skills-distiller`.
- If the user provides both a paper and an implementation repository, treat the
  repository as pre-recovery evidence only. Recovery must not read it.
- If the workflow classification is ambiguous and both repository and paper
  flows are plausible, ask one concise clarification before starting.

## Required Input Contract

Before source downloads, environment setup, or recovery, identify these fields
from the prompt or config. Ask only for values that cannot be inferred safely:

- `config_path`: preferred path to a filled TOML config.
- `workspace_root`: workspace that will contain distillation and generated-skill
  outputs.
- `paper_source`: local PDF/text path, direct PDF URL, arXiv URL/id, or paper
  title.
- `paper_slug`: stable snake_case id for this paper/version.
- `original_repo_source`: local repo path, Git URL, `none`, or `unknown`.
- `source_acquisition`: whether remote paper/repo sources may be
  downloaded/cloned and whether title top hits may be selected automatically.
- `repo_discovery_mode`: `ask`, `auto`, or `disabled` when
  `original_repo_source` is `unknown`. Default is `ask`.
- `generated_skills_root`: output root for generated module skills.
- `attempt_dir` or permission to use the default distillation directory:
  `<workspace_root>/<paper_slug>/distillation`.
- `recovery_target`: dataset, split, metric, target value, and whether the
  agent should propose the fastest faithful target first.
- `recovery_mode`: `hard` or `soft`; default is `hard`.
- `runtime_constraints`: model path, environment path, GPU ids, network/API
  setup, and environment mutation rules.
- `iteration_budget`: maximum refine cycles after the first recovery. Default
  is `10`; the user may set any non-negative integer.
- `language_preference`: language for final user summaries. Generated skill
  artifacts stay in English.

If no `config_path` is supplied, create or request one based on
`assets/distiller-run-config-template.toml` when the run is more than a quick
one-off. For batch work, require a TOML config with one `[[runs]]` entry per
paper.

## Clarification Triggers

Ask before proceeding when:

- The paper title or URL resolves to multiple plausible papers.
- `original_repo_source` is `unknown`, `repo_discovery_mode` is `ask`, and the
  next step would search for an implementation repo.
- Repo discovery returns multiple plausible candidates or the selected top
  candidate is not clearly tied to the paper.
- The recovery target is unspecified and the next step would launch an
  expensive recovery; read the paper first, propose the fastest faithful target,
  and ask for confirmation.
- Recovery mode is omitted and the user request implies reduced/proxy success
  might be acceptable; otherwise default to `hard`.
- Runtime setup might mutate a shared conda/virtualenv environment.
- The distillation directory already exists and repairing/resuming could overwrite
  evidence.

## Required Workflow

Use the agent's todo/task-list mechanism for visibility. If workflow or
subagent facilities are available, use them only where they help parallelize
module skill generation or review; ordinary sequential Distiller stages do not
require workflow orchestration.

1. Load this skill and, for detailed rules, load
   `../paper-skills-distiller/SKILL.md`.
2. Validate the user input. If `config_path` exists, run:

```bash
python <skills_root>/paper-skills-distiller/scripts/read_run_config.py \
  <config_path> \
  --output <workspace_root>/distiller_run_config.normalized.json
```

For one run in a batch, also write a selected normalized run JSON with
`--slug <paper_slug> --run-only`.

3. Resolve remote or title-based sources before distillation initialization. Prefer
   `../paper-skills-distiller/scripts/resolve_sources.py` for local paths,
   direct URLs, arXiv ids/URLs, arXiv title search, Git repo URLs, and bounded
   GitHub repo discovery when `repo_discovery_mode=auto`. Record acquisition
   evidence, candidates, selected URLs, clone commands, and blockers.
4. Initialize the distillation directory with
   `../paper-skills-distiller/scripts/init_run.py`, preserving
   `iteration_budget`, `recovery_mode`, `generated_skills_root`, resolved
   `paper_path`, optional resolved `original_repo_path`, and selected
   normalized run config.
5. Load `../plan-paper-skill-modules/SKILL.md`. Extract/read the paper, create
   `paper_profile.md`, `module_plan.json`, and no more than five module
   documents under `modules/`.
6. Validate modularization with
   `../plan-paper-skill-modules/scripts/validate_module_plan.py`. Do not perform
   heavyweight model, package, dataset, or GPU probing before this succeeds.
7. Load `../create-paper-module-skill/SKILL.md`. Convert each module document into a
   generated skill under `generated_skills_root`.
8. Validate every generated module skill with
   `../create-paper-module-skill/scripts/validate_skill_tree.py --run-tests` and save a
   JSON log under `generated_skills_validation/`.
9. Load `../prepare-paper-recovery-env/SKILL.md`. Create
   `environment/runtime_handoff.json` and
   `environment/logs/command_log.json` from bounded runtime probes and active
   setup. When packages, model cache, datasets, or benchmark files are missing,
   use the prepare-env isolated environment/data acquisition path before
   deciding the stage is blocked.
10. Load `../recover-paper-result/SKILL.md`. Run the strongest feasible fast recovery
    experiment allowed by `recovery_mode` and `runtime_constraints`, using only
    allowed recovery sources. The recovery must exercise generated skills and
    save executable command evidence.
11. Run the recovery experiment validator and save
    `recovery/experiment_validation.json`.
12. Load `../analyze-paper-recovery/SKILL.md`. Write `analysis/analysis_report.json` and
    `analysis/feedback.md`.
13. If analysis returns `refine`, update the relevant module docs, generated
    skills, tests, runtime handoff usage, and recovery harness, then rerun
    validation, recovery, and analysis until accepted or the configured
    `iteration_budget` is exhausted.
14. Run the final Distiller artifact validator and save `final_validation.json`.
15. Write the organized final report with
    `../paper-skills-distiller/scripts/write_final_report.py`, then validate
    the `reported` stage. Final reports belong under
    `<attempt_dir>/reports/final/`, not in the generated skill directory or a
    top-level `Distiller` directory.
16. If the run is accepted and the generated operating graph passes final
    validation, assess the graph's reuse as a separate deployment decision.
    Select project scope at `<project-dir>/.agents/skills/` when the modules are
    tied to this task, project layout, private data, evaluator, benchmark
    instance, or runtime; also select project when cross-project reuse remains
    uncertain. Select managed scope at `~/.disco/agent/skills/` only when the
    complete module graph is self-contained, source/version/provenance backed,
    independent of transient run state, verified on representative uses, and
    expected to apply across projects or research tasks. Use the Creator
    session's working directory as `<project-dir>` unless the user explicitly
    selected another project. Keep all module skills in one scope.
17. Present the reusability rationale, exact generated graph revision, selected
    scope, all destination paths, entry skill, final validation evidence,
    unresolved limits, collisions, and shadowing impact. Ask for approval of
    that exact import. Any overwrite requires separate approval.
18. After approval, resolve `distill-ml-knowledge` from the visible skill registry
    and run its `scripts/import_operating_skill_graph.mjs` once with every
    generated module skill root. Use `--scope project --project-dir
    <project-dir>` or `--scope managed --agent-dir ~/.disco/agent` as approved.
    Do not copy distillation, recovery, analysis, test, or report artifacts.
19. Write `researcher-handoff.md` under the distillation directory with the task,
    paper source/version, reuse rationale, selected scope, exact imported paths,
    module skill ids, graph entry point, recovery and validation evidence, and
    unresolved limits. Suggest `/researcher` only after import, or clearly state
    that the skills remain staged when the user declines it.

## Recovery Discipline

- `hard` mode must not accept proxy, toy, reduced, fallback, cache-only, or
  smaller-model recovery as success.
- `soft` mode may accept reduced/proxy recovery only when it is explicit,
  justified, executable, mechanism-checked, and validator-approved.
- Recovery must not read the original implementation repo. Use the paper,
  module docs, generated module skills, runtime handoff, datasets, and general
  public package documentation only.
- Do not report `blocked` merely because the active Python lacks packages
  (`torch`, `transformers`, `vllm`, `nltk`, etc.), because no local model cache
  exists, or because a dataset is absent locally. First run the allowed
  preparation steps: create/reuse an isolated environment under
  `$DISCO_CODING_AGENT_DIR/envs/` or `~/.disco/agent/envs/`, install the
  smallest required packages with timeouts, attempt permitted bounded model or
  dataset acquisition, and ask for missing credentials/permissions when they
  are truly required.
- If a user permits temporary simplification for this run, still create at
  least one data item, run at least one real training/inference/evaluation
  command when the paper task involves runtime behavior, and save the trace.
- Do not mark a run complete based on hand-written JSON artifacts alone. The
  primary recovery result must come from an executable command log.

## Output Contract

By the end, the user should have:

- A normalized run config or explicit record of prompt-derived fields.
- One distillation directory with the Distiller artifact contract.
- English module-level generated skills under `generated_skills_root`.
- Validation logs for module plan, generated skills, recovery experiment, and
  final distillation contract.
- `reports/final/final_report.md` and `reports/final/final_report.json`,
  alongside any verification or generated-skill review reports under
  `reports/`.
- An operating-graph reusability decision, approved project/managed import result
  when requested, and `researcher-handoff.md` with exact live paths.
- A final summary in the requested language explaining accepted status,
  blockers, recovery evidence, generated skill paths, and remaining gaps.
