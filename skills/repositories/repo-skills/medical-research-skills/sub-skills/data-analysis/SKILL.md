---
name: data-analysis
description: "Route and supervise clinical, biomedical, omics, imaging,
  survival, diagnostic, and machine-learning analyses with explicit schemas,
  backend limits, privacy gates, and reproducible outputs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Data Analysis

Use this route for clinical statistics, omics/bioinformatics, machine learning
(ML), survival or diagnostic modeling, data preparation, visualization, or a
reproducible analysis record. This is an operating router, not a substitute for
biostatistical review, clinical judgment, an ethics/privacy decision, or a
specialist package skill.

## Route in this order

1. **State the analysis contract.** Capture the scientific question, unit of
   analysis, study design, data modality, outcome and predictors, cohort and
   split rules, intended output, available Python/R/tools, compute or GPU
   constraints, and acceptance checks. If any missing item could change the
   method, stop and request it rather than guessing.
2. **Apply the privacy gate.** Confirm authorization and de-identification before
   opening or exporting data. Remove direct identifiers and inspect free text,
   filenames, DICOM tags, dates, rare combinations, and image burned-in text.
   Never place PHI in prompts, logs, plots, model features, or filenames. Route
   anonymization, access control, audit logging, or a possible clinical decision
   to `operations-and-audit`.
3. **Validate the schema before modeling.** Check identifiers, orientation,
   uniqueness, joins, data types, units, missingness, outcome coding, time order,
   class/event counts, and leakage-prone columns. Use
   [references/data-formats.md](references/data-formats.md).
4. **Select the narrowest evidence-backed workflow.** Use the decision table and
   package boundaries in [references/workflows.md](references/workflows.md), then
   read [references/troubleshooting.md](references/troubleshooting.md) before
   executing a script or interpreting a failure.
5. **Make the backend explicit.** Python workflows (for example `pydeseq2`,
   `scanpy`, `anndata`, `pyhealth`, `pydicom`, and `survival-analysis-km`) and R
   workflows (for example `roc-diagnostic-performance`, `LightGBM-analysis`, and
   `XGBoost-analysis`) are not interchangeable. Record interpreter, package
   versions, seed, configuration, and optional backend status. Do not claim that
   a CPU check verifies CUDA, R packages, compressed-pixel codecs, or a clinical
   dataset connector.
6. **Produce reviewable artifacts.** Preserve the validated input manifest,
   schema/data dictionary, exclusions and transformations, analysis parameters,
   random seed/split, software environment, warnings, tables, figures, and a
   concise interpretation with uncertainty. Keep exploratory, diagnostic-only,
   and report-ready results distinct.
7. **Route adjacent work.** Send a literature-grounded claim, evidence search,
   or contradictory finding to `evidence-insight`; send aims, estimands,
   eligibility, endpoint, power, confounding, or validation-plan decisions to
   `protocol-design`; send PHI, governance, installation, audit, reproducibility
   review, or operational safety issues to `operations-and-audit`.

## Fast routing signals

- Bulk RNA-seq integer counts with a condition/design/contrast: `pydeseq2`.
- Single-cell data or `.h5ad`: `anndata` for structure and I/O; `scanpy` for
  QC, normalization, dimensionality reduction, clustering, markers, and plots.
- EHR or longitudinal clinical prediction: `pyhealth` only after a patient-level
  task and split are defined; start with an interpretable baseline when data are
  small or labels are sparse.
- DICOM metadata, pixels, conversion, or de-identification: `pydicom`; privacy
  and release decisions still require `operations-and-audit`.
- Right-censored time-to-event data: `survival-analysis-km` for Kaplan–Meier,
  group comparisons, and documented survival summaries. Check censoring,
  time origin, competing events, and proportional-hazards assumptions before
  using a Cox estimate.
- Binary case/control marker performance: `roc-diagnostic-performance` for
  logistic-model coefficients, marker/full-model ROC curves, and AUC. It is not
  a survival, multiclass, calibration, or decision-curve workflow.
- R tabular boosting with feature importance: `LightGBM-analysis` or
  `XGBoost-analysis`. Exclude IDs and sensitive fields, check class balance and
  delimiter handling, and treat degenerate or tiny runs as diagnostic-only.

## Non-negotiable boundaries

- Association, prediction, feature importance, AUC, and survival estimates do
  not establish causality, treatment benefit, or clinical utility.
- Do not tune thresholds, select genes, impute, normalize, or choose features
  using held-out test data. Fit preprocessing inside training folds when
  evaluating predictive performance.
- Do not mix raw counts, normalized expression, transformed values, and model
  outputs without naming the scale and preserving provenance.
- Do not silently transpose matrices, coerce outcome labels, drop samples, or
  replace missing values. Record every change and its reason.
- Stop on invalid or ambiguous schemas, unsupported backends, missing codecs,
  insufficient events/classes, severe separation, or unreviewed PHI. Offer a
  bounded fallback rather than fabricating results.

## Bundled guidance

- [references/workflows.md](references/workflows.md): intake, method selection,
  package-specific boundaries, validation, execution, visualization, and
  handoffs.
- [references/data-formats.md](references/data-formats.md): modality schemas,
  orientation, identifiers, outcome conventions, and artifact contracts.
- [references/troubleshooting.md](references/troubleshooting.md): failure
  diagnosis, safe recovery, backend escalation, privacy response, and stop rules.
