# Direct Construction And Handoff

Read this reference after `distill-ml-knowledge` records
`construction strategy: direct` and the required source/task approvals are in
place. The direct strategy produces an operating graph and construction record;
it does not author a reusable Creator meta-skill.

## Approve The Construction Specification

For a task-oriented run, specialize the task anchor as
`tau = (q, D, E, g)`. For a task-agnostic run, keep the source anchor as `z` and
do not invent `tau`. Approve this exact revision after grounding has produced
the evidence plan:

```markdown
# Direct Construction Specification

- contract kind: operating-run
- routing decision revision:
- anchor kind: source | task
- distillation form: task-agnostic | task-oriented
- anchor `z`:
- task `tau`, when applicable: `tau = (q, D, E, g)`

## Scope `Q`
- required capabilities and triggers:
- expected operating observations:
- graph boundaries and non-goals:

## Grounding `X`
- accepted source material and revisions:
- provenance, access, and trust boundaries:
- evidence selection, exclusions, conflicts, and assumptions:

## Candidate graph `G_tilde`
- root/router and skill boundaries:
- explicit routing, dependency, composition, and reference links:
- progressive disclosure and bundled resources:

## Verification
| Capability or representative use | Check | Expected observation | Gate |
|---|---|---|---|
| ... | ... | ... | strict / soft |

## Creator construction record
- verified resources and permissions:
- prohibited actions, budget, and stop conditions:
- staging, resume, and recovery:
- deployment scope and importer:

## Unknowns and assumptions
| Item | Status | Owner | Resolution |
|---|---|---|---|
| ... | ... | ... | ... |

## User decision
- status: proposed | approved | revise
- approved revision identifier:
```

The specification must have no blocking unknowns at approval. Keep only
assumption-safe unknowns with an owner and validation plan. Reopen approval if
the anchor, evidence boundary, graph scope, budget, permissions, or verification
gate changes materially.

## Construct And Verify

1. Resolve the approved anchor and record source identity, revision, access, and
   trust boundary in `R`.
2. Retain only evidence supporting `Q`, the construction environment, graph
   structure, and verification contract. Record exclusions, conflicts, missing
   support, inaccessible material, and assumptions in `X`/`R`.
3. Build candidate `G_tilde = (S_tilde, L_tilde)`. Each node must carry its
   applicability, procedures, expected observations, checks, recovery actions,
   and evidence provenance.
4. Declare `metadata.disco-role: operating` on every root and sub-skill.
5. Verify static structure, source support, graph links, executable or
   representative-use behavior, and failure recovery. For a task-oriented run,
   run task-level trials when the approved `g` makes them applicable. For a
   task-agnostic source run, use source-supported representative workflows and
   do not substitute an invented task outcome.
6. Repair only affected skills, links, evidence mappings, or fixtures, then
   rerun the affected checks and graph integration. A strict blocker leaves the
   candidate unverified.

Keep evidence plans, drafts, candidate graphs, verification output, construction
records, and handoff files outside every live skill root.

## Deploy And Hand Off

7. Assess reusability only after verification. Default task-bound or uncertain
   output to `<project-dir>/.agents/skills/`; use managed scope only when the
   complete graph is self-contained, provenance-backed, and supported by
   cross-project representative-use evidence.
8. Keep every root and sub-skill in one scope. Show exact targets, entry point,
   verification, unresolved gaps, collisions, shadowing impact, and overwrite
   status before import approval.
9. After approval, invoke the selected locked importer once with every top-level
   root. Add overwrite only after separate approval.
10. Write `researcher-handoff.md` after the deployment decision. Do not load the
    graph or execute the downstream task in the Creator session.

Use this handoff shape:

```markdown
# Researcher Handoff

- anchor kind: source | task
- distillation form: task-agnostic | task-oriented
- anchor `z`:
- task `tau`, when applicable: `tau = (q, D, E, g)`
- scoped capabilities `Q`:
- grounded evidence `X` and provenance scope:
- accepted or unverified graph `G`:
- construction record `R` path:
- construction strategy: direct
- selected scope and exact imported paths:
- skill ids and graph entry point:
- verification evidence and unresolved limits:
- overwrite status:
```
