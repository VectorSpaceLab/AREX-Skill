# Citations and claim integrity

Read this reference whenever prose contains external facts, comparisons,
mechanistic explanations, methodological justification, reviewer rebuttals, or
submission-integrity concerns. A citation is evidence only when the cited source
supports the exact claim.

## Claim ledger

Maintain one row per material claim:

| ID | Manuscript location | Claim text | Claim class | Source | Match status | Allowed wording | Action |
|---|---|---|---|---|---|---|---|
| C1 | section/line | exact sentence | observed / interpreted / external / methodological | primary source, review, guideline, or none | verified / partial / mismatch / unavailable | strength-calibrated wording | keep, narrow, replace, or verify |

For a manuscript-wide pass, prioritize the Introduction, Discussion,
limitations, clinical/translational implications, Methods justifications,
response letters, and any sentence that changes the perceived evidence level.

## Five-axis source-fit test

A source supports a claim only after checking:

1. **Population/context** — same population, setting, species, assay, or review
   eligibility; do not generalize animal or in-vitro work to patients without
   explicit evidence.
2. **Exposure/intervention/domain** — same intervention, exposure, biomarker,
   diagnostic test, outcome, or method.
3. **Evidence level** — primary study, synthesis, guideline, protocol, or
   editorial is used for the role it can support.
4. **Direction** — the source's result agrees with the manuscript's direction,
   including null or conflicting findings.
5. **Inference strength** — association, prediction, mechanism, causation,
   safety, efficacy, and clinical recommendation are not interchangeable.

Topical similarity or a matching title is not verification. If the source text
or reliable metadata is unavailable, label the assessment `unclear` and request
the abstract/full text; do not certify the citation.

## Strength calibration

| Evidence actually available | Safer language | Avoid unless separately supported |
|---|---|---|
| descriptive observation | “was observed,” “was higher/lower in this sample” | “caused,” “proves,” “benefits” |
| association | “was associated with,” “was consistent with” | “led to,” “determined,” “mechanism” |
| prediction model | “predicted” within the validated population | “improves outcomes,” clinical utility without evaluation |
| exploratory/subgroup result | “exploratory,” “hypothesis-generating” | presenting as the primary prespecified finding |
| animal/in-vitro evidence | “supports a possible mechanism” | clinical efficacy or human safety claim |
| single-center/retrospective study | “in this setting/cohort” | broad population or causal generalization |
| RCT result | effect estimate with CI and population/context | claims beyond endpoint, follow-up, or comparator |
| systematic review | “the included evidence suggests…” with heterogeneity/quality | treating a heterogeneous synthesis as certainty |

Use `[CITE: specific evidence needed]` when a literature claim lacks a source.
Use `[AUTHOR TO SPECIFY: ...]` for missing study facts. Do not fill either
placeholder with a guessed reference or value.

## Common integrity failures

- **Mismatch:** source studies a different population, endpoint, intervention, or
  design than the sentence implies.
- **Overextension:** a source reports association but prose states causality, or
  a narrow sample is generalized to all patients.
- **Quote/paraphrase drift:** paraphrase is stronger, broader, or more certain
  than the source; verify the original wording rather than trusting a review.
- **Second-hand citation:** a review or technical report is cited for a result
  that should be checked in the underlying primary study.
- **Citation stacking:** many references are placed after one sentence without
  showing which source supports which proposition. Split the sentence or map
  citations to distinct claims.
- **Reference identity failure:** title, authors, year, DOI, PMID, or cite key
  does not resolve consistently. Treat an unmatched reference as unresolved,
  not as evidence of fabrication until metadata is checked.
- **Result/source conflation:** a manuscript's own finding is cited as though
  an external paper established it, or an external context claim is presented
  as if observed in the current dataset.

## Severity and correction

- **Major:** fabricated/unverifiable reference presented as real; causal or
  clinical claim unsupported by the cited design; animal-to-human or other
  material population overreach; citation used in a high-stakes rebuttal to
  defend a claim it does not support. Directly verify or remove, then narrow
  the prose.
- **Moderate:** partial population/endpoint fit, second-hand use where a primary
  source is available, important claim with only weak support, or unresolved
  metadata affecting interpretation. Replace or qualify before submission.
- **Minor:** citation placement, under-specific background source, style issue,
  or a source that is adequate but not ideal. Fix after material risks.
- **Unclear:** source text or network verification is unavailable. State the
  limitation and request the source; do not downgrade uncertainty to a pass.

Order findings by severity, then manuscript location. Explain why the issue
could mislead readers or invite reviewer criticism. Separate citation hygiene
from substantive integrity.

## Reporting-guideline integrity

A checklist cannot repair missing science. Determine the design first, then
check the relevant framework and extensions. For each item, record:

- present and sufficiently detailed;
- present but weak or not locatable;
- not reported;
- not applicable with a reason; or
- unclear because the manuscript material is missing.

Do not claim “CONSORT/STROBE/PRISMA/TRIPOD compliant” from an abstract or a
partial Methods section. A prospective cohort with a prediction model may need
both STROBE and TRIPOD coverage. A diagnostic review may combine review and
diagnostic reporting considerations. Report the checklist location and the
correction priority.

## Submission and privacy integrity

Before sharing or submitting:

- remove names, initials, dates that can identify a person, medical record
  numbers, addresses, accession keys, screenshots, and free-text PHI;
- preserve reproducible de-identified denominators and a controlled mapping
  only in an authorized system, never in the writing prompt;
- confirm consent and permissions for identifiable images, pedigrees, case
  details, datasets, and third-party figures;
- for double-blind review, inspect document properties, tracked changes,
  comments, acknowledgments, self-citations, institution names, repository
  URLs, trial/site descriptions, and file names. Follow the venue's exact
  masking policy and retain required declarations in the proper confidential
  fields;
- an AI-use statement may be required by the venue or field, but disclosure
  does not cure fake references, placeholders presented as results, or
  unchecked claims. AI tools cannot be authors and the human authors retain
  responsibility.

## Minimal final audit

Before delivery, confirm that every major claim has a source or is explicitly
identified as an observation from supplied data; every citation has matching
scope and strength; every number agrees across sections and visuals; every
placeholder is visible; unresolved sources are listed; and privacy/blinding
checks were performed or marked incomplete.
