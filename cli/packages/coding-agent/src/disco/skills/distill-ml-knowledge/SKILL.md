---
name: distill-ml-knowledge
description: "Canonical Creator entry point for ML knowledge distillation. Use for any request to turn repositories, papers, datasets, benchmark material, research notes, experiment evidence, or other source anchors into verified operating knowledge: normalize the downstream task, select direct, reuse-existing, or design-reusable, and route to the smallest adequate construction workflow."
metadata:
  disco-role: meta
---

# Distill ML Knowledge

Use this skill as the canonical Creator entry point for ML knowledge
distillation. Turn caller-supplied source anchors into operating knowledge that
a later Researcher can load. Do not execute the downstream research or software
task in this session.

## Inputs

Before selecting a construction path, collect only the routing inputs:

- Downstream ML research task, expected deliverable, execution environment,
  constraints, and acceptance procedure.
- Source anchor(s), access/version constraints, trust boundaries, and visible
  evidence.
- `path preference: auto | direct | reusable`.
- Current Creator-visible meta-skill inventory.
- User approval state for exploration, verification, import, and overwrite.

Read [task-and-construction-contract.md](references/task-and-construction-contract.md)
and normalize these inputs into its canonical task and routing records. Keep
unknown values explicit and apply its clarification gate before the affected
routing decision: resolve permitted read-only facts directly, but stop and ask
for blocking information or decisions together. Do not inspect Researcher-only
skills or hidden skill paths to improve the inventory.

## Select The Path

1. Read [path-selection-and-adequacy.md](references/path-selection-and-adequacy.md).
   Compare the required construction capabilities with the visible meta-skill
   contracts before expensive exploration or branch-specific specification.
2. Record exactly one `selected path`:
   - `direct`: construct a task-conditioned operating graph `G` plus
     construction record `R` from the concrete source anchor now.
   - `reuse-existing`: invoke one adequate existing meta-skill bundle or a
     bounded composition of existing bundles. Record the reuse mode as `single`
     or `compose` and preserve each selected workflow's verification, recovery,
     deployment, and import contract.
   - `design-reusable`: hand a verified recurring construction gap to
     `design-meta-skill`; do not use this path for a one-off prompt variation or
     ordinary task-specific operating graph.
3. Apply the preference mapping from the canonical contract. In particular,
   `reusable` is a preference, not a selected path: try `reuse-existing` first,
   then select `design-reusable` only for an evidence-backed recurring gap. If
   neither is valid, surface the conflict instead of silently selecting
   `direct` or inventing a reusable workflow.

## Execute The Selected Path

4. For `direct`, read
   [direct-construction-and-handoff.md](references/direct-construction-and-handoff.md).
   Approve an exact direct-run specification, then execute knowledge
   exploration, operating-graph generation, verification, refinement,
   deployment review, and handoff. Keep all drafts and review artifacts outside
   live skill roots.
5. For `reuse-existing`, invoke the selected workflow or ordered composition
   with the normalized task, approved source anchors, constraints, and handoff
   ownership. Do not generate a replacement meta skill. Let specialized
   workflows retain their own exact specification and importer; repository
   graphs, for example, must use the repo workflow's locked router transaction.
6. For `design-reusable`, read `../design-meta-skill/SKILL.md` and pass the exact
   routing-decision revision, normalized task, source requirements, capability
   matrix, uncovered contract, recurrence evidence, constraints, and approval
   state. The downstream skill designs the reusable bundle; it does not repeat
   path selection.
7. After an accepted `direct` or `reuse-existing` run produces an operating
   graph, apply that workflow's post-verification reuse assessment. Default
   task-bound or uncertain output to project scope and reserve managed scope for
   evidence-backed cross-project reuse. Keep every root and sub-skill in one
   scope.
8. Before import, show the selected scope, exact targets, graph entry point,
   verification results, unresolved gaps, collisions, shadowing impact, and
   overwrite status. Use the selected workflow's specialized importer when it
   has one. Otherwise, after approval, invoke
   [the bundled transaction helper](scripts/import_operating_skill_graph.mjs)
   once with every top-level root.
9. Write `researcher-handoff.md` with the normalized task, source anchor,
   selected path, reuse mode when applicable, scope, exact imported paths,
   skill ids, graph entry point, verification evidence, and unresolved limits.
   Do not load or execute the resulting operating graph in the Creator session.
