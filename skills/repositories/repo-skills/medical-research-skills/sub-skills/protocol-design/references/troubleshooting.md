# Protocol-design troubleshooting

Use this page to recover from an unstable or over-claimed protocol plan.
Symptoms and causes should be recorded in the handoff rather than hidden by
adding complexity.

| Symptom | Likely cause | Recovery |
|---|---|---|
| The request is a broad topic with many interesting analyses but no main question. | Aim sprawl or topic/aim confusion. | Ask for population/model, exposure/intervention, comparator, primary outcome, and time horizon. Reduce to one coherent primary aim; mark the rest exploratory or defer them. |
| Two or more “primary” endpoints or aims compete. | No primary estimand or an outcome hierarchy was not set. | Select the endpoint carrying the main claim; label others secondary/supportive and revisit multiplicity and power. |
| Cohort design has no clear index date or baseline window. | Exposure, eligibility, and follow-up are temporally mixed. | Define time-zero, pre-time-zero covariate window, risk-follow-up start/end, censoring, and competing events. Reclassify any post-baseline variable and review immortal-time/post-treatment bias. |
| EHR/claims/registry study claims causal treatment effects. | Convenience data were mistaken for a target trial. | Map eligibility, strategies, assignment moment, follow-up, outcome, contrast, and analysis. If key components or severity capture are missing, call it partially approximable or association-oriented and downgrade language. |
| A plan assumes fields, linkage, follow-up, or coding validity that the user has not confirmed. | Data-source capture was inferred from the database label. | Split the register into explicitly available, potentially obtainable, and unsupported. Add a data dictionary/validation task before locking the protocol. |
| The design says “control confounding” but names no variables or estimand. | Method-first planning or an implicit causal diagram. | State the target contrast and temporal role of variables. Separate necessary baseline confounders, effect modifiers, mediators, eligibility fields, and post-baseline process variables. Route implementation to data-analysis. |
| A sample-size answer produces one confident N from guessed inputs. | Unsupported effect size, event rate, variance, attrition, or model complexity. | Audit each input as known, uncertain, local, guessed, or missing-critical. Switch to scenario/range, event-driven, precision, fixed-N, or pilot framing; distinguish ideal from feasible enrollment. |
| Participants are counted but events, usable specimens, predictors, or validation cases are not. | Patient N was confused with the primary design driver. | Replan around events/usable samples/independent validation units; simplify endpoints, predictor burden, subgroup claims, or split discovery from validation. |
| Internal cross-validation is called external validation. | Validation tiers were collapsed. | Label internal resampling/holdout, temporal/site split, external cohort, orthogonal assay, functional, and translational evidence separately. State the claim supported by each. |
| “Validated” is used without stating what was validated. | Blanket validation language. | Replace with the tier and result: internally resampled, temporally replicated, externally evaluated, technically reproduced, or functionally supported. State remaining gaps. |
| A wet-lab, animal, organoid, or assay plan is specific despite weak biological context. | Translational ambition exceeded evidence and resources. | State the claim, model rationale, controls, feasibility, and oversight needs first. Keep experiments as candidate tiers until model/assay/resource facts are verified. |
| Biomarker/ML performance is high but protocol has no leakage or independent validation control. | Discovery and evaluation data were mixed or thresholds were tuned on the test set. | Lock preprocessing and thresholds within training folds, keep a truly held-out/temporal/site test set where possible, report calibration and spectrum, and downgrade transportability claims without independence. |
| Omics or multi-site results are unstable. | Batch, center, platform, multiplicity, or sample provenance is unresolved. | Predefine QC/batch handling, preserve sample splits, replicate on an independent platform/site when justified, and route computation and sensitivity analysis to data-analysis. |
| MR plan treats an IVW association as mechanism proof. | Instrument assumptions, ancestry, overlap, or pleiotropy were not audited. | Verify candidate GWAS types, instrument strength, harmonization, ancestry, overlap, pleiotropy, and directionality. Use IVW as primary only with proportional sensitivity; downgrade sparse/unstable signals to exploratory/follow-up priority. |
| An intervention or specimen protocol has no ethics path, privacy plan, or safety stop. | Scientific design was drafted without governance/operations. | Add IRB/REC/IACUC/biosafety/data-governance review, consent or waiver basis, PHI controls, participant burden, adverse-event/stopping rules, specimen handling, and named approval dependencies. Never claim approval. |
| Recruitment, staffing, lab/QC, or site capacity is assumed. | Feasibility was treated as a narrative afterthought. | List resource dependencies, readiness evidence, minimum viable design, contingency, decision date, and stop condition. Consider pilot framing rather than a nominal confirmatory claim. |
| Protocol request turns into statistical code, a fitted model, or polished manuscript. | Boundary crossed into execution or academic writing. | Preserve design decisions and hand off: **data-analysis** for schemas/code/fitting; **academic-writing** for methods, grants, reporting, or submission prose. |
| Literature, registry, event-rate, guideline, or dataset claims are needed but unverified. | Evidence retrieval was skipped. | Route to **evidence-insight** for search, source verification, evidence grading, and citation integrity. Keep current protocol statements as assumptions or candidate resources. |

## Stop conditions

Stop or return a provisional design when any of the following prevents a
credible primary claim:

- population, exposure/intervention, outcome, or temporality cannot be stated;
- the primary endpoint cannot be operationalized or ascertained;
- the intended data/specimen/model platform is inaccessible or unverified;
- the minimum event/sample/validation resource is unknown and no feasibility
  plan is possible;
- ethics, privacy, biosafety, or participant-safety requirements are unresolved;
- a causal or clinical-deployment claim requires evidence the design cannot
  supply;
- a required analysis or validation backend is unavailable and no valid
  alternative is documented.

A provisional protocol must say what is missing, what assumption was used, who
must verify it, and what change would invalidate the current design. Do not
silently fill gaps with plausible-looking numbers, citations, or methods.

## Handoff questions

Before routing onward, answer:

1. What is the single primary claim and its estimand?
2. Which facts are verified versus assumed?
3. What is the principal design/bias threat and mitigation?
4. What is the minimum credible sample/event/validation package?
5. What ethics, privacy, safety, or feasibility gate remains?
6. Is the next action evidence retrieval, computation, writing, or operations?
