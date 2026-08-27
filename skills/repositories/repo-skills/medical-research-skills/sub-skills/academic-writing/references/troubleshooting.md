# Academic-writing troubleshooting

Use this as a diagnosis table. Preserve the user's evidence and report an
unresolved blocker instead of silently filling a gap.

## Input and evidence failures

| Symptom | Likely cause | Recovery |
|---|---|---|
| User asks for a full section from only a topic | Missing design, results, or source evidence | Ask for the study type, question, protocol/analysis summary, result hierarchy, and target format. Offer an outline or input checklist. |
| Results prose would require invented numbers | Missing result table, analysis report, or figure inventory | Stop full drafting; route computations to **data-analysis** and request verified estimates, denominators, and uncertainty. |
| Methods has unknown randomization, ethics, reagent, or software details | Protocol record is incomplete | Insert `[AUTHOR TO SPECIFY: ...]`; route design/ethics decisions to **protocol-design**. Never invent a default. |
| Discussion lacks prior literature | Sources were not supplied or retrieved | Use `[CITE: ...]`, restrict interpretation to the current Results, and route source discovery to **evidence-insight**. |
| Bare reference list supplied for integrity review | No claim-reference pairs or source text | Do not infer support from titles; request the manuscript passage and cited source abstracts/full text. |
| Reference lookup is network-incomplete | External metadata service unavailable | Mark verification `INCOMPLETE`; check supplied DOI/PMID locally and request author confirmation. Never report network failure as a clean pass. |

## Section and consistency failures

| Symptom | Likely cause | Recovery |
|---|---|---|
| Methods and Results disagree on variables, sample size, or analysis | Version drift or analysis changed after Methods drafting | Build a cross-section discrepancy list; treat the analysis output and protocol as evidence, then revise both sections with author approval. Route statistical ambiguity to **data-analysis**. |
| Results reads like a figure dump | No approved narrative hierarchy | Order descriptive setup, primary result, support, sensitivity/subgroup, and validation. If the order is unknown, use a structuring pass before prose. |
| Discussion introduces a new result or causal claim | Boundary drift | Remove the new result or move it to Results; apply strength-calibrated language and the claim ledger. |
| Review chapter has long unsupported paragraphs | Search/library stage was skipped or citations were reused | Pause writing, define chapter-specific searches, verify primary sources, and checkpoint the outline/library before continuing. |
| Abstract contradicts the manuscript | Abstract was drafted from memory or an old version | Rebuild from the final verified Results and record design, sample, endpoint, estimate, uncertainty, and limitation. |
| Table/figure numbers disagree with prose | Stale analysis export, manual transcription, or panel mismatch | Treat the analysis output as the source of numerical truth only after it is verified; re-export or route to **data-analysis**, then rerun all cross-checks. |

## Reporting and submission failures

| Symptom | Likely cause | Recovery |
|---|---|---|
| Wrong checklist selected | Guideline chosen from a label rather than study design | Reclassify the design. Use CONSORT for trials, STROBE for observational studies, PRISMA for systematic reviews/meta-analyses, TRIPOD for prediction models, STARD for diagnostic accuracy, ARRIVE for animal studies, CARE for case reports, or a justified hybrid. |
| Checklist says “compliant” but items cannot be located | Partial manuscript or superficial checklist completion | Reclassify each item as present, weak, missing, not applicable, or unclear and record section/page/line locations. Do not certify formal compliance. |
| Journal suggestion is unrealistic or policy details are stale | Scope/metrics inferred from memory | Score scope, field, design tolerance, evidence strength, practical constraints, and article type. Label metrics approximate and verify current official instructions. Never promise acceptance. |
| Preflight finds a placeholder, AI meta-comment, or AI author | Unchecked generated residue | Hold submission; remove or substantiate the item, correct authorship, and review the whole manuscript. Disclosure alone is not a fix. |
| arXiv/reference check cannot reach external services | Network or rate limit | Report the reference section as incomplete, keep local structural and cite-key checks, and rerun when connectivity is available. Do not silently skip. |
| Figure or supplement has an unlicensed image or copied text | Permission/provenance missing | Remove, replace, obtain documented permission, or cite the license. Do not submit copied publisher figures or reviewer material without authorization. |

## Privacy and double-blind failures

| Symptom | Likely cause | Recovery |
|---|---|---|
| Prompt or draft contains names, MRNs, exact dates, addresses, or free-text PHI | Raw clinical material was pasted into writing context | Stop and remove identifiers; use an approved de-identification workflow. Do not echo the PHI in the output. Preserve only the minimum aggregate or coded information needed. |
| Double-blind manuscript names authors, institution, site, funder, or repository | Title page was merged with blinded manuscript or self-identification was not scrubbed | Make separate title-page and blinded files; remove identifying acknowledgments, metadata, tracked changes, comments, and revealing links as required by the journal. Keep required confidential declarations in the submission fields. |
| Self-citation reveals the group or prior study | Citation wording or author name is identifying | Follow the journal's masking rule; do not falsify the citation. Mark the citation for blinded handling and restore full attribution at revision if required. |
| Patient image or case description remains identifiable | Consent or anonymization is insufficient | Do not publish or circulate it until consent, masking, and journal permissions are confirmed. Route image/data handling to the appropriate privacy or ethics process. |

## Peer review and grant failures

| Symptom | Likely cause | Recovery |
|---|---|---|
| Response letter says “we addressed this” without location | No change ledger | Add reviewer comment, response, exact manuscript change, and page/line or section location. If no change, give evidence-based rationale and acknowledge the limitation. |
| Reviewer requests a new analysis that was not prespecified | Scope or design change | Route feasibility, estimand, multiplicity, and interpretation to **data-analysis** and **protocol-design**; label post hoc work and avoid presenting it as confirmatory. |
| Grant aim promises an outcome rather than a test | Aim is not falsifiable or lacks fallback | Rewrite as objective → hypothesis → approach → measurable outcome → decision point → alternative. Verify feasibility and power with **protocol-design**/**data-analysis**. |
| Grant cites preliminary data that are not supplied | Unsupported feasibility claim | Remove or label the missing evidence; do not fabricate pilot counts or effect sizes. Route literature support to **evidence-insight**. |

## Stop conditions and handoff

Stop and report `BLOCKED` when any of the following remains unresolved:

- identifiable or unauthorized private information is in the working material;
- a required number, result, citation, ethics statement, or author identity is
  missing and cannot be verified;
- a required backend analysis or source retrieval is unavailable;
- the target journal/funder's current rules are essential but not available;
- double-blind masking conflicts with a mandatory disclosure and the venue's
  policy is unknown.

A useful handoff names: the blocked artifact, evidence checked, exact missing
input, severity, safe next action, and owning route (**evidence-insight**,
**data-analysis**, or **protocol-design**).
