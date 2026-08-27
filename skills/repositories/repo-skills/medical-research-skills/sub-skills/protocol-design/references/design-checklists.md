# Protocol design checklists

Use these gates before calling a design execution-ready. A checked item means
that the protocol states the decision or explicitly marks it as unknown; it does
not mean the design is clinically approved or scientifically proven.

## Aims and hypotheses

- [ ] State one specific primary question and one primary aim.
- [ ] Define population/model, exposure/intervention, comparator, outcome, and
      time horizon.
- [ ] Make every formal hypothesis testable, directional only when justified,
      and tied to an estimand.
- [ ] Label aims as confirmatory, supportive, exploratory, descriptive, or
      hypothesis-generating.
- [ ] Remove overlapping aims, endpoint drift, rhetorical claims, and hidden
      dependencies.
- [ ] Keep secondary aims subordinate; downgrade analyses that would require a
      separate study identity.

## Study architecture and eligibility

- [ ] Name the lead design family and why it fits temporal and evidentiary logic.
- [ ] Identify target population, source population, setting, sampling frame,
      recruitment/access route, and generalizability target.
- [ ] Write inclusion and exclusion criteria as observable rules.
- [ ] Separate eligibility from analysis subgroup, effect modifier, and
      post-baseline classification.
- [ ] Define repeat episodes/entries, washout, enrollment period, and baseline
      assessment window.
- [ ] For trials/experiments, specify allocation, control, intervention fidelity,
      blinding where feasible, safety monitoring, and stopping/escalation rules.
- [ ] For specialized designs, name the required data/specimen/model platform
      and mark it unavailable until confirmed.

## Time-zero, exposure, endpoints, and follow-up

- [ ] Give one defensible index/assignment date and define what is known before
      or at that date.
- [ ] Define exposure/intervention, comparator, initiation, switching,
      discontinuation, dose/intensity, or instrument rules as applicable.
- [ ] Do not adjust for post-baseline mediators or consequences as baseline
      confounders without an explicit estimand and bias review.
- [ ] Operationalize one primary endpoint: event/threshold, measurement,
      ascertainment source, timing, and adjudication rule.
- [ ] Define limited secondary endpoints and mark recurrent, longitudinal,
      competing-risk, binary, continuous, or time-to-event structure.
- [ ] Specify follow-up start/end, observation horizon, censoring, loss to
      follow-up, competing events, and data truncation.
- [ ] Confirm that endpoint measurement is feasible, valid enough for the claim,
      and not merely convenient.

## Bias, confounding, and interpretation

- [ ] Draw or describe the causal/measurement logic before selecting adjustment
      variables.
- [ ] Review selection bias, confounding by indication, time-varying
      confounding, immortal-time bias, collider/overadjustment, and residual
      confounding where relevant.
- [ ] Review exposure, outcome, assay, coding, and reference-standard
      misclassification.
- [ ] Check missingness, informative censoring, center/site effects, batch
      effects, spectrum, linkage, ancestry, overlap, and transportability.
- [ ] State model assumptions (for example proportional hazards, linearity,
      exchangeability, positivity, calibration, or valid instruments) rather
      than implying they hold.
- [ ] Keep association, prediction, causal, mechanism, and clinical utility
      language distinct.
- [ ] Pre-specify a main analysis line, key sensitivity analyses, subgroup
      limits, and multiplicity stance; route implementation to data-analysis.

## Sample size, power, and feasibility

- [ ] Let the primary endpoint/estimand—not exploratory endpoints—drive planning.
- [ ] Choose the correct family: binary, continuous, time-to-event/events,
      matched/clustered, repeated-measures, prediction development, external
      validation, or precision.
- [ ] Audit effect size, event rate/prevalence, variance, allocation/exposure
      ratio, follow-up, attrition, usable samples, predictors, clustering, and
      subgroup size.
- [ ] Label every input: directly known; literature-supported but uncertain;
      local estimate; guessed; or missing-critical.
- [ ] Distinguish participants from events, ideal N from feasible N, and model
      development from validation adequacy.
- [ ] Provide optimistic/base/conservative/feasibility-bound scenarios when
      uncertainty is material.
- [ ] Downgrade to range-based, event-driven, precision, fixed-N, or pilot
      framing when exact planning is not credible.
- [ ] State what evidence or pilot estimate would most improve confidence.

## Validation and translational planning

- [ ] Define the primary claim to be validated before choosing tiers.
- [ ] Separate internal resampling/holdout from temporal/site/external
      validation; do not call one another.
- [ ] Distinguish technical/orthogonal support, biological/functional evidence,
      causal support, and clinical/translational implementation evidence.
- [ ] Classify each tier as necessary, recommended, optional, or not currently
      justified.
- [ ] Separate currently available, potentially obtainable, and unavailable
      datasets, specimens, assays, sites, models, and personnel.
- [ ] For biomarkers/prediction, address leakage, calibration, discrimination,
      spectrum, threshold locking, transportability, and independent validation.
- [ ] For omics/genetic/MR work, address replication, batch/platform, ancestry,
      sample overlap, instrument strength, pleiotropy, harmonization, and
      multiple testing where applicable.
- [ ] For functional validation, state the biological rationale, model/assay
      availability, biosafety, controls, and what remains unproven; do not invent
      experiments from an underspecified claim.
- [ ] State what the proposed validation can support and what it cannot.

## Translational, specialized, ethics, and feasibility gates

- [ ] Trace the claim chain: discovery → technical replication → biological
      support → clinical/implementation relevance. Identify the weakest link.
- [ ] Define whether the output is a research signal, validated assay/model,
      mechanism support, or clinically deployable tool; do not conflate them.
- [ ] Check population relevance, equity/generalizability, clinical workflow,
      interpretability, turnaround, cost, and downstream decision consequences.
- [ ] Obtain the appropriate ethics/oversight pathway (IRB/REC, IACUC, biosafety,
      data access, or governance) before human/animal/specimen work; do not claim
      approval or consent.
- [ ] Address consent/waiver, privacy, PHI/de-identification, linkage, retention,
      re-identification risk, secondary use, vulnerable groups, and data-sharing
      constraints.
- [ ] Address participant burden, harms, adverse-event monitoring, stopping
      rules, specimen handling, assay failure, and incidental findings where
      applicable.
- [ ] Check recruitment, staffing, site readiness, data engineering, lab/QC,
      budget, timeline, dependencies, and contingency resources.
- [ ] Define feasibility gates and stop conditions; distinguish a pilot from a
      powered confirmatory study.
- [ ] Record all unsupported assumptions and assign a next verification action.

## Routing and handoff

- [ ] Route literature/database/API retrieval, evidence grading, and citation
      verification to **evidence-insight**.
- [ ] Route data schemas, preprocessing, statistical fitting, model evaluation,
      plots, and reproducible computation to **data-analysis**.
- [ ] Route protocol narrative, methods/results sections, grants, reporting
      guidelines, and submission language to **academic-writing**.
- [ ] Route PHI/privacy, data governance, safety, installation, or audit concerns
      to **operations-and-audit** when relevant.
- [ ] Preserve the protocol decisions and assumptions in the handoff; do not
      silently replace them with analysis code or polished prose.
