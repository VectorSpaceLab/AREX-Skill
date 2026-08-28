---
name: design-meta-skill
description: "Designs and validates a reusable Creator meta-skill workflow for an evidence-backed recurring construction gap after distill-ml-knowledge selects the design-reusable strategy. Use it to parameterize future source or task anchors, verify the workflow, and prepare an approved managed Creator-infrastructure import."
metadata:
  disco-role: meta
---

# Design Reusable Meta Skill Bundle

Design a parameterized Creator workflow for future distillation anchors. This
skill does not produce the operating graph for the current task and does not
execute the final research or software task. The paper distinguishes only
task-agnostic and task-oriented distillation; `design-reusable` is a Creator
construction strategy, not a third distillation form.

`distill-ml-knowledge` owns anchor identification, `Q` scoping, adequacy
assessment, composition assessment, and strategy selection. This skill owns the
reusable workflow design, validation, approval, and managed Creator-infrastructure
import after it receives that exact handoff.

## Required Handoff

Require the current routing handoff with:

- decision revision and `construction strategy: design-reusable`;
- `anchor kind`, anchor identity, and `distillation form`;
- current task `tau = (q, D, E, g)` when the gap came from a task-oriented run;
- future anchor class and intended operating output when it came from a
  task-agnostic source run;
- scoped capabilities `Q`, required evidence/source behavior, and
  verification/recovery needs;
- Creator-visible capability matrix and inventory snapshot;
- uncovered recurring construction contract, recurrence evidence, and why
  extension or bounded composition is inadequate;
- construction constraints, unknowns, assumptions, and approval state.

If invoked without this handoff, read `../distill-ml-knowledge/SKILL.md` and
return through canonical routing. Do not start another reuse, composition, or
gap decision here. If the visible inventory or requirements changed materially,
return the evidence for a new routing revision.

## Workflow

1. Validate the handoff and stop with the exact missing blocking fields. Do not
   inspect Researcher-only skills or hidden paths.
2. Read [reusable-bundle-specification.md](references/reusable-bundle-specification.md).
   Draft the exact future-anchor and four-stage specification, preserving
   exclusions and assumption owners. Obtain approval before material source
   exploration, file generation, or compute use.
3. Stage all artifacts outside live skill roots, for example:

   ```text
   ~/.disco/agent/creator-runs/<run>/<timestamp>/
     routing-handoff.md
     reusable-bundle-spec.md
     evidence-plan.md
     draft/<meta-skill-id>/
     verification/
     construction-record.md
   ```

4. Read [generation-verification-and-review.md](references/generation-verification-and-review.md)
   and generate a workflow that later performs scope, ground, construct, and
   verify for caller-supplied anchors.
5. Parameterize all source, task, environment, permissions, budget, graph, and
   handoff inputs. Never hardcode the current checkout, credentials, temporary
   task state, or machine-specific paths.
6. Keep every draft meta `SKILL.md` explicitly `metadata.disco-role: meta`. Do
   not include target-specific `agents/` or `agents/openai.yaml`. Require every
   operating root, router, and sub-skill produced by the future workflow to
   declare `metadata.disco-role: operating`.
7. Verify the candidate workflow on representative anchors: one task-agnostic
   source anchor, one task-oriented task anchor with source discovery, one
   source/access failure and recovery, one graph verification failure and local
   repair, one task-bound/project deployment, and one self-contained/managed
   deployment. Confirm uncertain reuse defaults to project scope, each graph
   stays in one scope, and repo output uses its specialized locked transaction.
8. Run the validator before review:

   ```bash
   node scripts/validate_meta_skill.mjs <draft-meta-skill-dir>
   ```

9. Present the routing revision, reusable-bundle specification, evidence plan,
   candidate files, verification results, unresolved gaps, exact managed target,
   collisions, and overwrite impact. Obtain approval for this exact artifact
   revision.
10. After approval, import only the reviewed runtime meta bundle as Creator
    infrastructure:

    ```bash
    node scripts/import_meta_skill.mjs \
      --agent-dir ~/.disco/agent \
      <creator-run-dir>/draft/<meta-skill-id>
    ```

    Use `--overwrite` only after separate approval. The helper refuses to
    replace an operating or unclassified target.
11. Tell the user to run `/reload`. The next invocation of the imported meta
    skill, not this design run, constructs and verifies the operating graph and
    writes its `researcher-handoff.md`.

## Required Outputs

- validated routing handoff and recurring-gap evidence;
- approved reusable-bundle specification;
- staged, parameterized meta-skill draft and evidence plan;
- verification results, repairs, unresolved points, and construction record;
- separate managed Creator-infrastructure import proposal or result;
- contract for later operating graph verification, one-scope deployment, locked
  import, and Researcher handoff.

The future workflow's output is accepted operating graph `G` and construction
record `R`; the current meta bundle itself is not an operating graph. Its
reusability is assessed against recurring anchors and the generated workflow's
ability to support both project deployment under `.agents/skills/` and managed
deployment under `~/.disco/agent/skills/`.

## Failure Rules

- Missing or stale handoff: return to `distill-ml-knowledge`.
- Unresolved source access, credentials, hardware, permissions, or budget: keep
  the item in the future construction environment and stop before use.
- Failed strict verification: report the unverified bundle and do not import it.
- Invalidated recurring gap: return evidence for a new routing revision.
- Collision, overwrite, expanded source access/cost, or weakened verification:
  obtain separate approval.
- Never write drafts or review artifacts into live skill roots, split one future
  operating graph across scopes, send repo metadata through the generic
  importer, or execute the final downstream task here.
