# Portable Meta Skills For Other Agents

DisCo bundles a set of construction workflows for **Creator mode**. They are
portable Agent Skills, so an agent that does not run the DisCo CLI can still
follow the same evidence, review, and handoff process. This is a different
installation path from the [Research Skills Library](../skills/README.md):
the library contains Researcher-facing operating skills, while these skills
teach an agent how to construct or maintain them.

## When To Install Them

Install the portable meta skills when another agent should create, verify,
refresh, extend, or export skills but cannot install DisCo. Install DisCo itself
when you need mode-specific skill visibility, `/creator` and `/researcher`,
session isolation, the managed library, locked imports, or the built-in tools.
Copying these directories does **not** reproduce DisCo's mode/session boundary;
the target agent must follow the role and approval rules in the skill text.

## Bundled Meta Skills

The source of truth is
`cli/packages/coding-agent/src/disco/skills/`. The current Creator corpus has
these 15 skills:

| Skill | Purpose |
| --- | --- |
| `distill-ml-knowledge` | Canonical Creator entry point; own the shared task/construction contract and select direct, reuse-existing (single or composed), or design-reusable. |
| `design-meta-skill` | Consume a verified recurring-gap handoff and design the parameterized reusable meta-skill bundle without repeating path selection. |
| `prepare-repo-skill-env` | Create or verify an isolated Python inspection environment for a repository. |
| `create-repo-skill` | Turn repository evidence into a self-contained operating skill. |
| `verify-repo-skill` | Run usability, evidence, static, native-check, and import-readiness gates. |
| `refresh-repo-skill` | Update an existing repository skill after upstream drift. |
| `extend-repo-skill` | Add a new workflow area to an existing repository skill. |
| `import-repo-skills-to-agent` | Export selected managed operating skills and a scoped router to another agent. |
| `create-paper-skills` | Entry point for generating and validating reusable skills for paper replication. |
| `paper-skills-distiller` | Orchestrate paper source resolution, paper-replication skill generation, recovery, analysis, and refinement. |
| `plan-paper-skill-modules` | Build a paper profile, module plan, and module documents. |
| `create-paper-module-skill` | Convert a module document into a validated module skill. |
| `prepare-paper-recovery-env` | Record bounded package, model, data, and runtime evidence for recovery. |
| `recover-paper-result` | Run a bounded recovery experiment using generated skills. |
| `analyze-paper-recovery` | Compare recovery evidence with the paper target and return accept/refine/blocker feedback. |

All 15 directories declare `metadata.disco-role: meta`. The sibling
`repo-skills-router` is an `operating` skill and must not be copied as part of
this installation.

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
`repo-skills-router/` layout and builds a router scoped to the exported skills.
Do not flatten repository skills into the managed root or send their routing
metadata through the generic operating-graph importer.

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
[Research Skills Library](../skills/README.md) separately.
