# Generation, Verification, And Review

Run these stages only after approval of an exact reusable-bundle specification
for the `design-reusable` routing revision selected by
`distill-ml-knowledge`.

## Contents

- [Knowledge Exploration](#knowledge-exploration)
- [Meta-Skill Generation](#meta-skill-generation)
- [Verification And Refinement](#verification-and-refinement)
- [Construction Record And Review](#construction-record-and-review)
- [Import And Later Handoff](#import-and-later-handoff)

## Knowledge Exploration

Resolve only source evidence permitted by the approved bundle specification.
Map each proposed meta-skill capability to retained evidence, expected operating
output, validation, and recovery. Record exclusions, conflicts, missing support,
inaccessible evidence, and assumptions. Machine-specific evidence paths belong
in the construction record and must not leak into the reusable runtime bundle.

## Meta-Skill Generation

Generate a candidate workflow that later constructs operating graph
`G = (S, L)` from a caller-supplied anchor. Require it to define:

- Triggering description, applicability, and non-applicability.
- Parameterized source inputs and construction constraints.
- Ordered stages, intermediate artifacts, stop conditions, and recovery.
- Coherent operating-skill boundaries and explicit routing, dependency, or
  composition links.
- Evidence provenance and construction-record requirements.
- Static, executable, source-support, graph-integration, and human-review gates.
- Post-verification project/managed classification that defaults uncertainty to
  project scope and keeps the complete graph in one scope.
- Exact-path import review, correct locked importer, and Researcher handoff.

Declare `metadata.disco-role: meta` on the meta skill and all meta sub-skills.
Do not include `agents/` or `agents/openai.yaml` in their DisCo runtime trees.
Require `metadata.disco-role: operating` on every generated operating root,
router, and sub-skill. Keep root routers model-visible when routing requires it;
use `disable-model-invocation: true` on children when progressive disclosure
benefits from it.

## Verification And Refinement

Apply the approved bundle-verification gates. At minimum:

1. Parse all frontmatter and enforce exact role values.
2. Validate names, descriptions, directory identity, links, scripts, required
   artifacts, and absence of target-specific `agents/` directories.
3. Search for credentials, machine-specific paths, transient task state, and
   runtime dependencies on construction sources.
4. Run representative anchors or dry runs that exercise source resolution,
   evidence selection, graph generation, and construction records.
5. Inspect claims for source support and applicability limits.
6. Verify generated graph routing, links, roles, and progressive disclosure.
7. Exercise at least one expected failure and recovery path.
8. Exercise one task-bound/project case and one reusable/managed case. Confirm
   uncertainty selects project scope, one graph stays in one scope, and repo
   routing metadata selects the specialized repo transaction.

Localize failures to the affected workflow step, generated skill/link, evidence
mapping, or fixture. Repair only that portion and rerun affected checks plus
integration checks. Stop when strict gates pass or the approved budget is
exhausted; list soft-gate gaps as unresolved.

## Construction Record And Review

Record:

- Routing-decision and reusable-bundle specification revisions.
- Incoming capability matrix, uncovered contract, and recurrence evidence.
- Retained/excluded evidence with reasons.
- Generated files and parameterized graph contract.
- Checks, exact results, failures, repairs, and reruns.
- Budget/resource use, stop reason, assumptions, unsupported claims, and gaps.
- Meta-skill target, collisions, shadowing, user decisions, and later operating
  deployment contract.

Keep three approvals independent:

1. Reusable-bundle specification before material generation.
2. Exact meta-skill artifact before managed import.
3. Each later operating graph revision, scope, and destination before import,
   unless that invocation explicitly pre-authorized auto-import into one named
   scope. Auto-import never authorizes overwrite.

For final artifact review, show the candidate id and description,
applicability, specification revision, file manifest, verification evidence,
unresolved gaps, exact managed destination, and current conflicting target.

## Import And Later Handoff

Keep review artifacts outside the runtime skill directory. For an approved
meta-skill import, use `../scripts/import_meta_skill.mjs`. It locks, re-reads the
target, stages and validates the runtime bundle, atomically installs it, and
rolls back failed replacement. Add `--overwrite` only after separate approval;
the helper refuses to convert an operating or unclassified target into `meta`.

Require the generated workflow to use the visible
`distill-ml-knowledge/scripts/import_operating_skill_graph.mjs` for approved
ordinary operating graphs. It must pass every top-level root in one command and
use the selected project or managed scope. Repo-to-skills output instead uses
`verify-repo-skill/scripts/import_repo_skill.mjs`, which owns the nested install,
sibling router rebuild, and rollback.

Each later construction run writes `researcher-handoff.md` with the normalized
task, source/version, selected scope, exact imported paths, skill ids, graph
entry point, verification evidence, unresolved limits, and suggested Researcher
starting prompt. Chat history is not part of the handoff.
