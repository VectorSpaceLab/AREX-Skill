---
name: design-meta-skill
description: "Design and validate a reusable Creator meta-skill bundle for an evidence-backed recurring construction gap after distill-ml-knowledge selects design-reusable. Use when the canonical routing handoff proves that no existing visible meta workflow or bounded composition covers the required source, evidence, graph, verification, environment, or recovery contract. If invoked without that handoff, route through distill-ml-knowledge before beginning design."
metadata:
  disco-role: meta
---

# Design Reusable Meta Skill Bundle

Design a parameterized construction workflow, not the operating skills for one
task and not the final research result. Treat `distill-ml-knowledge` as the
owner of task normalization, adequacy assessment, composition assessment, and
path selection. This skill owns only the `design-reusable` branch.

## Required Handoff

Require the exact canonical routing handoff from `distill-ml-knowledge`:

- Routing-decision revision with `selected path: design-reusable`.
- Normalized downstream task `tau`, source requirements, required operating
  capabilities, verification/recovery needs, and construction constraints.
- Creator-visible capability matrix and inventory snapshot.
- Uncovered reusable construction contract and evidence that existing workflow
  extension or bounded composition is inadequate.
- Evidence that the construction capability will recur across future source
  anchors.
- Unknowns, assumptions, and user approval state.

If the skill is explicitly invoked without this handoff, read
`../distill-ml-knowledge/SKILL.md` and complete canonical routing first. Do not
start a parallel `reuse | compose | gap` decision here. If the visible inventory
or requirements changed materially after the handoff, return the changed
evidence to `distill-ml-knowledge` for a new routing revision.

## Workflow

1. Validate that the handoff is complete, current, internally consistent, and
   selects `design-reusable`. Do not inspect Researcher-only skills or hidden
   skill paths to challenge it. For missing required fields or blocking
   unknowns, return the exact list to `distill-ml-knowledge` and stop this branch
   until the user supplies the required information or decision and routing is
   revised.
2. Read
   [reusable-bundle-specification.md](references/reusable-bundle-specification.md).
   Draft the parameterized `reusable-bundle` specification from the handoff,
   preserving unresolved assumptions and exclusions. Obtain approval of its
   exact revision before material source exploration, file generation, or
   compute use.
3. Create a staging directory outside every live skill root. Use a layout such
   as:

   ```text
   ~/.disco/agent/creator-runs/<task-slug>/<timestamp>/
     routing-handoff.md
     reusable-bundle-spec.md
     evidence-plan.md
     draft/<meta-skill-id>/
     verification/
     construction-record.md
   ```

4. Read
   [generation-verification-and-review.md](references/generation-verification-and-review.md).
   Execute knowledge exploration, meta-skill generation, representative
   forward verification, failure-recovery verification, and focused refinement
   against the approved specification.
5. Parameterize the candidate over future caller-supplied source anchors. Do not
   hardcode the current checkout, environment prefix, credentials, one task's
   transient paths, or current routing handoff.
6. Require every draft meta `SKILL.md` to declare:

   ```yaml
   metadata:
     disco-role: meta
   ```

   Keep the DisCo runtime tree free of target-specific `agents/` directories and
   `agents/openai.yaml`. Require every root, router, and sub-skill in the
   operating graphs it later generates to declare
   `metadata.disco-role: operating`.
7. Require the candidate workflow to verify each generated operating graph,
   perform its reusability assessment after verification, keep the whole graph
   in one scope, show the exact deployment proposal, and use the correct locked
   importer. Preserve the repo workflow's nested collection and sibling-router
   transaction as the managed special case.
8. Run the validator before review:

   ```bash
   node scripts/validate_meta_skill.mjs <draft-meta-skill-dir>
   ```

9. Present the routing-decision revision, reusable-bundle specification,
   evidence plan, candidate file list, verification results, unresolved gaps,
   exact managed target, collisions, and overwrite impact. Obtain explicit
   approval for the exact artifact revision; do not infer it from vague
   continuation language.
10. After approval, import only the reviewed runtime bundle as managed Creator
    infrastructure:

    ```bash
    node scripts/import_meta_skill.mjs \
      --agent-dir ~/.disco/agent \
      <creator-run-dir>/draft/<meta-skill-id>
    ```

    If the target exists, obtain separate overwrite approval before adding
    `--overwrite`. The helper may revise an existing `meta` target but refuses to
    replace an operating or unclassified target.
11. Tell the user to run `/reload`, then invoke the new meta skill with a
    concrete source anchor. That later invocation owns operating-graph
    construction and writes `researcher-handoff.md` after its deployment
    decision; this design session does not execute the downstream research task.

## Required Outputs

- Validated canonical routing handoff and recurring-gap evidence.
- User-approved reusable-bundle specification.
- Evidence plan and staged, parameterized meta-skill draft.
- Verification evidence, repairs, and explicit unverified points.
- Human-readable construction record tied to both exact revisions.
- Reviewed managed-import proposal or approved meta-skill import result.
- Contract for later operating-graph verification, one-scope deployment,
  transaction-safe import, and Researcher handoff.

## Failure Rules

- If the handoff is missing, stale, or no longer supports `design-reusable`,
  return to `distill-ml-knowledge`; do not independently select another path.
- If source access, credentials, hardware, permissions, or budget is unresolved,
  keep it in the reusable-bundle construction environment, stop before use, and
  ask the user.
- If a strict verification gate cannot pass, report the unverified bundle and
  do not import it as accepted Creator infrastructure.
- If a newly visible adequate workflow or composition invalidates the recorded
  gap, return that evidence for a new routing revision and stop generation.
- Require separate approval for any collision, overwrite, expanded source
  access, expanded cost, or weakened verification.
- Never write drafts or review artifacts directly into
  `~/.disco/agent/skills/` or `<project-dir>/.agents/skills/`.
- Never split one later operating graph across project and managed scopes, send
  repo routing metadata through the generic importer, or execute the final ML
  research task in this workflow.
