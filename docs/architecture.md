# Architecture

AREX-Skill separates the published skill library from the DisCo runtime
that routes, uses, creates, and maintains it.

## Current Repository Snapshot

```text
AREX-Skill/
  README.md
  README.zh-CN.md
  CONTRIBUTING.md
  CONTRIBUTING_CN.md
  docs/
  skills/
    README.md
    repositories/
      repo-skills/
      repo-skills-router/
  scripts/
  cli/
```

The current checkout contains both the published skill library and the DisCo
TypeScript source tree. The broader library boundary is
`skills/`; this checkout currently publishes its repository
skill collection under `skills/repositories/repo-skills/` and a sibling
`skills/repositories/repo-skills-router/`. The single source of truth for
bundled and portable DisCo workflows lives under
`cli/packages/coding-agent/src/disco/skills/`.

## Source Layout

The DisCo source tree lives at `cli/`:

```text
cli/
  package.json
  npm-shrinkwrap.json
  docs/
  examples/
  scripts/
  packages/
    coding-agent/
      UPSTREAM_SOURCE.md
      UPSTREAM_MANIFEST.json
      src/
      test/
```

Source-tree roles:

| Path | Role |
| --- | --- |
| `cli/package.json` | The only publishable npm package, `@auto-ml-skills/disco`, exposing the `disco` CLI and SDK. |
| `cli/packages/coding-agent/src` | DisCo's copied and modified Pi coding-agent runtime, including interactive/print modes, project trust, sessions, tools, skill discovery, workflow skills, and dynamic orchestration. |
| `cli/packages/coding-agent/test` | Upstream-derived tests and DisCo regression contracts. |
| `cli/docs` and `cli/examples` | Documentation and examples shipped in the npm package. |
| `cli/scripts` | Asset copying, upstream provenance verification, and package-content verification. |

`cli/package.json` is public and versioned as the standalone package. The
`cli/packages/coding-agent/` directory is a provenance-bearing source subtree,
not a nested npm workspace. DisCo does not depend on
`@earendil-works/pi-coding-agent`; it owns the copied coding-agent runtime and
uses pinned `@earendil-works/pi-agent-core`, `@earendil-works/pi-ai`, and
`@earendil-works/pi-tui` packages as normal dependencies. This keeps a user's
separately installed Pi CLI and global packages outside DisCo's dependency and
resource-discovery boundaries.

## Runtime Task Execution

DisCo is a research-first agent, not only a skill authoring tool. It uses the
existing agent loop, file and command tools, software implementation, and
experiments to complete research goals end to end. It also handles standalone
software requests with the same execution loop. Researcher is the default
session role; Creator is an explicit construction role.

Runtime skill discovery includes:

- DisCo-managed user skills under `~/.disco/agent/skills/`;
- shared user skills under `~/.agents/skills/`;
- project resources under `<project>/.disco/skills/` and project or ancestor
  `.agents/skills/` directories after project trust is granted;
- skills from installed npm, git, HTTPS/SSH, or local packages;
- bundled DisCo workflow skills.

The managed library can contain hundreds of repo skills without filling the
initial model context. Repo-skill roots use
`disable-model-invocation: true`, so they remain registered for explicit
`/skill:<name>` invocation but are omitted from the model-visible skill list.
The startup `Skills` section reports this model-visible set rather than every
registered skill; explicit skill command completion still uses the full set.
The `repo-skills-router` is model-visible by default and provides area-family
progressive disclosure:

1. Read the router and choose one or two likely taxonomy areas.
2. Read only the relevant area pages, then compare the matching family pages.
3. Resolve the selected repository skill at
   `../repo-skills/<skill-id>/SKILL.md`.
4. Read only the necessary sub-skills, references, or scripts.
5. Execute and verify the task against the current checkout and environment.

The live router in `~/.disco/agent/skills/repositories/repo-skills-router/` takes precedence
over the bundled fallback template. Its repository collection is the sibling
`~/.disco/agent/skills/repositories/repo-skills/`; the updater never scans Creator meta skills
or unrelated user skills. Selected guidance is checked against its provenance,
current source, installed version, and actual command results.

`disco repo-skills install` and `disco repo-skills update` manage the official
collection by skill ID. The manager records the official commit and digests in
`~/.disco/agent/repo-skills-library.json`, keeps a shallow source cache under the
DisCo agent directory, verifies that cache's stored origin before fetching, and
preserves Creator/user skill IDs that are not owned by the official manifest.
`status` checks managed digests plus router presence and live skill coverage
without network access. Source preparation happens before the shared repo import
lock; live state is re-read under that lock before a staged router and skill tree
are swapped with rollback support.

`disco repo-skills router disable` adds
`disable-model-invocation: true` only to the live router. This removes it from
automatic model selection while keeping `/skill:repo-skills-router` available.
The router updater preserves that live policy across individual imports and
full collection updates. Canonical library output and routers exported to other
agents remain model-visible by default.

### Creator and Researcher Boundaries

Each DisCo session has exactly one role. Creator loads skills marked
`metadata.disco-role: meta` and explicitly cross-mode `shared` utilities,
including `distill-ml-knowledge`,
`design-meta-skill`, and the repository and paper construction workflows.
Researcher loads `operating` skills and `shared` utilities, including the
router, imported repository graphs, and task-related operating skills. A
skill with no role metadata is treated as a user/third-party operating skill and
is available only in Researcher; an explicitly invalid role is excluded from
both roles. Role filtering occurs before name collisions, command registration,
and prompt construction. Shared visibility does not relax either mode's task
boundary; bundled construction and generated operating artifacts remain
strictly `meta` and `operating`, respectively.

Creator starts with `distill-ml-knowledge`. It owns the canonical task and
construction vocabulary, assesses visible workflows and bounded compositions,
and selects `direct`, `reuse-existing`, or `design-reusable`. Only an
evidence-backed recurring construction gap enters `design-meta-skill`, which
consumes the exact routing handoff rather than repeating adequacy or path
selection. The entry point records only a lightweight routing contract before
selection; the chosen direct or reusable-bundle branch owns its exact
construction specification. An approved new meta skill is reusable Creator
infrastructure and is installed at
`~/.disco/agent/skills/<meta-skill-id>/`. The operating graph it later produces
has a separate reuse assessment, destination proposal, and approval. It is
consumed only in a new Researcher session.

`/creator` and `/researcher` are interactive context boundaries. A confirmed
cross-role switch persists the old session, creates a clean session, rebuilds
the prompts and role-filtered registry, and leaves the old trajectory available
through `/resume`. `/export` exports only the current session; it never merges
messages from the previous role. Non-interactive and RPC clients select the
initial role with `--agent-mode creator|researcher`, independently of
`--mode text|json|rpc`. A request that belongs to the other role is rejected
before execution, with an explicit suggestion to switch; DisCo never changes
roles implicitly.

Additional skill packages use DisCo's package manager. A package may declare
resources under a `disco` manifest key, use a legacy `pi` key, or rely on
conventional `skills/`, `extensions/`, `prompts/`, and `themes/` directories.
`disco install <source>` persists the package so its enabled resources are
discovered on later runs.

`disco install <source> --for creator|researcher|both` persists one package
installation with mode-scoped activation for all four resource types;
`--for default` removes that installer override. The package policy takes
precedence over skill frontmatter and maps package skills to effective
`meta`/`operating`/`shared` roles. Package resolution itself stays mode-neutral
for `disco config`; the resource loader filters activation before extension
execution, skill collisions, and prompt/theme loading.

## Skill Authoring Pipeline

DisCo currently bundles specialized package/repo and paper construction
workflows. `distill-ml-knowledge` is the canonical Creator entry point that
normalizes a task, assesses single-workflow and composed coverage, and selects
`direct`, `reuse-existing`, or `design-reusable`. `design-meta-skill` consumes
the verified recurring-gap handoff and designs the reusable bundle; it does not
reclassify the request. Their source is under
`cli/packages/coding-agent/src/disco/skills/`.

### Package/Repo Flow

At a high level, DisCo's repo-skill pipeline is:

1. In Creator mode, start with `distill-ml-knowledge` to assess whether the
   request should take `direct`, `reuse-existing`, or `design-reusable`.
2. Classify the source as package/repository, paper, or a task-specific gap.
3. Analyze source structure and confirm scope.
4. Prepare a minimal inspection environment.
5. Gather evidence from source, docs, examples, tests, metadata, and live
   package inspection.
6. Plan a top-level skill and sub-skill structure.
7. Generate and integrate self-contained runtime guidance.
8. Run the built-in verification workflow.
9. Import an approved repo graph under
   `~/.disco/agent/skills/repositories/repo-skills/<skill-id>/`.
10. Classify the verified repository against the fixed area-family taxonomy,
    write the external routing decision plus minimal v2 metadata, and rebuild
    the affected area/family router views under the import lock.

The create flow does not treat verification as optional cleanup.
`create-repo-skill` hands the integrated draft to `verify-repo-skill` before a
skill is ready to import or publish.

### Verification Gate

`verify-repo-skill` owns the final quality gate for created, refreshed, or
extended repo skills. It writes check-only artifacts outside the runtime skill
directory, normally under:

```text
<repository>/skills/tests/<skill-id>/
  test-cases/
  reports/
```

The verification stage covers:

- assertion-backed usability case generation;
- content-level self-refine against the selected source scope and generated
  skill tree;
- representative native repo example/test checks when they are safe and
  available;
- static quality gates for links, self-containment, provenance, routing
  metadata, local-path leaks, and frontmatter shape;
- final coverage, review, publication, and handoff reports;
- import readiness and, when approved or auto-authorized, locked import into
  DisCo's managed repository collection.

Runtime skill directories should not contain usability cases, eval notes,
verification reports, human-review notes, publication checklists, or prompt
samples. Those belong under the review/test artifact directory.

### Paper Flow

The paper-to-skill flow generates and validates reusable skills for paper
replication. It is a Creator workflow selected from the visible task
description. The current source tree includes:

```text
cli/packages/coding-agent/src/disco/skills/
  create-paper-skills/
  paper-skills-distiller/
  plan-paper-skill-modules/
  create-paper-module-skill/
  prepare-paper-recovery-env/
  recover-paper-result/
  analyze-paper-recovery/
```

The flow resolves a paper source, optionally uses an implementation repository
as pre-recovery evidence, modularizes the paper, creates and validates
module-level skills for paper replication, prepares bounded runtime evidence,
runs a recovery experiment without reading the original implementation repo,
analyzes gaps, refines within the configured `iteration_budget` when needed,
and writes attempt artifacts plus final reports. The default repeated-run input
is a TOML run config based on the bundled
`distiller-run-config-template.toml`. Batch configs are normalized to JSON
under a workspace-level `paper2skills_runs/` area, then each selected paper/run
gets its own run root, source acquisition record, generated-skills root, and
attempt directory.

Run config normalization records fields such as `paper_slug`, `paper_source`,
`original_repo_source`, `repo_discovery_mode`, `recovery_target`,
`recovery_mode`, `runtime_constraints`, `iteration_budget`, and
`generated_skills_root`. New runs default to `recovery_mode: hard` and
`iteration_budget: 10`; `hard` mode does not accept reduced, proxy, toy,
smaller-model, or fallback recovery as success, while `soft` mode may accept a
declared proxy only when executable evidence and mechanism checks pass.

The run root also records source acquisition when needed, normally at
`source/source_resolution.json`. Each paper attempt follows a contract shaped
like:

```text
run_manifest.json
run_config.normalized.json   # preferred when a config was used
paper_profile.md
module_plan.json
modules/
generated_skills_validation/
reports/
  generated-skills/
  verification/
  final/
    final_report.md
    final_report.json
environment/
  runtime_handoff.json
  logs/command_log.json
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
```

Paper recovery has a stricter source boundary than modularization: the optional
implementation repository may inform module planning and module-skill creation,
but recovery must use only the paper, module docs, generated skills, runtime
handoff, data, and general package documentation. The recovery result must be
backed by executable command logs, and the attempt must prove that generated
module skills were called, imported, or cross-checked rather than bypassed by a
one-off handwritten recovery script.

After an accepted run passes final validation, Creator classifies the complete
module graph for project or managed deployment, proposes every live target, and
imports only after approval. Every module stays in the same scope. The workflow
then writes `researcher-handoff.md`; the generated `skills/` directory remains
staging and review input rather than becoming live automatically.

### Bundled Workflow Skills

The package/repo workflow skills include:

| Workflow Skill | Role |
| --- | --- |
| `prepare-repo-skill-env` | Create or verify a scoped Python inspection environment after extraction scope is known. |
| `create-repo-skill` | Analyze source evidence, plan and generate the runtime skill, then hand off to verification. |
| `verify-repo-skill` | Own assertion-backed usability cases, content self-refine, native checks, static gates, reports, and import readiness. |
| `refresh-repo-skill` | Update an existing repo skill against changed upstream source, then verify. |
| `extend-repo-skill` | Add deeper coverage to an existing skill, then verify. |
| `import-repo-skills-to-agent` | Export DisCo-managed skills and a scoped router into Codex, Claude Code, or another agent target. |

`repo-skills-router` is bundled beside these meta skills but is not a Creator
workflow. It is an `operating` skill that provides Researcher's progressive
routing entry point.

The paper workflow skills include:

| Workflow Skill | Role |
| --- | --- |
| `create-paper-skills` | Entry point for generating and validating paper-replication skills in Creator mode. |
| `paper-skills-distiller` | Orchestrate source resolution, modularization, paper-replication skill creation, recovery, analysis, refinement, and final reports. |
| `plan-paper-skill-modules` | Create paper profile, module plan, and module docs. |
| `create-paper-module-skill` | Convert module docs into generated module skills and validation checks. |
| `prepare-paper-recovery-env` | Record bounded package, model, GPU, dataset, command-log, and runtime handoff evidence. |
| `recover-paper-result` | Run a bounded recovery experiment using generated skills and save executable command plus generated-skill invocation evidence. |
| `analyze-paper-recovery` | Compare recovery evidence against the paper target, experiment gate, source boundary, and mechanism checks, then return accept/refine feedback. |

## Runtime Skill Shape

The runtime skill shape follows progressive disclosure:

```text
SKILL.md                         # first file an agent reads
references/                      # supporting evidence and longer notes
sub-skills/<area>/SKILL.md       # deeper task-specific guidance
scripts/                         # small helpers for checks/preflight
```

`SKILL.md` should be useful on its own and route deeper only when the task needs
more detail. References and scripts should be linked from the skill text when
they are expected to be used.

Generated repo skills are expected to include:

- `references/repo-provenance.md` with source commit, package version, dirty
  state, and evidence paths;
- `references/repo-routing-metadata.json` for managed router placement;
- `disable-model-invocation: true` in repo-skill root and sub-skill frontmatter
  so compatible agents keep bulk repo skills behind the routing entry point;
- an enabled canonical/export router, while a DisCo live router follows the
  user's `repo-skills router enable|disable` policy;
- bundled references or scripts instead of links to the original checkout when
  future use depends on those details.

## Router

The repo-skills router is a generated area-family index for the published
repository skill library:

```text
skills/
  repositories/
    repo-skills/
      <repo-skill-id>/
    repo-skills-router/
      SKILL.md
      references/
        areas/
        families/
        index/
        maintenance.md
```

It is not a replacement for individual skills. It gives the first-pass
selection map, then points agents from an exact family page to candidate
repository skill roots.

## Deployment Scopes And Managed Library

A newly designed meta skill and the operating graph it later constructs have
separate deployment decisions. After validation and explicit approval, the
meta skill itself always uses the managed Creator location:

```text
~/.disco/agent/skills/<meta-skill-id>/
```

An ordinary operating graph uses exactly one of these live scopes:

| Scope | Location | Selection rule |
| --- | --- | --- |
| Project | `<project-dir>/.agents/skills/<skill-id>/` | Use for output tied to one task, checkout, private dataset, evaluator, benchmark instance, convention, or environment. Uncertain reuse defaults here. The project must be trusted before Researcher loads it. |
| Managed | `~/.disco/agent/skills/<skill-id>/` | Use only for self-contained, provenance-backed output that is independent of transient task state, verified on representative uses, and expected to work across projects or research tasks. |

All roots and sub-skills in one graph stay in the same scope. Creator presents
the reuse evidence, exact targets, entry point, verification results,
unresolved gaps, collisions, overwrite status, and shadowing impact before
import. The generic graph importer installs all roots in one locked transaction
and rolls back the graph on failure; overwrite always requires separate
approval.

Repository graphs are a high-reuse managed special case. They do not use the
generic importer and retain this canonical layout:

```text
~/.disco/agent/skills/
  <meta-skill>/               # Creator only
  <reusable-operating-skill>/ # Researcher only
  repositories/
    repo-skills/
      <repo-skill-id>/
    repo-skills-router/
```

The repository import transaction copies the runtime graph, validates
`references/repo-routing-metadata.json`, and rebuilds the sibling router while
holding the shared import lock. Router updates are generated from structured
metadata, not hand-edited as free-form Markdown during import. DisCo discovers
the managed root automatically, keeps hidden repo skills out of the initial
context, and uses its live router for progressive selection when enabled or
when explicitly invoked while disabled. Use
`import-repo-skills-to-agent` only when exporting managed skills and a scoped
router into another runtime such as `~/.agents/skills/`, `~/.claude/skills/`, or
an explicitly selected legacy `~/.codex/skills/`.

When exporting to Codex, the import workflow also adds target-side
`agents/openai.yaml` files with `policy.allow_implicit_invocation: false` to
non-router repo skills, because Codex does not use the
`disable-model-invocation` frontmatter field for that policy.

## Source Of Truth

Use these source-of-truth rules:

- The broader library lives under `skills/`; repository skills
  are the `skills/repositories/repo-skills/` collection and the router is
  its sibling `skills/repositories/repo-skills-router/`.
- Bundled and portable external-agent workflow skills have one source of truth:
  `cli/packages/coding-agent/src/disco/skills/`.
- Edit workflow skills in that source directory, then rebuild DisCo. Do not
  maintain a second hand-synchronized mirror.
- Verification and review artifacts live outside runtime skill directories,
  normally under `skills/tests/<skill-id>/` in the inspected repository.
- Project-bound or uncertain operating graphs are deployed under a trusted
  project's `.agents/skills/`; only evidence-backed reusable graphs belong at
  the top level of `~/.disco/agent/skills/`. Repository graphs keep their
  dedicated nested collection and sibling router.
- Do not hand-edit generated `dist/` resources as the source of truth.
- Keep docs explicit about whether a feature belongs to the runtime skill
  library, bundled workflow source, or DisCo CLI runtime.
