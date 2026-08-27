# Data-analysis workflows

This reference turns the router into an execution plan. The named package skills
are catalog capabilities, not proof that a package, codec, R library, dataset,
GPU, or credential is installed. Use the supplied input and environment as the
source of truth and record anything that was not verified.

## 1. Intake record

Before selecting a method, write a short run record containing:

- question and estimand or prediction target;
- study design, inclusion/exclusion rules, unit of analysis, and time origin;
- data modality, file formats, row/column meaning, identifiers, and data dictionary;
- outcome type and coding, predictor availability, missingness, censoring, and
  class/event counts;
- train/validation/test or resampling plan, site/time grouping, and leakage risks;
- requested tables, figures, model object, report, or machine-readable outputs;
- Python/R interpreter, package versions, optional dependencies, hardware,
  resource limits, seed, and permissible file/network access;
- PHI authorization, de-identification status, retention, and output-sharing
  constraints.

A missing field is blocking when it can change the estimand, analysis family,
privacy status, or validity of the output. Keep safe assumptions labeled with a
validation action.

## 2. Method-selection map

| Signal | First route | Required checks | Typical output | Do not overclaim |
|---|---|---|---|---|
| Descriptive or inferential clinical table | Statistical workflow selected by outcome/design | variable types, independence, distribution, missingness, multiplicity, effect size and CI | analysis-ready table, estimate/CI/p-value, assumptions log | a p-value is not clinical importance or causality |
| Bulk RNA-seq counts | `pydeseq2` | samples × genes orientation, non-negative integer counts, aligned metadata, replicated groups, design rank, contrast, low-count rule | normalized/model results, Wald statistics, BH-adjusted `padj`, LFC table and plots | LFC shrinkage helps ranking/visualization; it does not replace the tested p-value |
| Single-cell transcriptomics | `anndata` then `scanpy` | `.X` shape, `obs`/`var` alignment, sparse/dense scale, raw/layer provenance, QC thresholds, batch and donor structure | filtered `.h5ad`, QC/PCA/UMAP/cluster/marker figures, metadata | clusters and marker associations are not automatic cell-type truth or independent biological replicates |
| Longitudinal EHR or coded clinical events | `pyhealth` after task definition | patient/visit/event hierarchy, code vocabulary, temporal leakage, patient-level split, label window, class imbalance, consent/access | task dataset, baseline/model, held-out metrics, calibration/fairness/uncertainty notes | research performance is not deployment or clinical decision support |
| DICOM metadata, pixels, or series | `pydicom` | valid DICOM, transfer syntax/codec, modality and geometry, series ordering, PHI and burned-in text | sanitized metadata, pixel/volume derivative, QC log | de-identification is not guaranteed by deleting a few tags; inspect the whole release |
| Right-censored outcome | `survival-analysis-km` | time origin and units, nonnegative time, binary event, censoring definition, group counts, competing risks, follow-up | KM curve with CI/risk table, log-rank summary, median/RMST where estimable | a curve comparison is not a causal treatment effect; inspect assumptions before Cox interpretation |
| Binary diagnostic marker/case-control | `roc-diagnostic-performance` | expression matrix orientation, matched sample IDs, exactly two groups, enough cases/controls, finite values, separation and train/test design | logistic coefficients/ORs, per-marker and full-model AUC, ROC figure | AUC is discrimination in the sampled cohort, not calibration, utility, or external validity |
| Tabular boosting and feature importance in R | `LightGBM-analysis` or `XGBoost-analysis` | delimiter, target type, IDs/sensitive columns, encoding, row count, split, class balance, early stopping, importance metric | metrics, importance table/plot, remediation and run summary | importance is model-dependent and not causal; tiny or collapsed models are diagnostic-only |
| Visualization only | modality-appropriate plotting workflow | scale, units, denominators, missingness, subgroup counts, uncertainty, color/label accessibility | figure plus data/parameter manifest | a polished figure cannot repair invalid data or analysis |

If the request combines rows, use the common validation stage once and branch only
where the schemas and estimands differ. Do not force a single package to cover
all modalities.

## 3. Validation and preparation stage

1. Make a read-only inventory of files and permitted output locations.
2. Parse headers/metadata and compare the declared schema with observed columns,
   dimensions, identifiers, units, and encodings.
3. Resolve orientation using explicit evidence (headers, dimensions, known IDs),
   never by a silent heuristic. Preserve the original and a transformed copy.
4. Check duplicate IDs, join loss, impossible values, date/time order, unit
   consistency, missingness patterns, outliers, and label/event counts.
5. Remove or quarantine identifiers and PHI before modeling or plotting. Keep a
   restricted mapping outside shared artifacts only if governance authorizes it.
6. Define preprocessing inside the resampling boundary. Fit imputation,
   scaling, encoding, feature selection, and threshold choice on training data
   only. For omics, state filtering and normalization before testing.
7. Freeze a manifest: input fingerprints or governed dataset IDs, row/column
   counts, exclusions, transformation parameters, software, seed, and output
   names.

Use [data-formats.md](data-formats.md) for modality-specific acceptance tests.

## 4. Analysis-specific execution rules

### Clinical statistics

Select methods from the outcome and design, not from a desired p-value. Report
sample size, missing-data handling, effect size, uncertainty interval, and
assumption/robustness checks alongside any test. Distinguish descriptive,
associational, predictive, and causal questions. Repeated measures, clustering,
confounding, informative missingness, multiple comparisons, and time-varying
exposure require protocol-level decisions; route them to `protocol-design`.

### Omics and bioinformatics

For `pydeseq2`, require integer count scale, aligned sample metadata, an estimable
formula, an explicit reference group and contrast, and multiple-testing control.
For `anndata`/`scanpy`, preserve `X`, layers, `raw`, `obs`, `var`, embeddings,
and parameters as separate provenance-bearing slots. Keep donor/sample as the
replication unit where appropriate; do not treat every cell as an independent
clinical participant. QC thresholds are data-dependent and must be justified
with plots and counts before/after filtering.

### Clinical ML and EHR

Define the prediction time, feature availability window, label window, and
censoring/competing event policy before constructing features. Split by patient,
and use time/site holdouts when transportability matters. Compare against a
simple baseline; report AUROC and AUPRC for binary outcomes when appropriate,
calibration, subgroup performance, missingness, and uncertainty. Deep learning,
GPU, and large-data claims remain optional until directly verified. `pyhealth`
is a research toolkit, not a certified clinical device.

### Survival and diagnostic modeling

For survival, retain time units, event definition, censoring, and time origin.
Check sparse groups, heavy censoring, delayed entry, competing risks, and
proportional hazards before interpreting a hazard ratio. Consider RMST or
restricted follow-up when proportional hazards is implausible.

For diagnostic ROC, verify matched samples and exactly two groups. Prevent marker
selection and threshold tuning on the evaluation set. Report confidence
intervals or resampling strategy where supported, prevalence/context, and an
external validation plan. Route calibration, decision-curve, nomogram, or
multi-class work to the appropriate specialist workflow or `protocol-design`.

### Visualization

Create figures from a frozen analysis table, not an untracked interactive state.
Include units, denominator, uncertainty, sample counts, missingness notes, and a
legend that remains interpretable in grayscale or color-vision deficiency. Use
consistent scales across comparisons, avoid truncated axes that mislead, and save
an editable/vector version plus a data/parameter manifest. Never place direct
identifiers, rare dates, or free-text PHI in labels or image annotations.

## 5. Python/R/backend boundary

- Python is the preferred boundary for `pydeseq2`, `scanpy`, `anndata`,
  `pyhealth`, `pydicom`, and `survival-analysis-km` patterns. Verify imports and
  versions in the actual environment; optional plotting, PyTorch, codecs, and
  GPU support are separate gates.
- R is the execution boundary for the representative `roc-diagnostic-performance`,
  `LightGBM-analysis`, and `XGBoost-analysis` workflows. Verify `Rscript`, every
  required package, input parser behavior, and output files independently.
- A Python table can feed an R workflow only through a declared interchange
  contract: delimiter/encoding, column names, orientation, factor/label rules,
  missing-value representation, units, and a checksum or row-count check.
- Do not translate APIs or silently substitute an algorithm across languages.
  If the original backend is unavailable, provide a documented fallback and
  label the result as non-equivalent or unverified.
- CPU success is not evidence of CUDA/ROCm/MPS, compressed DICOM codec, R
  package, external dataset connector, or model-download readiness. Record
  optional backend status and stop if it is required for the requested result.

## 6. Reproducibility and handoff

The minimum run bundle is:

```text
run-manifest/
  data-dictionary.(md|json)
  input-manifest.(md|json)
  schema-check.(md|json)
  parameters.(md|json)
  environment.(md|json)
  exclusions-and-transformations.md
  results/             # tables, figures, model summary
  warnings-and-limits.md
```

Record deterministic seeds, split indices or split rule, package versions,
randomness controls, plotting settings, and the exact command/config. Keep
machine-learning models and predictions separate from identifiers. A result is
report-ready only after schema checks, leakage checks, method assumptions,
artifact checks, and human review pass.

- Evidence question, literature comparison, or unsupported biological/clinical
  claim → `evidence-insight`.
- Study architecture, endpoint/estimand, power, confounding, or validation plan
  → `protocol-design`.
- PHI, DICOM release, access, audit, environment installation, reproducibility
  audit, or operational safety → `operations-and-audit`.

## 7. Stop and fallback policy

Stop rather than fabricate when the input cannot be parsed, the outcome is
ambiguous, the design is rank-deficient, identifiers cannot be removed, a
required backend is missing, classes/events are insufficient, or the requested
interpretation exceeds the method. A safe fallback may be schema-only review,
descriptive QC, a baseline model, parser/help verification, or a written plan;
label it partial and list the next required check.
