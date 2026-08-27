---
name: academic-writing
description: "Supports evidence-disciplined medical manuscript, review,
  abstract, figure, table, submission, peer-review, and grant writing without
  fabricating data, citations, or compliance."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Academic Writing

Use this route for medical or biomedical manuscripts and reviews: planning or
revising IMRaD sections, structured abstracts, figures and tables, citation
integrity, reporting checklists, journal adaptation, peer-review responses,
submission preflight, and grant components. The researcher remains the author
and must approve every scientific claim.

## Intake gate

Before drafting, establish:

- artifact: full manuscript, review, section, abstract, figure/table text,
  response letter, submission package, or grant;
- study/review type, research question, evidence available, and target audience;
- target journal or funder, format, word limit, declarations, and deadline;
- whether data, source papers, references, figures, and reviewer comments are
  actually supplied; record missing items rather than inferring them;
- privacy status and whether the package is double-blind. Do not request or
  reproduce identifiable patient information.

If the evidence is insufficient, ask focused questions or produce an outline,
input checklist, or marked partial draft—not plausible-looking prose.

## Route the work

1. Read [workflows.md](references/workflows.md) for the artifact-specific
   workflow and handoffs.
2. Use the claim ledger and source-fit tests in
   [citations-and-integrity.md](references/citations-and-integrity.md).
3. Apply [troubleshooting.md](references/troubleshooting.md) when inputs,
   privacy, blinding, references, figures, reporting checklists, or submission
   constraints fail validation.
4. For a long review, use staged outline → evidence search/library →
   chapter-by-chapter drafting → verification → abstract/conclusion → format;
   preserve intermediate state and obtain author checkpoints.
5. For Methods, Results, and Discussion, keep boundaries explicit: Methods
   reports what was done, Results reports what was observed, and Discussion
   interprets only those results in light of supplied literature.

## Non-negotiables

- Never invent participants, outcomes, effect sizes, p-values, software,
  ethics IDs, approvals, citations, reviewer facts, grant preliminary data, or
  journal policy. Use `[AUTHOR TO SPECIFY: ...]`, `[CITE: ...]`, or an
  uncertainty note when necessary.
- Match claim strength to design and evidence: association is not causation;
  exploratory, animal, in-vitro, single-center, or unvalidated findings must
  not be generalized into clinical certainty.
- Identify the applicable reporting framework from the actual design. Use a
  hybrid review when necessary rather than falsely certifying one checklist.
- Do not rewrite or silently alter numerical results, denominators, figure
  labels, reference identities, or author contributions. Check consistency
  across title, abstract, Methods, Results, Discussion, tables, figures, and
  supplements.
- For journal recommendations, rank scope/design/evidence fit and label current
  metrics as approximate; verify live instructions and policies on the official
  journal or funder site. Never predict acceptance.
- For submission, remove PHI and local identifiers. For double-blind review,
  separate title-page metadata and scrub names, institutions, acknowledgments,
  self-identifying phrasing, file metadata, and revealing repository links as
  the journal requires; do not conceal mandatory ethics or conflict disclosures
  from the confidential submission fields.

## Handoffs

- Route literature retrieval, evidence maps, source appraisal, and replacement
  citations to **evidence-insight**; return with traceable source records.
- Route statistical computation, data cleaning, model fitting, uncertainty,
  and figure generation to **data-analysis**; this skill reports supplied
  outputs but does not manufacture analyses.
- Route study design, endpoints, randomization, power, eligibility, protocol,
  and ethics planning to **protocol-design** before writing Methods or grants.
- After a stable Results section, hand the evidence boundary to Discussion;
  after a compliance or integrity review, revise the owning section and rerun
  the relevant check.

## Output contract

Deliver the requested artifact plus a compact audit note: inputs used, study or
reporting framework selected, claims or values left unresolved, citation and
privacy checks, journal/funder assumptions, and next handoff. Stop and report a
gap when verification cannot be completed.
