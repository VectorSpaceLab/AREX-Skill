# DisCo Workflows

This guide covers the operational details intentionally omitted from the main
README: mode boundaries, Researcher execution, Creator construction workflows,
deployment scopes, and cross-agent export. Install DisCo and the published
repository collection as described in the [Installation Guide](installation.md)
before using repository guidance.

## Agent Modes And Sessions

Every DisCo session has one agent mode:

| Mode | Visible skills | Responsibility |
| --- | --- | --- |
| **Researcher** (default) | `operating` and `shared` skills, including user skills without `metadata.disco-role` | Use routed operating knowledge, code, tools, and experiments to complete an ML research task. |
| **Creator** | Skills marked `metadata.disco-role: meta` or `shared` | Start with `distill-ml-knowledge`, select `direct`, `reuse-existing` (single or composed), or `design-reusable`, and route only a verified recurring construction gap to `design-meta-skill`. |

Use `--creator` or `--researcher` to select the role for a new session. These
selectors work in both interactive and non-interactive sessions. In the
interactive UI, `/creator` and `/researcher` warn before opening a new session
with a clean context. The previous session remains available through `/resume`
and can be exported separately; an export from the new session contains only
the new session's activity.

The `--mode text|json|rpc` option selects the output protocol and is independent
of the agent mode. If a natural-language request belongs to the other agent
mode, DisCo stops before doing the work and suggests the corresponding switch;
it never changes modes implicitly.

`shared` is reserved for utilities that genuinely apply in both modes. It does
not authorize Creator to execute the final research task or Researcher to carry
out Creator construction work. Package installers can override visibility for
all resources in one package with `disco install <source> --for
creator|researcher|both|default`; see the [package
guide](../cli/docs/packages.md#mode-targeting).

## Researcher Workflows

### Use The Published Repository Collection

Install the public collection once, then use the same command namespace to
inspect and update it:

```bash
disco repo-skills install
disco repo-skills status
disco repo-skills update
```

`status` performs an offline check of the recorded commit, managed content,
router state, and router coverage. It does not check the remote HEAD; `update`
does that explicitly.

The updater changes only official managed skill IDs and preserves additional
Creator or manually imported repo skills. Local edits to an official skill are
reported as drift; `--force` is required to replace them and retains a backup.

After installation, ask for a concrete research outcome. For example, compare
two inference systems under a controlled protocol:

```bash
disco --researcher -p "Benchmark vLLM and SGLang with the same model and workload on this machine. Tune each server under identical hardware and memory constraints, report the best verified throughput for each, and preserve the commands and measurements needed to reproduce the comparison."
```

For a relevant request, DisCo reads `repo-skills-router`, opens one or two
likely area pages, compares the matching family pages, and then reads selected
skills such as `vllm/SKILL.md` and `sglang/SKILL.md`. It uses its normal file,
command, and experiment tools to perform and verify the task. It does not
inject all repository-skill descriptions or bodies into the initial context.

The router participates in automatic skill selection by default. To remove it
from model-visible skill discovery without uninstalling the collection, run:

```bash
disco repo-skills router disable
```

The disabled router remains registered for explicit
`/skill:repo-skills-router` invocation. Restore automatic selection with
`disco repo-skills router enable`; either change takes effect in a new
Researcher session.

When the exact skill is known, it can also be invoked explicitly:

```bash
disco --researcher -p "/skill:vllm determine and verify the highest-throughput vLLM configuration for <model and workload>"
```

### Use An Approved Task-Specific Graph

After Creator constructs and imports a task-specific operating graph, invoke
the entry skill recorded in its handoff:

```bash
disco --researcher -p "/skill:<graph-entry> Complete <research task> within <environment and budget constraints>, and verify it with <evaluator>."
```

Researcher progressively opens the required subgraph and applies its methods,
checks, and recovery actions during execution. If the visible graph cannot
supply required knowledge, it records the concrete capability gap and suggests
a new Creator session instead of authoring skills in place.

The handoff also records where the complete graph was deployed:

- Output tied to one task, project, private dataset, evaluator, benchmark
  instance, or local environment, as well as output whose reuse is uncertain,
  goes to `<project-dir>/.agents/skills/`. It is loaded only after the project
  is trusted.
- A self-contained, provenance-backed graph with representative cross-project
  verification may be proposed for `~/.disco/agent/skills/`.
- One graph is never split across the two scopes.

## Creator Workflows

Start Creator for construction, review, maintenance, or export:

```bash
disco --creator
```

Creator sees meta and shared skills. It first identifies the source or task
anchor, scopes the required capabilities, and checks whether the visible
construction workflows cover the request. Reuse or composition is recorded as
a Creator construction strategy when its full verification and handoff contract
remains intact.

### Assess Construction-Workflow Adequacy

Start with `distill-ml-knowledge` for an ordinary ML knowledge distillation
request. It identifies the anchor and drives `scope`, `ground`, `construct`,
and `verify`. A repository source normally uses
`reuse-existing` with `create-repo-skill`; a paper source normally reuses the
paper workflow. Only an evidence-backed recurring gap in source handling,
evidence selection, graph shape, verification, environment, or recovery is
handed to `design-meta-skill`:

```bash
disco --creator -p "/skill:distill-ml-knowledge identify <source or task anchor>; scope, ground, construct, and verify the operating skill graph."
```

An approved new meta skill is imported only after validation and explicit user
review, always as reusable Creator infrastructure at
`~/.disco/agent/skills/<meta-skill-id>/`. Invoke it with the concrete knowledge
source anchor to construct the task's operating skills. Those outputs receive
their own reuse classification and import approval according to the deployment
rules above. Creator then writes a handoff for a new Researcher session.

### Construct A Repository Skill

Create and verify a repository-specific skill from source evidence:

```bash
disco --creator -p "Create a repo skill for /path/to/repo."
```

The workflow analyzes repository structure, prepares or checks a Python
inspection environment when needed, writes runtime guidance, records
provenance, and hands the draft to `verify-repo-skill`. Verification creates
assertion-backed usability cases, runs content-level self-refinement, checks
safe native examples or tests when available, runs static quality gates, and
writes coverage and review artifacts before the skill is treated as ready.

To delegate both extraction-scope selection and managed-library import after
successful verification, state that explicitly:

```bash
disco --creator -p "Create a repo skill for /path/to/repo with auto decide and auto import."
```

### Construct Paper-Replication Skills

For repeatable runs that generate and verify skills for paper replication, copy
and fill the bundled run configuration, then pass it to DisCo:

```bash
cp cli/packages/coding-agent/src/disco/skills/create-paper-skills/assets/distiller-run-config-template.toml \
  /path/to/distiller_run_config.toml
disco --creator -p "Use Distiller to generate and verify paper-replication skills for each run in this config. config_path: /path/to/distiller_run_config.toml"
```

The paper source can be a local PDF or text file, direct PDF URL, arXiv URL or
identifier, or paper title. An implementation repository is optional and can
be a local path, Git URL, `none`, or `unknown`.

Distiller modularizes the paper, creates and validates module-level skills for
paper replication, prepares bounded runtime evidence, runs the strongest
feasible recovery experiment without reading the original implementation
repository, analyzes gaps, refines within `iteration_budget` when needed, and
writes attempt artifacts plus final reports under
`<attempt_dir>/reports/final/`. The default `recovery_mode` is `hard`: reduced,
proxy, toy, or fallback runs are recorded as diagnostics rather than accepted
as successful recovery unless `soft` mode is selected explicitly.

After final validation, Creator proposes one deployment scope for the complete
paper-replication skill graph, imports it only after approval, and writes a
Researcher handoff. The generated `skills/` tree remains staging content until
it is approved and imported.

### Maintain An Existing Skill

Extend a correct skill when it needs deeper coverage for a new workflow area:

```bash
disco --creator -p "Add streaming inference coverage to the existing skill at /path/to/repo/skills/example-skill using /path/to/repo as evidence."
```

Refresh a skill when upstream APIs, configuration, examples, dependencies, or
runtime behavior change:

```bash
disco --creator -p "Refresh the skill at /path/to/repo/skills/example-skill against the current /path/to/repo code."
```

Refresh preserves correct existing guidance while reconciling stale guidance
with the current source baseline.

### Export Repository Skills To Another Agent

Use `import-repo-skills-to-agent` when Codex, Claude Code, or another compatible
agent needs selected skills from DisCo's managed repository collection. The
workflow preserves the sibling layout of `repo-skills/` and
`repo-skills-router/` in the target skill directory. After overwrite approval,
its transactional helper regenerates the final root index and scoped router,
keeps unrelated target repository skills, applies Codex-only policy to target
copies, and automatically restores the prior target on a failed mutation. Use
the reported `--resume <transaction-directory>` command after interruption;
do not repair or merge partial output manually.

Import the router plus `vllm` and `sglang` into Claude Code:

```bash
disco --creator -p "/skill:import-repo-skills-to-agent import vllm and sglang to ~/.claude"
```

Import the same skills into Codex's recommended user-level skills root:

```bash
disco --creator -p "/skill:import-repo-skills-to-agent import vllm and sglang to ~/.agents"
```

Restart the target agent after import. The [AREX-Skill Library
guide](../skills/README.md) documents the source layout and
DisCo installation, while the
[`import-repo-skills-to-agent` workflow](../cli/packages/coding-agent/src/disco/skills/import-repo-skills-to-agent/SKILL.md)
defines target layouts, overwrite policy, and router invocation conventions.

## Reference

- [Architecture](architecture.md)
- [Bundled Skills Reference](../cli/packages/coding-agent/src/disco/skills/README.md)
- [AREX-Skill Library](../skills/README.md)
- [DisCo Meta Skills](disco-meta-skills.md)
