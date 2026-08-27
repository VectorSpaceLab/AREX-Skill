# Direct Construction And Handoff

Read this reference only after `distill-ml-knowledge` has selected `direct` or
the user has explicitly requested a direct run and the routing contract confirms
that it is feasible. Read
[task-and-construction-contract.md](task-and-construction-contract.md) for the
canonical definitions of `tau`, `(s, u, v, e, sigma)`, `G = (S, L)`, and `R`.
The direct path produces an operating graph and construction record; it does not
author a reusable meta-skill bundle.

## Contents

- [Approve The Direct-Run Specification](#approve-the-direct-run-specification)
- [Construct And Verify](#construct-and-verify)
- [Deploy And Hand Off](#deploy-and-hand-off)

## Approve The Direct-Run Specification

Specialize the canonical fields for the current task and source anchor:

```markdown
# Direct-Run Construction Specification

- contract kind: operating-run
- routing decision revision:

## Downstream task
- tau:
- task and deliverable:
- downstream environment:
- constraints:
- task evaluation:

## Source contract (`s`)
- accepted anchors and versions:
- access and trust boundaries:
- evidence selection constraints:

## Operating use (`u`)
- required capabilities and triggers:
- expected observations:
- non-goals:

## Skill verification (`v`)
| Capability | Check | Expected observation | Gate |
|---|---|---|---|

## Construction environment (`e`)
- verified resources:
- requested resources:
- prohibited actions:
- budget and stop conditions:

## Graph structure (`sigma`)
- root/router:
- skill boundaries and links:
- progressive disclosure:

## Unknowns and assumptions
| Item | Status | Owner | Resolution |
|---|---|---|---|

## User decision
- status: proposed | approved | revise
- approved revision identifier:
```

Apply the shared clarification gate before requesting approval. The
specification may retain only assumption-safe unknowns; if a blocking unknown
remains, stop and ask for the missing information or decision instead of asking
the user to approve an incomplete revision.

Keep the run aligned to the approved revision. If the source anchor,
permissions, budget, evidence contract, graph scope, or verification plan
changes materially, pause and obtain a revised approval.

## Construct And Verify

1. Resolve the approved source anchor and record its version, access path, and
   trust boundary.
2. Retain only evidence supporting the approved operating use, verification,
   construction environment, and graph structure. Record exclusions, conflicts,
   inaccessible evidence, missing support, and assumptions.
3. Build candidate `G'` so each skill carries applicability, procedures,
   expected observations, checks, recovery actions, and evidence provenance.
4. Declare `metadata.disco-role: operating` on every root and sub-skill.
5. Verify against the approved skill-verification and construction-environment
   contract with static checks, source-support checks, graph/link checks,
   feasible task trials, and failure-recovery checks when available.
6. Repair only affected skills, links, evidence mappings, or verification
   fixtures. Rerun affected checks and graph integration.
7. If a strict check cannot run or the budget is exhausted, record the blocker
   and return an unverified candidate instead of claiming acceptance.

Keep evidence plans, drafts, candidate graphs, verification output,
construction records, and handoff files outside every live skill root.

## Deploy And Hand Off

8. Assess reuse only after verification. Default task-bound or uncertain output
   to `<project-dir>/.agents/skills/`; use `~/.disco/agent/skills/` only for
   self-contained, provenance-backed output with evidence of cross-project use.
9. Keep every root and sub-skill in one scope. Show the exact targets, entry
   point, reuse evidence, verification, unresolved gaps, collisions, shadowing,
   project-trust impact, and overwrite status before import approval.
10. After approval, invoke `../scripts/import_operating_skill_graph.mjs` once
    with every top-level root. Add `--overwrite` only after separate approval.
11. Write `researcher-handoff.md` after the import decision. Do not copy review
    artifacts into live skills or load the graph in the Creator session.

Use this construction record shape:

```markdown
# Construction Record

- task and direct-run specification revision:
- routing decision revision:
- retained/excluded/conflicting/missing evidence:
- candidate roots, entry point, boundaries, links, and provenance:
- checks, results, repairs, reruns, and unverified points:
- selected scope, exact targets, collisions, shadowing, and overwrite status:
- stop reason: accepted | unverified | blocked
- budget used and remaining limits:
```

Use this handoff shape:

```markdown
# Researcher Handoff

- task `tau` and source anchor:
- selected path: direct
- selected scope and exact imported paths:
- skill ids and graph entry point:
- verification evidence and unresolved limits:
- overwrite status:
```
