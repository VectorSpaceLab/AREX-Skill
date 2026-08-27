# Academic-writing workflows

Read this reference after the intake gate in `SKILL.md`. It is a routing and
quality-control guide, not a substitute for the author's data, protocol,
source papers, journal instructions, or funder notice.

## 1. Select the artifact and evidence boundary

Capture a short work order:

| Field | Required decision |
|---|---|
| Artifact | section, full manuscript, narrative/systematic review, abstract, visual text, response letter, submission package, or grant |
| Study type | RCT, cohort, case-control, cross-sectional, diagnostic, prediction, review, animal, in-vitro, qualitative, or hybrid |
| Evidence | protocol, analysis report, result hierarchy, figures/tables, source papers, reviewer comments, or preliminary data actually supplied |
| Target | journal/funder, article format, audience, word/character limit, language, and declarations |
| Status | draft, revision, resubmission, preprint, or double-blind submission |

State `ready`, `partially ready`, or `not ready`. A vague topic is not enough
for a full Methods, Results, or Discussion draft. A bare reference list is not
enough for an integrity review. A title or abstract alone is not enough to
certify reporting compliance.

## 2. Manuscript sections

### Introduction

Build background → evidence gap → study objective/hypothesis → contribution.
Keep background claims tied to supplied or verified sources. If the gap is not
supported, route the search or evidence-map task to **evidence-insight**.
Do not present the study's results in the Introduction.

### Methods

Convert the protocol and actual analysis record into reproducible prose:

1. design, setting, dates, oversight, registration, and consent;
2. participants/samples, eligibility, recruitment, exclusions, and sample size;
3. intervention/exposure, comparator, procedures, equipment/reagents, and
   measurement instruments;
4. primary/secondary outcomes and timing;
5. randomization, allocation concealment, and blinding when applicable;
6. statistical model, estimand, assumptions, missing-data handling, multiplicity,
   sensitivity/subgroup analyses, software/version, and data availability.

If an item is unknown, mark it for the author. Route unresolved design,
endpoint, power, randomization, or ethics decisions to **protocol-design** and
route computations or missing statistical outputs to **data-analysis**. Check
that every analysis appearing in Results has a Methods counterpart.

### Results

Require a clear result hierarchy, analysis summary, or figure inventory before
writing full prose. Use descriptive setup → primary findings → supporting
analyses → sensitivity/subgroup analyses → validation. Report denominators,
effect estimates, uncertainty, and exact figure/table references supplied by
the author. Keep interpretation out of Results, do not promote exploratory
findings, and present null results with effect size and confidence interval—not
only a p-value. If the hierarchy is unclear, structure first rather than
polishing incomplete evidence.

### Discussion and conclusion

Use: principal finding → interpretation → comparison with supplied literature
→ implications proportional to evidence → limitations with impact and mitigation
→ conclusion tied to the research question. Do not introduce new data, cite
invented studies, or turn an association into a mechanism or recommendation.
When prior literature is missing, use explicit citation placeholders and route
source retrieval to **evidence-insight**.

## 3. Reviews and abstracts

### Narrative or long-form medical review

Use a stateful sequence: scope and audience → detailed outline with subheadings
→ search/library plan → source verification → chapter drafting → chapter audit
→ conclusion → structured abstract → formatting. Keep a source ledger and
checkpoint before major stages. Mark review claims with traceable citations;
do not use the review itself as if it were primary evidence when a primary
source is needed. Do not cite the abstract or conclusion merely to inflate
coverage if the evidence does not support it.

### Systematic or scoping review

Confirm eligibility criteria, information sources, dates, complete search
strategy, screening and extraction process, risk-of-bias method, synthesis,
registration/protocol, and certainty assessment where relevant. Route missing
search design or eligibility decisions to **evidence-insight** or
**protocol-design**. Never fabricate counts in the flow diagram.

### Abstract, title, highlights, or lay summary

Start from the verified manuscript, not from a topic alone. Preserve design,
population, sample size, primary outcome, key estimate/uncertainty, and evidence
limits. Adapt structure and word count to the target venue; do not add a result
that is absent from the Results. An abstract or conclusion normally carries no
citation unless the venue explicitly requires it and the source is supplied.

## 4. Figures, tables, and supplements

For each item, verify: unique label, title/legend, population and denominator,
units, statistical notation, abbreviations, sample size, uncertainty, panel
order, colors/symbols, and a matching in-text callout. A figure legend should
make the visual interpretable without claiming more than the analysis. A table
narrative should highlight the message and not repeat every cell. Ask
**data-analysis** to regenerate or validate values and plots; ask
**protocol-design** when an endpoint or analysis definition is unclear.

Check that:

- numbers agree across figure, table, Results, abstract, and supplement;
- confidence intervals, p-values, and correction methods are identified;
- representative images disclose scale bars, replicates, and selection rules;
- flow diagrams account for exclusions and missing participants;
- accessibility, file format, resolution, permissions, and color limitations
  follow current journal instructions;
- patient images, pedigrees, screenshots, and genomic data are de-identified
  and have appropriate consent or controlled-access handling.

## 5. Citations, reporting, and submission adaptation

Use the claim ledger in `citations-and-integrity.md`. Select reporting guidance
from the actual study design: commonly CONSORT for trials, STROBE for
observational studies, PRISMA for systematic reviews/meta-analyses, TRIPOD for
prediction models, STARD for diagnostic accuracy, ARRIVE for animal work, CARE
for case reports, and other appropriate extensions. A hybrid study may require
more than one framework. Record each item as present, weak, missing, not
applicable, or unclear and give the manuscript location.

For a target journal, first compare scope and design tolerance, then structure,
word limits, abstract headings, reference style, figure/table limits,
reporting-checklist requirements, data/ethics declarations, and blind-review
rules. Journal metrics, acceptance patterns, and policies are time-sensitive;
use only current official instructions for final submission decisions.

## 6. Peer review, revision, and resubmission

Create a comment ledger with reviewer, location, issue type, requested action,
evidence needed, response, manuscript change, and page/line or section
location. Triage comments as scientific/design, analysis, reporting, clarity,
format, or disagreement. Respond point by point: quote or paraphrase the
comment, thank the reviewer without overclaiming, state the action, show the
exact change location, and explain a respectful non-change with evidence when
necessary. Route design or analysis requests to **protocol-design** or
**data-analysis** rather than masking an unresolved issue with prose.

For a rebuttal, check that citations directly support the response and that the
response does not claim a new analysis unless it was actually performed. Re-run
consistency, reference, reporting, and double-blind checks after revisions.

## 7. Grants and specific aims

For a grant, separate significance/need, gap, objective, central hypothesis,
innovation, aims, approach, feasibility/preliminary evidence, risks and
alternatives, milestones, team/resources, rigor/reproducibility, inclusion,
ethics, and dissemination. Each aim should have a testable outcome and a
credible fallback. Use only supplied preliminary data; mark missing evidence.
Route hypothesis, endpoint, sample-size, design, and feasibility choices to
**protocol-design**; route power or analysis plans to **data-analysis**; route
literature support to **evidence-insight**. Match the current agency notice
and page/budget rules rather than relying on a generic template.

## Evidence basis used for this route

This route distills the repository README's Academic Writing map and the
representative `medical-review-writer-architect`, `methods-section-writer`,
`results-section-writer`, `discussion-composer`, `reference-integrity-checker`,
`reporting-guideline-compliance-checker`, `arxiv-preflight`, and
`target-journal-matcher` evidence. Their common verified behaviors are:
clarification before long-form drafting, explicit placeholders instead of
fabrication, section boundaries, source-to-claim matching, severity-aware
reporting checks, location-specific preflight findings, and fit-based journal
triage.
