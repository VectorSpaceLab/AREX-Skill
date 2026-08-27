# DisCo Skills

This directory is the single source of truth for DisCo's bundled workflow
skills and the `repo-skills-router` template. DisCo discovers this corpus at
startup, then exposes only the skills owned by the current Creator or Researcher
session.

## Mode Ownership

Every bundled `SKILL.md` declares one strict role:

```yaml
metadata:
  disco-role: meta # Creator only
```

or:

```yaml
metadata:
  disco-role: operating # Researcher only
```

Creator owns all construction workflows in this directory. Researcher owns the
bundled/live `repo-skills-router` and the repo or task skills produced by those
workflows. Mode filtering removes an ineligible skill from both the system
prompt and `/skill:*` commands; `disable-model-invocation` only controls prompt
visibility after that filter.

`distill-ml-knowledge` is the Creator bootstrap workflow and owner of the shared
task/construction vocabulary, Creator-visible adequacy assessment, and path
selection. It records a lightweight routing contract before branch-specific
specification, then selects `direct`, `reuse-existing`, or `design-reusable`.
`reuse-existing` covers either one adequate bundle or a bounded composition with
explicit artifact and handoff ownership. Only an evidence-backed recurring gap
enters `design-meta-skill`, which consumes that exact routing handoff and owns
the user-reviewed reusable-bundle specification, staged meta-skill generation,
validation, final approval, and live import. It does not repeat path selection.
After an approved import, run `design-meta-skill`'s
`scripts/import_meta_skill.mjs` transaction helper, then `/reload` before
invoking the new meta skill. The helper refuses unapproved collisions, uses the
shared repo/meta import lock, validates the installed copy, and rolls back
failed replacements. Review artifacts stay outside the runtime skill directory.

The newly designed meta skill and the operating graph it later creates have two
different deployment decisions. The meta skill itself is reusable Creator
infrastructure and is imported to
`~/.disco/agent/skills/<meta-skill-id>/`. After invocation and verification, its
operating graph is classified separately:

- Project scope uses `<project-dir>/.agents/skills/<skill-id>/` for output tied
  to one task, checkout, private dataset, evaluator, convention, benchmark
  instance, or environment. Uncertain reuse defaults here, and Researcher loads
  it only after the project is trusted.
- Managed scope uses `~/.disco/agent/skills/<skill-id>/` only for self-contained,
  provenance-backed output that is independent of transient run state, verified
  on representative uses, and expected to work across projects or research
  tasks.

One graph must stay in one scope. Before import, Creator shows the reuse evidence,
exact targets, entry point, verification, unresolved gaps, collisions, and
shadowing impact. After approval it runs
`distill-ml-knowledge/scripts/import_operating_skill_graph.mjs` once with every
top-level root. The helper validates operating roles and graph links, rejects
symlinks and repo router metadata, uses the shared import lock, and rolls back
the graph on failure. Overwrite requires separate approval.

Every DisCo-owned meta skill created later must declare `meta`. Every root,
router, and sub-skill it creates for task execution must declare `operating`.
Third-party skills without `metadata.disco-role` are left unchanged and load
only in Researcher; an explicitly invalid role is rejected in both modes.
Live `meta` skills may share `~/.disco/agent/skills/` with repo skills: router
rebuilds exclude them from repo inventory, routing metadata, and generated
router text.

DisCo-owned meta-skill runtime trees do not include `agents/` directories or
`agents/openai.yaml`; those are target-specific Codex manifests, not part of
DisCo's Creator skill contract. A workflow that explicitly exports operating
skills to Codex may generate policy files only in the target-side copies.

## Package / Repo Workflows

Use these in Creator mode for software repositories and Python packages:

- `prepare-repo-skill-env`: prepares and verifies an isolated Python
  inspection environment with the target repository package installed. It runs
  explicit terminal commands, prefers Conda when available, and can use
  micromamba, venv, or uv when appropriate. Its minimum environment set follows
  required CPU/GPU/backend candidates from the confirmed extraction scope; it
  does not default to CPU when a selected capability requires real accelerator
  runtime evidence. If no suitable manager or Python exists, it makes the
  host-level installation visible and obtains authorization before changing the
  host.
- `create-repo-skill`: inspects repository evidence and the verified
  Python environment, then creates a self-contained repo-specific runtime skill.
- `verify-repo-skill`: creates assertion-backed usability test cases,
  runs content-level self-refine, checks safe native examples/tests in their
  assigned CPU/GPU/backend environments, blocks unverified required backends,
  performs static verification, and writes final coverage and review handoff
  artifacts under `skills/tests/<skill-id>/`, with concrete cases in
  `test-cases/` and reports in `reports/`.
- `refresh-repo-skill`: refreshes an existing repo-specific skill after
  repository code, APIs, docs, examples, configs, or dependencies changed.
- `extend-repo-skill`: expands an already implemented skill with new or
  deeper coverage without discarding useful current guidance.
- `import-repo-skills-to-agent`: exports DisCo's managed skills and
  `repo-skills-router` into another agent tool, asks before overwriting
  duplicate skills, and merges an existing target router. When exporting only
  selected skills, it builds a filtered router view for those selected skills
  instead of copying the full DisCo-managed router.

Package workflow defaults:

- If the user does not provide a repository path for skill creation, use the
  current working directory.
- Default decision policy is `extractionScope: ask` and
  `importAfterVerification: ask`; `auto decide` / `agent decide` delegates
  scope confirmation, and `auto import` / `default import` delegates final
  import after successful verification. Auto-import never accepts a partial
  environment or unresolved required-backend block.
- Default generated skill output is `<repository-path>/skills/`, or
  `<repository-path>/skills/disco/` when the repository already has a
  `skills/` directory.
- Review and test artifacts go under
  `<repository-path>/skills/tests/<chosen-skill-id>/`, separate from runtime
  skill content.
- When no Python inspection environment is supplied, analyze the repository
  first, confirm the extraction scope, then use `prepare-repo-skill-env` to
  create the smallest suitable isolated environment with explicit terminal
  commands. The minimum may be GPU-capable when selected native cases require
  it; use CPU-only only when the selected scope is CPU-compatible. Prefer Conda
  and use micromamba, venv, or uv when appropriate, selecting Python 3.11 unless
  repository metadata requires another version.
- The default private inspection environment prefix is
  `$DISCO_CODING_AGENT_DIR/envs/<chosen-skill-id>-inspection` when that variable
  is set, otherwise `~/.disco/agent/envs/<chosen-skill-id>-inspection`.
- Verification is required before import. Approved imports write to
  `~/.disco/agent/skills/repositories/repo-skills/<skill-id>/` and rebuild the sibling live
  router inside the same global import lock. Repo output is the high-reuse
  managed special case and never uses the generic operating-graph importer.

## Paper Workflows

Use these in Creator mode to generate and validate skills for paper replication:

- `create-paper-skills`: entry skill for paper-replication skill requests.
- `paper-skills-distiller`: orchestrates paper source resolution,
  modularization, paper-replication skill creation, recovery runtime
  preparation, recovery, analysis, and refinement.
- `plan-paper-skill-modules`: creates a paper profile, module plan, and module docs.
- `create-paper-module-skill`: converts module docs into generated
  paper-replication skills.
- `prepare-paper-recovery-env`: records bounded package, model, GPU, dataset,
  and runtime evidence for recovery.
- `recover-paper-result`: runs a fast recovery experiment without reading the original
  implementation repo.
- `analyze-paper-recovery`: compares recovery against the paper target and returns
  accept/refine/blocker feedback.

Paper workflow defaults:

- Input may be a local PDF/text file, direct PDF URL, arXiv URL/id, paper title,
  or paper/repository pair.
- Process artifacts use `<workspace_root>/<paper_slug>/distillation/`; generated
  skills use `<workspace_root>/<paper_slug>/skills/`.
- The default `iteration_budget` is 10 refinement cycles after the first
  recovery attempt.
- The default `recovery_mode` is `hard`; reduced, proxy, toy, fallback, or
  smaller-model runs are diagnostics rather than successful recovery.
- Missing packages, models, datasets, benchmark files, or credentials are setup
  work first. Use an isolated environment, attempt permitted targeted setup,
  and record command evidence before declaring a blocker.
- After an accepted run passes final validation, classify the complete module
  graph as project or managed, ask for the exact deployment approval, import all
  module roots in one transaction, and write `researcher-handoff.md`. The
  generated `<workspace_root>/<paper_slug>/skills/` tree remains staging and
  review input; it is not itself a live skill root.

## Runtime Use And Routing

DisCo discovers the bundled corpus from its npm package or binary assets.
Project operating skills live under trusted projects at `.agents/skills/`, and
the managed runtime library lives at `~/.disco/agent/skills/`. In Researcher mode,
imported repo skills are registered there but normally set
`disable-model-invocation: true`, so their descriptions and bodies do not fill
the initial model context. The live `repo-skills-router` is visible by default
as the progressive-disclosure entry point; users can disable automatic router
selection while retaining explicit `/skill:repo-skills-router` invocation.
Creator mode sees the bundled and imported
meta skills instead and cannot register this operating corpus.

For an ordinary software or research task, DisCo reads the router only when a
repository-specific skill may help, reads one relevant area page and then the
matching family page, selects the best matching repo skill, and then reads that
skill's `SKILL.md` and only the references needed for the task. It uses the selected guidance with its
normal file and command tools to complete and verify the requested work. Users
can also invoke any registered skill explicitly with `/skill:<name>`.

The bundled router is a fallback template. Approved or auto-authorized imports
create or update the primary live router at
`~/.disco/agent/skills/repositories/repo-skills-router/SKILL.md`. The dedicated repo-skill
importer stages and validates the runtime tree, runs the skill replacement and
router rebuild under one global lock, and restores both on failure. The imported
skill is then directly available to DisCo Researcher; exporting it to another
agent is optional and separate.

The public collection uses the same live layout and lock through
`disco repo-skills install|update|status`. Its manifest owns only official skill
IDs, so Creator/user additions under `skills/repositories/repo-skills/` survive collection updates.
`disco repo-skills router disable|enable` changes only automatic invocation;
router rebuilds preserve the live choice, while canonical and external-agent
router output remains enabled.

Dynamic workflow orchestration is built into DisCo as the `workflow` tool,
with state stored under `~/.disco/workflows`. The create workflow uses
todo tracking for progress visibility, structured questions for user
intervention points, subagents for parallel extraction, and the built-in
workflow tool for coordinated sub-skill generation and main-agent review.
Main-agent planning owns the sub-skill structure and canonical ids, while each
subagent receives a complete brief with evidence, target files, required
references/scripts, boundaries, and quality rubrics for its assigned sub-skill.
Every workflow subagent inherits the parent session mode and its skill boundary.

When these workflow skills are copied into another agent such as Claude Code or
Codex, do not assume those DisCo-managed extensions exist. Follow the same
natural-language workflow with that agent's own task list, user-question,
subagent, or manual sequencing features.

## Use With DisCo

Run DisCo from the repository where work should happen, or pass explicit paths:

```bash
./bin/disco
```

For an ordinary task, describe the outcome directly. DisCo will consult the
managed router in the default Researcher mode when a repo-specific skill is
relevant and then execute the work:

```bash
disco -p "Use the appropriate repo skill to configure and smoke-test a local vLLM OpenAI-compatible server."
```

For skill construction, start an interactive session and switch modes before
submitting the authoring task:

```text
/creator
Create a skill for /path/to/repo using Python /path/to/env/bin/python.
```

For a non-interactive construction run, select Creator explicitly. The request
and visible evidence determine whether the repo/package, paper, or another meta
workflow applies:

```bash
disco --agent-mode creator -p "Create a skill for /path/to/repo using Python /path/to/env/bin/python."
disco --agent-mode creator -p "Use Distiller to generate and verify paper-replication skills for each run in this config. config_path: /path/to/distiller_run_config.toml"
```

`--agent-mode` selects the agent role. The existing `--mode text|json|rpc`
option selects only the output protocol. Non-interactive sessions default to
Researcher when `--agent-mode` is omitted.

Creator first assesses adequacy. A normal repository task reuses the existing
repo workflow, and a normal paper task reuses the paper workflow. Use
`design-meta-skill` only when the visible workflows cannot satisfy a concrete
source-access, evidence-selection, graph-construction, verification, or recovery
requirement.

Typical create flow:

1. Switch to Creator and ask DisCo to create a repo-specific skill for the
   target repository. If no Python inspection environment is provided, DisCo
   first analyzes the repository structure, asks for confirmation of the
   extraction scope by default, then uses `prepare-repo-skill-env` to create
   and verify the smallest inspection environment needed for that scope. If
   the create request says `auto decide`, DisCo agent-confirms the extraction
   scope from repo evidence and continues without routine manual scope
   approval.
2. When a verified Python executable is already available, include it in the
   create request to skip automatic environment preparation.
3. DisCo uses `verify-repo-skill` to create assertion-backed
   usability cases, run content-level self-refine, check safe native
   examples/tests when available, and produce review/test artifacts. By
   default, DisCo writes the publishable skill to
   `skills/<skill-id>/` when `skills/` does not exist yet, or
   `skills/disco/<skill-id>/` when the repo already has a `skills/`
   directory. Check-only artifacts go to `skills/tests/<skill-id>/`: concrete
   usability and native-backed cases live under `test-cases/`, while
   assertion/eval notes, native verification reports, final skill reports,
   human-review notes, publication checklists, and prompt samples live under
   `reports/`.
4. Approve import when DisCo asks through the structured user-question tool, or
   include `auto import` in the original create request to authorize import
   after successful verification. DisCo passes only the verified runtime skill
   directory, not the review/test artifacts, to
   `verify-repo-skill/scripts/import_repo_skill.mjs`. The importer stages and
   recursively validates the runtime tree, installs it at
   `~/.disco/agent/skills/repositories/repo-skills/<skill-id>/`, consumes
   the v2 `references/repo-routing-metadata.json` plus its external routing handoff, and rebuilds the sibling live
   `repo-skills-router` under the same global lock. If any step fails, it
   restores both the previous skill and router. After a successful import,
   DisCo Researcher can use the repo skill in a new session; exporting it to
   another agent is optional and requires an explicit user request.

Example prompt:

```text
Use create-repo-skill for /path/to/repo and put the generated skill under
/path/to/repo/skills/.
```

To delegate routine scope approval and final import approval for one create run:

```text
/skill:create-repo-skill auto decide, auto import for /path/to/repo and
put the generated skill under /path/to/repo/skills/.
```

To skip automatic environment preparation:

```text
Use create-repo-skill for /path/to/repo with /path/to/env/bin/python and
put the generated skill under /path/to/repo/skills/.
```

To refresh an existing skill after the repository changed:

```text
Use refresh-repo-skill to update /path/to/repo/skills/example-skill from
the current /path/to/repo code. Use /path/to/env/bin/python as evidence.
```

To extend an existing skill with new coverage:

```text
Use extend-repo-skill to add streaming inference coverage to
/path/to/repo/skills/example-skill. Use /path/to/repo and
/path/to/env/bin/python as evidence.
```

Paper-replication skill flow:

```text
Run /creator first in an interactive session, then:

Use Distiller to generate and verify paper-replication skills for each run in this config.

config_path: /path/to/distiller_run_config.toml
```

For repeated paper-replication skill runs, copy and fill
`create-paper-skills/assets/distiller-run-config-template.toml`. The
paper source may be a local PDF/text file, direct PDF URL, arXiv URL/id, or
paper title. The optional implementation repo may be a local repo, Git URL,
`none`, or `unknown`. Recovery must not read the original implementation repo.

## Optional Installation In Other Agents

Use `import-repo-skills-to-agent` when another agent should receive selected
Researcher-facing repository skills and the scoped `repo-skills-router`.
That workflow handles the canonical nested layout, overwrite review, filtered
router generation, and Codex `agents/openai.yaml` policy.

For portable Creator workflows, use the package-root guide
`docs/meta-skills-for-other-agents.md` (or its Chinese version,
`docs/meta-skills-for-other-agents.zh.md`). It lists
the exact 15 meta-skill directories and target paths without copying the
Researcher operating library or router. This bundled corpus README intentionally
does not duplicate shell-copy commands.



Edit workflow skills only in this source directory:

- `cli/packages/coding-agent/src/disco/skills/`

Build output is regenerated from the source copy:

- npm/dist resources: `cli/packages/coding-agent/dist/disco-resources/skills/`
- binary resources: `cli/packages/coding-agent/dist/disco-skills/`

Do not edit generated resource directories directly for source changes. Edit
the source copy and rebuild DisCo.
