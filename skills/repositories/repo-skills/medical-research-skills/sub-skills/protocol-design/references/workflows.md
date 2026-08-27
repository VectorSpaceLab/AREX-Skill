# Protocol-design workflows

Use this reference after [SKILL.md](../SKILL.md) identifies protocol planning as
the dominant task. It distills the catalog's core design routes; it is
self-contained and does not require the source checkout.

## 1. Intake and framing

Capture the minimum protocol record before selecting methods:

| Field | Required question | If unknown |
|---|---|---|
| Scientific question | What population/model, exposure/intervention, comparator, and outcome are being related? | Ask before locking the design. |
| Objective | Is the goal descriptive, explanatory, predictive, prognostic, causal-leaning, translational, or feasibility/pilot? | Downgrade claims and label assumptions. |
| Primary estimand | What contrast, association, prediction performance, or mechanism-support statement is primary? | Do not let secondary analyses drive planning. |
| Setting/data | Which sites, cohort, specimens, assay platform, registry/EHR/claims source, or GWAS architecture are actually available? | Mark capture and access unverified. |
| Time | What is time-zero and the outcome horizon/follow-up? | Stop if temporality cannot be defended. |
| Constraints | Recruitment, events, specimens, personnel, budget, privacy, hardware, and validation resources? | Use feasibility-bounded planning. |

Frame one primary aim, a limited set of supporting secondary aims, and clearly
labeled exploratory work. An aim that could be a separate paper or study is
usually not a secondary aim in the same protocol.

## 2. Design-family selection

| Question pattern | Lead route | Design-defining checks |
|---|---|---|
| Manipulated intervention or controlled experiment | Experimental protocol | Allocation, intervention fidelity, controls, safety, blinding, primary outcome, stopping rules. |
| Exposure/predictor precedes future clinical outcome | Cohort/prognostic protocol | Source population, eligibility, time-zero, baseline variables, follow-up, censoring, endpoint ascertainment. |
| Routine-care treatment, safety, utilization, or comparative effectiveness | RWE protocol | EHR/claims/registry capture, new-user/comparator logic, target-trial components, switching and confounding. |
| Outcome-defined comparison | Case-control route | Case definition, control source, index date, exposure ascertainment, selection and recall bias. |
| Test/model performance | Diagnostic/prognostic validation route | Index test, reference standard, threshold, calibration/discrimination, spectrum, split and independent validation. |
| Mechanism translated across model systems | Translational route | Claim chain, model relevance, orthogonal evidence, assay/perturbation feasibility, transfer limits. |
| High-dimensional molecular data | Omics/integration route | Sample/data provenance, batch structure, pre-specification, leakage control, replication and biological interpretation. |
| Genetic instruments and GWAS summary data | MR/genetic route | Exposure/outcome direction, IV relevance, ancestry, overlap, pleiotropy, harmonization, sensitivity and claim boundaries. |

If more than one family fits, name a lead family and the reason an alternative
was not selected. Do not turn a question into a cohort merely because records
exist, or into an MR study merely because a causal phrase was used.

## 3. Core protocol build sequence

1. **Question and aim:** write the population, intervention/exposure, comparator,
   outcome, time horizon, estimand, primary hypothesis, and confirmatory versus
   exploratory status.
2. **Population and eligibility:** define target population versus source
   population, inclusion/exclusion criteria, repeat-entry rules, recruitment or
   sampling frame, and subgroup rules. Eligibility is not an after-the-fact
   analysis subgroup.
3. **Time-zero and exposure:** define index/assignment date, allowable baseline
   window, exposure or intervention definition, washout/new-user rule when
   relevant, comparator, and what is post-baseline.
4. **Endpoints and follow-up:** operationalize one primary endpoint and limited
   secondary endpoints; specify ascertainment, timing, fixed horizon versus
   time-to-event/recurrent/longitudinal structure, censoring, loss to follow-up,
   competing events, and missingness.
5. **Analysis line:** name the primary estimand and model family only after the
   endpoint structure is known. State adjustment set, subgroup/interactions,
   multiplicity, sensitivity analysis, and missing-data strategy at a level the
   data can support. Route code and fitting to **data-analysis**.
6. **Power and feasibility:** select binary, continuous, time-to-event,
   matched/clustered, prediction, validation, or precision logic. Audit effect
   size, event rate/variance, allocation/exposure prevalence, attrition,
   predictors, and feasible N as known, uncertain, locally estimated, guessed,
   or missing. Use scenarios rather than false precision.
7. **Validation:** tie validation to the primary claim. Classify internal,
   temporal/site/external, orthogonal/technical, functional, and translational
   layers as necessary, recommended, optional, or not justified.
8. **Ethics and operations:** document risk/benefit, consent or waiver basis,
   privacy/de-identification, data governance, vulnerable populations, specimen
   handling, biosafety, intervention safety, recruitment burden, staffing,
   site readiness, monitoring, and stop/escalation conditions. Do not claim
   approval.
9. **Decision and handoff:** provide a minimum credible design, upgrades,
   unsupported claims, unresolved questions, and the next route.

## 4. Specialist routes represented by the catalog

- **Aims/hypotheses:** convert a broad idea into one primary aim, subordinate
  aims, testable hypotheses, and an exploratory boundary. Use when the study
  story is not yet coherent.
- **Clinical cohort:** use for retrospective/prospective cohorts; emphasize
  time-zero, enrollment, follow-up, endpoint ascertainment, baseline versus
  post-baseline variables, and a single primary analysis line.
- **Sample size/power:** use when the design and endpoint are known enough to
  audit assumptions. It should return formal, range-based, event-driven,
  precision, fixed-N, or pilot framing—not an unsupported single N.
- **Validation strategy:** use to plan internal resampling/holdout, temporal or
  site split, external cohort, orthogonal platform, functional, and translational
  evidence without conflating tiers.
- **RWE:** use for EHR, claims, or registry studies. Define target/source
  population, index date, exposure episode, comparator, outcomes, censoring,
  capture gaps, and whether target-trial emulation is recommended, partial, or
  not appropriate.
- **Mendelian randomization:** use for GWAS-based genetically proxied causal
  questions. Define direction, candidate data types, instrument and ancestry
  rules, overlap and pleiotropy risks, IVW-led analysis, sensitivity ladder,
  and evidence/claim downgrade rules.

Specialized biomedical routes (biomarker, omics, single-cell, QTL/
colocalization, pharmacovigilance, network pharmacology, animal/cell,
translational, treatment-response, and multi-omics) remain subordinate to the
same question → design → endpoint → validity → feasibility → validation chain.
Do not infer a dataset, assay, model system, code package, or external cohort
just because the route name suggests one.

## 5. Standard deliverable

Return a protocol planning memo with:

1. question, target population, objective, estimand, and assumptions;
2. primary/secondary/exploratory aim hierarchy and hypotheses;
3. selected design and rejected alternatives;
4. eligibility, time-zero, exposure/intervention, comparator, follow-up, and
   endpoints;
5. variables and causal/measurement role, with baseline discipline;
6. bias/confounding and missingness controls;
7. primary analysis line and multiplicity/sensitivity concepts;
8. sample-size/power stance and scenario assumptions;
9. validation ladder and claim boundary;
10. translational, ethics, privacy, safety, and feasibility assessment;
11. minimum credible plan, upgrades, stop conditions, unresolved questions;
12. downstream handoff to evidence-insight, data-analysis, academic-writing, or
    operations-and-audit.

The final memo should distinguish **known**, **supported but uncertain**,
**locally estimated**, **guessed**, and **missing-critical** facts. Evidence
retrieval, citations, statistical code, and regulatory submission writing are
separate workflows.
