# Generation, Verification, And Review

Run these stages only after approval of an exact reusable-bundle specification
for the `design-reusable` construction strategy selected by
`distill-ml-knowledge`. The candidate is Creator infrastructure; its later
invocations produce operating graphs.

## Knowledge Exploration

Resolve only evidence permitted by the approved future-anchor contract. Map each
proposed workflow capability in `Q` to retained evidence in `X`, expected
operating output, validation, and recovery. Record exclusions, conflicts,
missing support, inaccessible evidence, and assumptions. Machine-specific paths
belong only in the construction record and must not enter the reusable runtime
bundle.

## Meta-Skill Generation

Generate a candidate workflow that later turns caller-supplied anchors into
`G_tilde = (S_tilde, L_tilde)` and, after verification, `G = (S, L)`. Require it
to define:

- triggering description, supported anchor classes, applicability, and
  non-applicability;
- scope behavior for task-agnostic source anchors and task-oriented
  `tau = (q, D, E, g)` anchors;
- parameterized source/evidence inputs, construction constraints, and approval
  points;
- ordered scope, ground, construct, and verify stages with intermediate
  artifacts, stop conditions, and recovery;
- coherent operating-skill boundaries plus explicit routing, dependency,
  composition, and relative-reference links;
- provenance and construction-record requirements for `X`, `G_tilde`, `G`, and
  `R`;
- static, executable, source-support, graph-integration, representative-use,
  task-level when applicable, and human-review gates;
- post-verification project/managed classification that defaults uncertainty to
  project scope and keeps a complete graph in one scope;
- exact-path import review, the correct locked importer, and Researcher
  handoff.

Declare `metadata.disco-role: meta` on the meta skill and all meta sub-skills.
Do not include `agents/` or `agents/openai.yaml` in their runtime trees. Require
`metadata.disco-role: operating` on every generated operating root, router, and
sub-skill. Keep operating routers model-visible when routing requires it and use
`disable-model-invocation: true` on generated repo roots/sub-skills when their
deployment contract requires progressive disclosure.

## Verification And Refinement

Apply the approved bundle-verification gates:

1. Parse all frontmatter and enforce exact role values, identifiers, and links.
2. Validate source/evidence parameterization, required artifacts, graph
   boundaries, and absence of target-specific agent manifests.
3. Search for credentials, machine-specific paths, transient task state, and
   runtime dependencies on construction sources.
4. Exercise one task-agnostic source anchor and one task-oriented task anchor
   with source discovery.
5. Exercise at least one source/access failure with recovery and one graph
   verification failure with local repair.
6. Inspect claims for source support, applicability limits, and adequate
   progressive disclosure.
7. Exercise one task-bound/project deployment and one self-contained/managed
   deployment. Confirm uncertainty selects project scope, one graph stays in one
   scope, and repo routing metadata selects the specialized repo transaction.

Localize failures to the affected workflow step, generated node/link, evidence
mapping, or fixture. Repair only that portion and rerun the affected checks plus
integration checks. Stop when strict gates pass or the approved budget is
exhausted; list soft-gate gaps as unresolved.

## Construction Record And Review

Record in `R`:

- routing and reusable-bundle specification revisions;
- incoming `z`, distillation form, `Q`, uncovered construction gap, and
  recurrence evidence;
- retained/excluded/conflicting `X` with reasons;
- generated files and parameterized future graph contract;
- checks, exact results, failures, repairs, and reruns;
- resource use, stop reason, assumptions, unsupported claims, and gaps;
- meta-skill target, collisions, shadowing, user decisions, and later operating
  deployment contract.

Keep approvals independent:

1. Reusable-bundle specification before material generation.
2. Exact meta-skill artifact before managed import.
3. Each later operating graph's revision, scope, and destination before import,
   unless that invocation explicitly pre-authorized auto-import into one named
   scope. Auto-import never authorizes overwrite.

For final artifact review, show candidate id and description, anchor
applicability, specification revision, file manifest, verification evidence,
unresolved gaps, exact managed destination, and current conflicts.

## Import And Later Handoff

Keep review artifacts outside the runtime skill directory. For an approved meta
bundle, use `../scripts/import_meta_skill.mjs`; it stages, validates, atomically
installs, and rolls back failed replacement. Add `--overwrite` only after
separate approval.

Require later operating-graph construction to use
`../distill-ml-knowledge/scripts/import_operating_skill_graph.mjs` for ordinary
graphs, passing all top-level roots in one command and using one approved scope.
Repo output uses `../verify-repo-skill/scripts/import_repo_skill.mjs`, which owns
the nested install, sibling-router rebuild, and rollback.

Each later run writes `researcher-handoff.md` with anchor kind, distillation
form, `z` or `tau`, `Q`, `X` provenance, accepted/unverified `G`, `R` path,
selected scope, exact imported paths, graph entry point, verification evidence,
and unresolved limits. Chat history is not part of the handoff.
