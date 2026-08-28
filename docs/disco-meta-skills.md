# DisCo Meta Skills

DisCo bundles 15 construction workflows for **Creator mode**. These are
Creator-only meta skills: they teach an agent how to distill, verify, maintain,
and export Researcher-facing operating skills. They are also portable Agent
Skills, so an agent that does not run the DisCo CLI can follow the same
evidence, review, and handoff process.

This is a different corpus from the [AREX-Skill
Library](../skills/README.md): the library contains Researcher-facing
operating skills, while these skills construct or maintain them.

## Supported Meta Skills

The source of truth is
`cli/packages/coding-agent/src/disco/skills/`. The 15 root directories below
declare `metadata.disco-role: meta` and are available to Creator mode.

### Shared Construction

| Skill | Purpose |
| --- | --- |
| `distill-ml-knowledge` | Canonical Creator entry point; identifies a source or task anchor and drives scope, ground, construct, and verify. |
| `design-meta-skill` | Designs and validates a reusable meta-skill bundle for an evidence-backed recurring construction gap. |

### Repository Skills

| Skill | Purpose |
| --- | --- |
| `prepare-repo-skill-env` | Creates or verifies an isolated, backend-aware Python inspection environment for a repository. |
| `create-repo-skill` | Turns repository evidence into a self-contained operating skill. |
| `verify-repo-skill` | Runs usability, evidence, static, native-check, and import-readiness gates. |
| `refresh-repo-skill` | Updates an existing repository skill after upstream drift. |
| `extend-repo-skill` | Adds a new workflow area or deeper coverage to an existing repository skill. |
| `import-repo-skills-to-agent` | Exports selected managed repository skills and a scoped router to another agent. |

### Paper Skills

| Skill | Purpose |
| --- | --- |
| `create-paper-skills` | Entry point for generating and validating reusable skills for paper replication. |
| `paper-skills-distiller` | Orchestrates paper source resolution, skill generation, recovery, analysis, and refinement. |
| `plan-paper-skill-modules` | Builds a paper profile, module plan, and module documents. |
| `create-paper-module-skill` | Converts a module document into a validated module skill. |
| `prepare-paper-recovery-env` | Records bounded package, model, data, and runtime evidence for recovery. |
| `recover-paper-result` | Runs a bounded recovery experiment using generated skills. |
| `analyze-paper-recovery` | Compares recovery evidence with the paper target and returns accept/refine/blocker feedback. |

The sibling `repo-skills-router` is an `operating` skill for Researcher-mode
progressive routing, so it is not part of this meta-skill list and should not
be copied as part of a portable Creator installation.

## When To Install Them Outside DisCo

DisCo already bundles these workflows. Install the portable meta skills into
another compatible agent when that agent should create, verify, refresh,
extend, or export skills but cannot run the DisCo CLI. Install DisCo itself
when you need mode-specific skill visibility, `/creator` and `/researcher`,
session isolation, the managed library, locked imports, or built-in tools.

Copying these directories does **not** reproduce DisCo's mode/session boundary;
the target agent must follow the role and approval rules in the skill text.

## Install Into Codex

The current Codex user-level convention is `~/.agents/skills`. The command
below copies only the 15 meta-skill directories; it does not copy the router,
the 1,000 repository skill graphs and their generated sub-skills, or any README:

```bash
git clone https://github.com/VectorSpaceLab/AREX-Skill.git
cd AREX-Skill
mkdir -p ~/.agents/skills
for skill in \
  analyze-paper-recovery \
  create-paper-module-skill \
  create-paper-skills \
  create-repo-skill \
  distill-ml-knowledge \
  design-meta-skill \
  extend-repo-skill \
  import-repo-skills-to-agent \
  paper-skills-distiller \
  plan-paper-skill-modules \
  prepare-paper-recovery-env \
  prepare-repo-skill-env \
  recover-paper-result \
  refresh-repo-skill \
  verify-repo-skill; do
  cp -R "cli/packages/coding-agent/src/disco/skills/$skill" ~/.agents/skills/
done
```

For a project-local Codex installation, replace `~/.agents/skills` with
`<project>/.agents/skills` and run the command from the repository checkout.
`~/.codex/skills` may still be supplied explicitly for an older Codex version,
but it is a legacy compatibility target rather than the recommended new path.

## Install Into Claude Code

Claude Code's user-level skills directory is `~/.claude/skills`:

```bash
mkdir -p ~/.claude/skills
for skill in \
  analyze-paper-recovery \
  create-paper-module-skill \
  create-paper-skills \
  create-repo-skill \
  distill-ml-knowledge \
  design-meta-skill \
  extend-repo-skill \
  import-repo-skills-to-agent \
  paper-skills-distiller \
  plan-paper-skill-modules \
  prepare-paper-recovery-env \
  prepare-repo-skill-env \
  recover-paper-result \
  refresh-repo-skill \
  verify-repo-skill; do
  cp -R "cli/packages/coding-agent/src/disco/skills/$skill" ~/.claude/skills/
done
```

Review the target directory before copying. Existing same-name skills are
overwritten by `cp -R`; use a temporary directory and compare first when the
target contains local edits. Remove only the listed directories to uninstall
this bundle. Do not remove a shared `agents/openai.yaml`, router, or unrelated
user skill.

## Adapt Deployment Paths

The copied workflows describe DisCo's live destinations:
`~/.disco/agent/skills/` for managed Creator or reusable operating skills and
`<project-dir>/.agents/skills/` for project-bound operating graphs. When the
target agent, rather than DisCo, should own a generated skill, map the managed
destination to that agent's user-level skill root. For Codex this is
`~/.agents/skills/`; for Claude Code it is `~/.claude/skills/`. Keep
project-bound or uncertain operating graphs project-local, keep one graph in
one scope, and request approval for the exact destination and any overwrite.

Repository graphs remain a special case. Prefer
`import-repo-skills-to-agent`, which preserves the sibling `repo-skills/` and
`repo-skills-router/` layout. Its bundled transactional helper merges exact
repository and assignment records, regenerates both the root
`repository-index.jsonl` and scoped router, validates the staged and installed
collection, and restores the previous target on failure. Resume an interrupted
transaction with the exact path reported by the helper. Do not flatten
repository skills into the managed root, hand-merge router Markdown, or send
their routing metadata through the generic operating-graph importer.

## What The Copy Does Not Provide

Portable meta skills do not install DisCo's TypeScript runtime, tools,
`metadata.disco-role` filtering, mode-specific prompts, automatic import
coordination, or session manager. They also do not make another agent
automatically hide operating skills while a construction workflow runs. The
bundled transaction helpers must be invoked explicitly if they are applicable
to the target layout. Keep operating skills and meta skills in separate
directories where the target agent supports that distinction, and ask for
approval before expensive setup, generated-skill import, or overwrites as
required by the workflow text.

For the full runtime with Creator/Researcher isolation, install the
[`disco` CLI](../cli/README.md) and then install the
[AREX-Skill Library](../skills/README.md) separately.
