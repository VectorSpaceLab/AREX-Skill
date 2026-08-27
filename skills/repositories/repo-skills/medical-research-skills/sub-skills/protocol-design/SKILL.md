---
name: protocol-design
description: "Routes biomedical research questions into ethically aware,
  feasibility-conscious study protocols covering aims, design, endpoints, bias,
  power, validation, and translational planning."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Protocol Design

Use this route when a researcher needs to turn a biomedical idea into a
study-design plan: aims and hypotheses, design family, eligibility and
endpoints, bias/confounding controls, sample-size logic, validation, or a
translational/specialized protocol. This is protocol planning, not patient care,
statistical execution, or manuscript prose.

## Route and boundary

1. **Frame the question.** State the population/model, exposure or intervention,
   comparator, primary outcome, time horizon, intended estimand, and whether the
   claim is descriptive, associative, predictive, mechanistic, or causal-leaning.
   Create one coherent primary aim; subordinate secondary and exploratory aims.
2. **Select the study design.** Choose among experimental, clinical cohort,
   case-control, diagnostic/prognostic, RWE, translational, omics, or genetic
   (including MR) designs based on temporal logic, available data/specimens,
   recruitment, and the claim—not on habit. Define time-zero, eligibility,
   baseline window, exposure/intervention, follow-up, censoring, and endpoints.
3. **Stress validity and feasibility.** Separate baseline from post-baseline
   variables; identify selection, confounding, immortal-time, measurement,
   missingness, multiplicity, transportability, and competing-risk threats.
   Treat effect sizes, event rates, variance, follow-up, data capture, and
   validation resources as unknown until supported. Obtain ethics, privacy,
   safety, recruitment, specimen, site, and operational feasibility review.
4. **Plan power and validation.** Let the primary endpoint/estimand drive
   formal, range-based, event-driven, precision, or fixed-N feasibility
   planning. Specify internal versus independent, temporal/site/external,
   technical/orthogonal, functional, and translational validation tiers; never
   call resampling external validation or infer causal proof from support alone.
5. **Produce a bounded handoff.** Return assumptions, decisions, alternatives,
   feasibility blockers, minimum credible protocol, analysis/validation needs,
   and what remains unverified. Route live evidence retrieval and citation
   verification to **evidence-insight**, executable modeling/data checks to
   **data-analysis**, and protocol/manuscript/grant prose to
   **academic-writing**. Ethics/privacy or operational concerns may also need
   **operations-and-audit**.

## Read the bundled references

- [workflows.md](references/workflows.md) for the end-to-end route, design
  families, outputs, and specialist handoffs.
- [design-checklists.md](references/design-checklists.md) for aims, eligibility,
  endpoints, validity, power, validation, translation, ethics, and feasibility
  gates.
- [troubleshooting.md](references/troubleshooting.md) for missing inputs,
  design mismatch, unsupported assumptions, and recovery actions.

## Safety and evidence limits

Do not provide patient-specific diagnosis or treatment, invent literature,
registry/database capture, event rates, sample sizes, assay feasibility,
validation cohorts, or ethical approval. Mark candidate resources and
assumptions explicitly. A protocol draft is not an IRB/REC/IACUC submission,
statistical analysis execution, or clinical decision. If a critical design
input is missing, ask focused questions or proceed only with a clearly labeled
provisional design and an explicit stop condition.
