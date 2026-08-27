# Dataset and metric troubleshooting

## Missing paths and wrong constructor layout

**Symptom:** `FileNotFoundError`, an `IOError` message, or a class exits while
looking for a fixed filename.

**Likely cause:** `dirpath` was omitted, points at the CSV rather than its
parent directory, or the source file was renamed. Check the exact contracts in
[data-formats.md](data-formats.md) and run the checker against the directory.
For HELOC, COMPAS, MEPS, Adult, and TED, the filename is part of the API; do
not pass a generic `data.csv` and expect discovery. For e-SNLI, remember that
the class has no `dirpath` parameter. For Ford/Sunspot/Climate/Diabetes, a
custom local path cannot be supplied through the public constructor in this
release; use the expected cache location or an external adapter.

**Recovery:** correct the directory/file layout, preserve a raw copy, rerun
`check_dataset_contract.py`, and only then construct the class. Do not catch a
process exit and continue with an uninitialized object.

## Network-disabled environments

**Symptom:** a constructor hangs, raises a requests/URL error, or attempts to
retrieve a file even though a local path was supplied.

**Cause:** MNIST, CIFAR, CDC, Fashion-MNIST, Climate, Ford, Sunspot, and
Diabetes constructors download when their cache is absent. Supplying `dirpath`
only helps for classes that actually expose it; it does not disable downloads.

**Recovery:** run the bundled checker with `--no-network` (the default), stage
all required files through an approved channel, and verify them locally. If the
files are unavailable, stop with a missing-data report. Do not alter the
package, replace URLs with arbitrary mirrors, or run a tutorial downloader.
The checker itself performs no socket, HTTP, archive extraction, or package
installation operation.

## Optional `xport` dependency and CDC files

**Symptom:** importing the CDC module raises `ModuleNotFoundError: xport`, or
construction fails while converting XPT files.

**Cause:** CDC imports `xport` at module import and expects a fixed NHANES
questionnaire file set. The default callback is defined but not applied by the
current constructor.

**Recovery:** install the supported AIX360 optional dependency set in the
execution environment, or keep the workflow at local structural validation.
Check that XPT files are complete and that the generated `csv/` directory is
writable before conversion. Treat refusal/unknown CDC responses as coded survey
values, not ordinary numeric measurements, and consult the current NHANES
codebook. Do not claim CDC coverage from a single arbitrary CSV.

## Optional torch/torchvision dependency and Fashion-MNIST

**Symptom:** `ModuleNotFoundError: torch` or `torchvision`, cache lookup fails,
or the constructor unexpectedly tries to download.

**Cause:** `FMnistDataset` imports both packages at module import, constructs
`FashionMNIST` with `download=True`, randomly samples the training subset, and
uses a historical `fmnit_data` default spelling.

**Recovery:** verify compatible torch/torchvision versions and a complete
Fashion-MNIST cache before construction. Pass an explicit cache root when
possible, then verify `data_dims`, loader batch shapes, and pixel range. For a
reproducible subset, control torch's random seed before construction; the class
itself does not expose a seed. If the cache is absent in offline mode, report
the dependency/data block rather than retrying.

## Optional TensorFlow dependency and Climate

**Symptom:** importing the climate module fails with `ModuleNotFoundError:
 tensorflow`, or loading data fails in `timeseries_dataset_from_array`.

**Cause:** TensorFlow is imported at module import, even for inspection. The
class uses a Keras time-series helper and a fixed cache path; it does not accept
`dirpath`.

**Recovery:** use an environment containing a compatible TensorFlow/Keras pair,
then validate the CSV's `Date Time` plus 14 feature columns and finite numeric
values. Check the selected seven columns, sequence length 120, forecast offset,
and train/test counts. A CPU import does not prove that a separate GPU
workflow works. In offline mode, keep the class unconstructed until the CSV is
present.

## Raw versus preprocessed shapes

**Symptom:** an algorithm reports unexpected column counts, an image model gets
flattened input, or a time-series model receives too few windows.

**Cause:** AIX360 returns different representations: HELOC default `data()` is
an array with target last while `dataframe()` is raw; MNIST images are
`(n,28,28,1)` and scaled to `[-0.5,0.5]`; Fashion-MNIST batches are `(batch,28,
28,1)` and scaled to `[0,1]`; CIFAR images are `(n,32,32,3)`; Ford windows are
`(n,500,1)`; Climate windows use a 120-step sequence; Sunspot returns a frame
plus schema.

**Recovery:** print and persist `shape`, `dtype`, feature names, target shape,
and value range immediately after loading. Compare those facts with the
consuming explainer/model contract. Do not normalize twice or infer a target
column from “last column” unless that dataset explicitly defines it.

## Inconsistent feature, coefficient, and base arrays

**Symptom:** reshape errors, an index error, an invalid model prediction, or a
`nan`/unexpected metric result.

**Cause:** explanation weights refer to a subset or a different feature order;
`base` has the wrong width; a model was trained after dropping columns; or
categorical encoding expanded the feature space.

**Recovery:** build a feature-name-to-model-index map, zero-fill a coefficient
vector of exactly `x.shape[0]`, and create `base` in that same encoded space.
Assert equal lengths and finite values before calling either metric. Ensure
`predict_proba(x.reshape(1,-1))` has one row and at least two classes. If
faithfulness is `nan`, inspect for constant coefficient or perturbed-probability
vectors before averaging. For monotonicity, inspect signed coefficient order
and the ordered probability sequence; do not sort by absolute weight unless the
metric is intentionally reimplemented outside AIX360.

## Bad preprocessing or label alignment

**Symptom:** stratified split fails, labels have the wrong length, all rows are
removed, or a callback raises a missing-column error.

**Cause:** the callback received an already transformed array instead of its
expected DataFrame, sentinel values were treated as ordinary measurements, or
rows were filtered after labels were separated without applying the same mask.

**Recovery:** validate raw columns first, apply the callback to a copy, compare
row counts before/after each filter, and check `X.shape[0] == y.shape[0]`.
For HELOC choose deliberately between zero replacement and NaN preservation.
For COMPAS ensure both jail date columns parse with the expected timestamp
format. For MEPS use the data dictionary to interpret codes and verify the
post-filter columns. For Adult confirm the headerless positional layout.

## Licensing, download, and conversion expectations

**Symptom:** a benchmark cannot be fetched automatically, a form/account is
required, or the local file cannot be redistributed.

**Recovery:** stop and request the user to acquire the dataset under its current
terms. HELOC may require the FICO challenge access form; MEPS requires reading
AHRQ usage restrictions and converting H181 to `h181.csv`; CDC/NHANES requires
source-specific terms and questionnaire codebooks. Record source version,
license/approval state, checksum where available, and conversion steps in the
experiment handoff. A successful structural check is not evidence that a
license or download obligation was satisfied.

## What not to do

Do not run full notebooks, hidden download helpers, external R/SPSS conversion,
large model training, or GPU-dependent explainers as a substitute for this
route's checks. Do not put credentials in URLs or commit downloaded personal or
restricted data into the skill tree. Route model fitting and explanation
construction to the owning AIX360 algorithm sub-skill.
