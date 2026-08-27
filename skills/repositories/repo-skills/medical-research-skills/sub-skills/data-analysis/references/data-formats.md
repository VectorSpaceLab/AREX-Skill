# Data formats and schema contracts

Validate structure before selecting a statistical or machine-learning method.
The examples below are abstract contracts; adapt names to the supplied data and
preserve a data dictionary. Never infer clinical meaning from a column name
alone.

## Universal schema contract

Every input should have:

- a declared file format, encoding, delimiter, decimal convention, and unit;
- a data dictionary with semantic type, allowed values/range, missing-value
  codes, measurement time, and whether a field is an identifier or PHI;
- a stable analysis key or an explicitly documented aggregate unit;
- unique keys where uniqueness is required and an explicit many-to-one/many-to-many
  join policy;
- finite numeric values where a method requires them, with `NA`/missing distinct
  from zero, censoring, and not-applicable;
- an analysis manifest recording source, row/column counts, transformations,
  exclusions, and validation status.

Check for duplicate columns, duplicate keys, hidden whitespace, mixed encodings,
locale-specific decimals, sentinel values (`999`, `-9`, empty strings), accidental
index columns, and dates stored as free text. Preserve a raw, access-controlled
copy; publish only the minimum de-identified derivative.

## Clinical and general tabular data

Preferred interchange is CSV/TSV with a header and one row per declared unit
(patient, visit, sample, or measurement). At minimum define:

| Field class | Contract |
|---|---|
| analysis key | unique at the declared unit; no direct patient identifier in model features |
| outcome | type, coding, reference level, observation/prediction window, and missing rule |
| predictors | numeric/categorical/text/time-series type, units, availability time, and transformations |
| dates/times | timezone, time origin, granularity, and whether dates were shifted/de-identified |
| site/batch | categorical values and whether used for adjustment, grouping, or holdout |
| PHI | access classification and removal/redaction status |

Before modeling, compare row counts before/after joins, inspect target prevalence,
check impossible clinical values, and decide whether repeated rows need mixed,
clustered, or patient-level handling.

## Bulk RNA-seq expression for `pydeseq2`

Canonical analysis orientation is **samples × genes**:

```text
counts:  rows = unique sample IDs; columns = unique gene IDs
metadata: rows = the same sample IDs; columns = condition, batch, covariates
```

Many files arrive genes × samples and may need an explicit transpose. Accept only
non-negative integer-like raw counts for a count model. Do not pass log-CPM,
normalized expression, TPM, or already transformed values as raw counts. Verify:

- sample IDs are unique and exactly aligned between matrix and metadata;
- each contrast group has enough biological replicates;
- condition/reference labels are present and unambiguous;
- covariates are coded with the intended type and the design matrix is estimable;
- low-count filtering is declared before testing;
- gene identifiers are unique or a documented aggregation rule is applied;
- batch/paired structure is handled by a declared design rather than post-hoc
  interpretation.

Outputs should identify scale, design, contrast, normalization, tested genes,
raw p-values, BH-adjusted `padj`, LFC, and any shrinkage used for ranking.

## Single-cell `.h5ad`/AnnData for `anndata` and `scanpy`

The core object contract is:

```text
X       observations × variables matrix (cells × genes for scRNA-seq)
obs     one row per observation, indexed by obs_names
var     one row per variable, indexed by var_names
layers  aligned alternative matrices such as counts or normalized values
raw     optional frozen raw snapshot; record when and why it was made
obsm    observation-aligned embeddings such as PCA/UMAP
varm    variable-aligned loadings or embeddings
obsp    observation-pair matrices such as neighbor graphs
uns     parameters, annotations, and unstructured provenance
```

Validate dimensions and index alignment after every subset/concatenation. Record
whether `X` is dense/sparse, raw counts/log-transformed/other scale, in-memory or
backed, and whether a view was copied before modification. For batches, preserve
batch/donor labels and the join strategy; `inner` versus `outer` feature joins
changes the biological universe. A cluster is not a donor, and cell-level
replication must not be reported as independent patient-level evidence.

Minimum single-cell QC manifest: cells/genes before and after filtering,
mitochondrial/ribosomal definitions, thresholds, normalization target,
transformation, HVG rule, dimensions/neighbors, clustering resolution, batch
correction, marker method, and annotation evidence.

## DICOM and imaging data for `pydicom`

Treat a DICOM file as a structured object, not merely an image. Validate:

- readable file meta and transfer syntax; required decompression handlers for
  compressed pixel data;
- modality, study/series/instance identifiers, dimensions, orientation, spacing,
  slice ordering, frame count, and pixel representation;
- consistency across a series before stacking a volume;
- window/VOI interpretation and photometric/color-space handling before plotting;
- patient/study/series/physician tags, private tags, dates, UIDs, filenames, and
  pixel-embedded text for PHI.

Anonymization requires an approved policy, recursive metadata review, UID/date
handling, pixel-text inspection where relevant, and a post-anonymization audit.
Do not claim that setting a name to `ANONYMOUS` alone is sufficient. Preserve
spatial metadata needed for the research task in a governed, non-identifying form.
Route release and governance decisions to `operations-and-audit`.

## EHR/event sequences for `pyhealth`

Define the hierarchy explicitly:

```text
patient → visits/encounters → timestamped events → task sample → label
```

Declare code systems and vocabulary versions (for example diagnosis, procedure,
and medication families), event timestamp semantics, unit, missingness, and
feature availability relative to the prediction time. Validate that no future
visit, post-outcome code, discharge artifact, or duplicated patient crosses a
split. Split by patient and, where transportability matters, by time/site. Keep
patient and visit identifiers out of model features and shared predictions.

The task label must specify binary/multiclass/multilabel/regression semantics,
observation window, prediction window, censoring/competing event treatment, and
class balance. Report baseline and held-out metrics, calibration, subgroup
performance, and uncertainty. Deep models, GPU, and large external datasets are
optional backend claims and require separate verification.

## Survival data

A minimal row-level table is:

```text
analysis_key, time, event, [group], [covariates]
```

`time` must be numeric, non-negative, and measured from a declared origin.
`event` must be explicitly coded (usually 1 = event, 0 = right-censored), with
competing events and delayed entry handled by design rather than recoding. Check
for zero follow-up, impossible dates, duplicate analysis units, sparse groups,
heavy censoring, and ties. Preserve the number at risk and censoring marks in
figures. A survival model cannot recover information absent from follow-up.

## Diagnostic ROC data

The representative ROC workflow expects two related tables:

```text
expression: rows = unique marker/gene IDs; columns = unique sample IDs
groups:     rows = unique sample IDs; columns = binary group label
```

Validate file type/delimiter, finite numeric values for selected markers, exact
sample matching, at least two samples in each group, and exactly two outcome
levels. Declare which level is the case/positive class. Ensure marker selection,
preprocessing, and threshold choice do not use the evaluation sample. Report
sample counts and uncertainty; AUC alone is not calibration or net benefit.

## R boosting tables for `LightGBM-analysis` and `XGBoost-analysis`

Use CSV/TSV with one row per analysis unit and a declared target column. Check:

- target exists, has the requested type, and has adequate rows/classes;
- character/factor encoding is intentional and levels are captured;
- unnamed first columns, sample IDs, patient IDs, accession numbers, dates, and
  sensitive fields are dropped before modeling;
- delimiter and decimal parsing produce the expected number of columns;
- train/test/validation rules are reproducible and stratified/grouped when needed;
- early stopping, importance metric (`gain`, `split`, `cover`, or frequency), and
  top-N display limit are recorded.

Require output tables, figures, run summary, warnings/remediation, and session
information. If a model collapses to one class, has all-zero importance, or is
underpowered, mark it diagnostic-only rather than reporting an importance story.

## Output and cross-language contract

A handoff between Python and R must include:

```text
encoding: UTF-8 (or declared alternative)
delimiter/decimal: declared
header and index policy: declared
orientation: rows/columns meaning
missing values: explicit representation
categorical levels: ordered/reference level if relevant
units and transformations: declared
row/column counts and key check: recorded
PHI status: de-identified and reviewed, or blocked
```

Never serialize a Python index as an unexplained R predictor. Never use a display
CSV as a raw-count or model-input file without checking its scale and metadata.

## PHI and privacy schema gate

Classify fields before analysis:

1. direct identifiers and quasi-identifiers;
2. dates, locations, free text, filenames, UIDs, and rare combinations;
3. clinical measurements and derived features;
4. labels, predictions, and model explanations.

Only the minimum approved fields proceed. Remove or tokenize identifiers outside
the analysis key, redact free text, inspect DICOM private tags and pixels, and
avoid small-cell outputs that can re-identify participants. Keep linkage keys and
access logs outside shared run artifacts. If privacy status is uncertain, stop and
route to `operations-and-audit`.
