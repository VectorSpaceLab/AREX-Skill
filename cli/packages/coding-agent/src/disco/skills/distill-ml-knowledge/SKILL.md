---
name: distill-ml-knowledge
description: "Canonical Creator entry point for DisCo skill distillation. Use when turning a repository, paper, tutorial, dataset, benchmark, research note, task, or other source material into a verified operating skill graph. Identify the anchor, scope capabilities, ground them in evidence, construct a candidate graph, verify it into an accepted graph, and record the construction."
metadata:
  disco-role: meta
---

# Distill ML Knowledge

Use this skill as the canonical Creator entry point for DisCo skill
distillation. Convert a distillation anchor into a verified operating skill
graph that a later Researcher can load. The four paper-aligned stages are
**scope**, **ground**, **construct**, and **verify**. This skill does not execute
the downstream research or software task in the current Creator session.

## Identify The Anchor

Read [task-and-construction-contract.md](references/task-and-construction-contract.md)
and create one anchor record before material exploration:

```markdown
# Distillation Anchor

- anchor kind: source | task
- anchor value:
  - source anchor: repository | paper | tutorial | dataset | benchmark | other
  - task anchor: `tau = (q, D, E, g)`
- source material: provided | discovered during grounding | mixed
- version/access/trust boundary:
- intended future use:
- unknowns and assumptions:
```

Use a source anchor for task-agnostic distillation. It may be a repository,
paper, tutorial, dataset, benchmark, or comparable source and does not require a
made-up downstream task. Use a task anchor for task-oriented distillation. The
task-oriented `D`, `E`, and `g` values are blocking when routing or verification
would change without them; ask for clarification before the affected action.

## Scope, Ground, Construct, Verify

1. **Scope** the capabilities `Q` and define applicability, non-goals, candidate
   skill boundaries, graph entry points, and verification targets. For a
   task-agnostic anchor, begin with source understanding and capability
   identification. For a task-oriented anchor, begin with task decomposition and
   capability gap analysis.
2. **Ground** `Q` in retained evidence `X`. For task-agnostic distillation,
   extract knowledge from the source anchor. For task-oriented distillation,
   discover permitted source material for the capability gaps, then select and
   record evidence. Preserve provenance, versions, exclusions, conflicts,
   inaccessible material, and assumptions.
3. **Construct** a candidate graph `G_tilde = (S_tilde, L_tilde)`. Use tool
   encapsulation and skill packaging for source-oriented work, or skill
   generation for task-oriented work. Each root and sub-skill needs a clear
   responsibility, progressive-disclosure route, evidence boundary, checks, and
   recovery behavior.
4. **Verify** the candidate graph with static, source-support, executable,
   graph/link, and applicable task-level or representative-use checks. Exercise
   failure recovery and repair affected skills, links, evidence mappings, or
   fixtures. The result is accepted graph `G` plus construction record `R`, or a
   candidate with explicit unverified blockers. Task-agnostic runs use
   source-supported representative workflows and do not invent a task-level
   outcome trial when no downstream task exists.

## Creator Construction Strategy

After a lightweight scope/preflight, read
[construction-strategy-and-adequacy.md](references/construction-strategy-and-adequacy.md)
and record exactly one Creator construction strategy. This is implementation
orchestration recorded in `R`, not a third distillation form:

- `reuse-existing`: invoke one adequate visible workflow or a bounded
  composition, preserving its verification, deployment, recovery, handoff, and
  specialized importer contract.
- `direct`: execute the four stages for the current anchor and produce the
  operating graph now.
- `design-reusable`: pass an evidence-backed recurring construction gap to
  `design-meta-skill`, which designs a future Creator workflow. It does not
  directly produce the current Researcher operating graph.

Record the layered routing fields below. Do not use the construction strategy to
pretend that the anchor form is a task form:

```markdown
# Routing Record

- anchor kind: source | task
- distillation form: task-agnostic | task-oriented
- anchor `z`:
- scoped capabilities `Q`:
- required evidence and verification:
- construction strategy: direct | reuse-existing | design-reusable
- reuse mode: single | compose | not-applicable
- selected visible contracts:
- uncovered recurring construction gap:
- recurrence evidence:
- construction constraints and approval state:
- decision revision:
```

Apply `auto` by preferring an adequate existing workflow, then `direct` for a
concrete task-conditioned need or `design-reusable` only for a verified
recurring construction gap. A `reusable` preference tries `reuse-existing`
first and must surface a conflict rather than silently falling back to a
one-off direct run.

## Handoffs And Deployment

For `direct`, read [direct-construction-and-handoff.md](references/direct-construction-and-handoff.md)
and obtain approval of the exact construction specification after grounding.
For `reuse-existing`, pass the anchor, `Q`, `X`, constraints, and ownership to
the selected workflow without bypassing its verification or importer. For
`design-reusable`, pass the complete routing handoff to
`../design-meta-skill/SKILL.md`; that skill must not repeat strategy selection.

After an accepted operating graph is verified, decide project or managed scope
separately. Default task-bound or uncertain graphs to
`<project-dir>/.agents/skills/`; use `~/.disco/agent/skills/` only for
self-contained, provenance-backed graphs with representative reuse evidence.
Keep every root and sub-skill in one scope, show exact destinations and
collisions, obtain import approval, and invoke the selected specialized or
generic locked importer once with all top-level roots.

Write `researcher-handoff.md` outside live skill roots with the anchor kind,
distillation form, `Q` summary, `X` provenance scope, accepted or unverified
`G`, `R` path, construction strategy, selected scope, exact imported paths,
entry point, verification evidence, and unresolved limits. Do not load the
resulting operating graph or execute the downstream task in this Creator run.
