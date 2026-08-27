# Data-analysis troubleshooting

Use this as a stop/recover matrix. First preserve the input manifest, command,
versions, and error text. Do not hide a failed or partial run by deleting its
artifacts.

## Triage matrix

| Symptom | Likely cause | Safe checks | Recovery or stop rule |
|---|---|---|---|
| File cannot be read or has one giant column | wrong path, encoding, delimiter, or extension | inspect a copy of the header, encoding, delimiter, and row/column count | re-export with a declared delimiter/encoding; do not guess silently |
| Missing/duplicate columns or keys | schema drift, whitespace, duplicate IDs, bad join | normalize header whitespace for checking, report duplicates and join loss | repair upstream data or document a deterministic mapping; stop if unit of analysis is unclear |
| Numeric coercion creates `NA` | locale decimals, text units, sentinel values, mixed types | profile raw tokens and missing-value codes | convert with an explicit rule and count changes; otherwise stop |
| Matrix orientation is disputed | genes × samples versus samples × genes | compare metadata IDs and dimensions; inspect data dictionary | transpose only with recorded evidence and revalidate alignment |
| Python package import fails | package absent/incompatible interpreter | record interpreter/package versions and test the smallest import | install in an isolated approved environment or use an explicit non-equivalent fallback; do not claim execution |
| R workflow fails at startup | `Rscript` or required package absent | run help/parser check and enumerate required packages | route to R environment preparation; do not substitute Python without labeling it |
| GPU/codec/dataset connector unavailable | optional backend not installed or hardware/data access missing | separate CPU/import success from backend-specific probes | continue only with an explicit partial claim if a CPU fallback is scientifically adequate; otherwise stop |
| PHI appears in a table, filename, log, plot, or DICOM tag | incomplete de-identification or unsafe output | quarantine output, search metadata/filenames/free text, review DICOM private tags and pixels | do not share or continue; redact/rebuild and route governance to `operations-and-audit` |
| Model uses patient/sample/accession ID | identifier leakage | inspect feature list, encoded columns, importance table, and joins | remove the field, rerun from a clean split, and invalidate the contaminated result |
| Test performance is implausibly high | leakage, duplicated participants, post-outcome features, selection on test | audit timestamps, group overlap, preprocessing fit, feature selection, and threshold tuning | invalidate result and rebuild the pipeline; do not merely add a caveat |
| Tiny sample or sparse class/event count | underpowered design or unstable fit | count unique units, classes/events, missingness, and events per parameter | provide descriptive/QC or a protocol-design plan; label any model diagnostic-only |
| Design matrix is singular or contrast missing | confounded covariates, empty levels, invalid reference | inspect level counts, rank, formula, and contrast spelling | simplify only with a declared scientific rationale; route estimand/design questions to `protocol-design` |
| `pydeseq2` rejects counts/design | non-integer/negative/transformed counts, unaligned metadata, rank deficiency | verify raw count scale, sample IDs, replicates, and design matrix | restore raw counts or fix metadata; never round normalized values to pretend they are counts |
| Too few or too many single-cell observations after QC | thresholds unsuitable, bad mitochondrial annotation, empty layer | compare before/after counts and QC distributions; inspect `obs`/`var` alignment | revise thresholds with justification and preserve pre-QC object; do not call a failed QC run biological evidence |
| AnnData subset/concat corrupts metadata | view mutation, duplicate names, mismatched joins, wrong `inner`/`outer` choice | check shapes, indices, layers, `raw`, and batch labels after each operation | copy before mutation, make join explicit, and revalidate; preserve the original object |
| EHR model inflates metrics | patient leakage, future information, label-window error | verify patient-level split, feature timestamps, task function, and prediction time | rebuild task/split; route endpoint and validation decisions to `protocol-design` |
| `pyhealth` training runs out of memory or is slow | long sequences, large batches, deep model, absent GPU | measure sequence lengths, batch size, model, device, and dataset size | reduce sequence length/batch or use a baseline; do not claim GPU verification from a CPU run |
| DICOM pixels cannot decode | compressed transfer syntax lacks handler or invalid file | inspect transfer syntax, file meta, frame count, and codec availability | install/verify the approved codec or perform metadata-only QC; do not silently discard images |
| DICOM series is misordered or geometry inconsistent | mixed series, missing orientation/position, duplicate instances | group by study/series and validate orientation, spacing, instance positions | separate series or stop volume construction; preserve geometry metadata |
| Survival estimate is nonsensical | negative time, event recoding, time-origin error, heavy censoring, competing risks | inspect ranges, origin, event table, follow-up, and risk sets | correct data/design or report limited descriptive output; do not infer treatment effect |
| Cox interpretation is unstable | proportional-hazards violation, sparse events, time-varying effects | inspect residual/assumption checks, events per covariate, and follow-up | use time-stratified/alternative estimand with protocol input, or report KM/RMST only |
| ROC model fails or separates perfectly | mismatched samples, invalid labels, too few cases/controls, collinearity/separation | verify exact IDs, two groups, finite markers, counts, and model warnings | reduce/justify predictors or use penalized/exploratory route; no unqualified AUC claim |
| ROC AUC is near 1 on a small cohort | leakage, overfit, marker selection, batch confounding | audit selection, preprocessing, batch/site, and resampling/external validation | label exploratory and seek independent validation; do not convert AUC into clinical utility |
| LightGBM/XGBoost parses target incorrectly | delimiter, target type, factor level, unnamed index, missing target | inspect parsed columns and resolved task type before training | correct input/arguments, exclude IDs, and rerun with a seed; preserve remediation output |
| Boosting importance is all zero or predictions collapse | underpowered signal, constraints, class imbalance, failed training | inspect best iteration, class predictions, metrics, importance metric, and warnings | mark diagnostic-only, adjust only via documented rerun plan, and never narrate a ranking as biology |
| Figure is misleading or unreadable | inconsistent scale, hidden denominator, truncated axis, PHI label, raster loss | compare plot with source table and parameter manifest | regenerate with units/counts/uncertainty and safe labels; retain prior figure as superseded |
| Results cannot be reproduced | missing seed, package drift, implicit preprocessing, overwritten output | compare manifest, environment, command, split, and artifact checksums | reconstruct from raw/governed inputs or label as non-reproducible; route audit to `operations-and-audit` |

## Recovery sequence

1. Stop at the first invalid assumption and preserve the failed run.
2. Classify the blocker as schema, privacy, method/design, dependency/backend,
   compute, or output integrity.
3. Make the smallest reversible repair; never change outcome, cohort, or model
   family just to obtain a result.
4. Re-run schema and privacy checks before the analysis. Re-run leakage and
   split checks before any predictive metric.
5. Compare the new manifest with the failed one and explain every changed row,
   feature, parameter, dependency, and output.
6. Mark the result `complete`, `partial`, `diagnostic-only`, or `blocked`; do
   not use a successful process exit as the acceptance criterion.

## Backend-specific limits

- **Python:** A successful parser/help or import check proves only that narrow
  surface. It does not verify large-data behavior, optional plotting, PyTorch,
  GPU, DICOM codecs, or data connectors.
- **R:** An `Rscript --help` or parser check does not prove that `optparse`,
  `data.table`, `lightgbm`, `xgboost`, ROC libraries, or plotting devices work
  on the supplied data. Record package versions and run outputs separately.
- **Cross-language:** If the handoff changes orientation, factors, missing values,
  date units, or encoding, invalidate the downstream result until row/key checks
  pass.
- **Hardware and network:** Do not download models/data, call APIs, or access
  credentials as an implicit troubleshooting step. Ask for an approved
  environment or provide a bounded offline plan.

## Routing escalations

- Missing literature, evidence comparison, biological mechanism claim, or
  citation verification → `evidence-insight`.
- Ambiguous cohort, endpoint, estimand, comparator, sample size, confounding,
  temporal split, or external-validation plan → `protocol-design`.
- PHI, DICOM release, access authorization, audit trail, installation/import,
  environment governance, or reproducibility audit → `operations-and-audit`.

## Final checks before handoff

- schema and data dictionary are attached;
- PHI gate passed and output labels/files are safe;
- exclusions, transformations, missingness, and split rules are recorded;
- method assumptions and limitations are stated;
- interpreter/packages/backend/seed/config are recorded;
- expected tables, figures, and run manifest exist;
- no required backend remains unverified;
- result status and next review owner are explicit.
