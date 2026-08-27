# MedMNIST troubleshooting

Read this when a package import, dataset/evaluator construction, CLI call, or
output operation fails. Keep the exact flag, split, size, root, task, and file
name in the incident note.

## Install and import

**Symptom:** `import medmnist` prints a request to install requirements or
raises an import error for torch, torchvision, NumPy, pandas, scikit-learn,
scikit-image, Pillow, tqdm, or Fire.

**Recovery:** install the public package in the intended environment, then run
`python -c "import medmnist; print(medmnist.__version__)"`. Avoid mixing a
source checkout and a different installed release while diagnosing. The
selected public workflows require CPU package behavior; CUDA is not a
MedMNIST requirement.

**Symptom:** the version or registry differs from the documented baseline.

**Recovery:** inspect `medmnist.__version__`, `len(medmnist.INFO)`, and the
public package metadata. Re-check the repository provenance file before relying
on exact details; a changed release may need a skill refresh.

## Root, files, and data validation

**Symptom:** `RuntimeError: Failed to setup the default root directory` or a
custom root error.

**Cause:** the `root` argument is missing, not a directory, or cannot be
created/accessed. Create an explicit writable directory and pass it to the
constructor; the package expects it to exist.

**Symptom:** `RuntimeError: Dataset not found`.

**Cause:** the exact file is absent. For `size=None`/`28`, use
`<flag>.npz`; for larger sizes use `<flag>_<size>.npz`. Either place the
official Zenodo file in the root after checking its checksum or deliberately set
`download=True` with network approval. Do not retry a download blindly.

**Symptom:** a local NPZ cannot be loaded, has missing keys, or has mismatched
image/label counts.

**Recovery:** inspect it with the bundled no-PyTorch checker or a local NumPy
snippet. A standard archive has six keys: `train_images`, `train_labels`,
`val_images`, `val_labels`, `test_images`, and `test_labels`; each image and
label pair must have the same first dimension and labels are normally `(N, L)`.
Do not silently resize or relabel an invalid archive.

## API and argument misuse

**Symptom:** `ValueError` for a split or an assertion/error for a size.

**Recovery:** use only `train`, `val`, or `test`. Use 28/default for all
subsets, 64 for all subsets, 128/224 only for 2D subsets. Confirm the selected
class in `INFO[flag]["python_class"]`; do not infer 2D versus 3D from a name
suffix alone.

**Symptom:** a 2D sample is not a tensor or a 3D sample has unexpected values.

**Cause:** the public API returns a Pillow image for 2D and a normalized,
channel-first NumPy array for 3D before any user transform. `as_rgb=True` turns
grayscale 2D images into RGB and repeats 3D data to three channels. Apply a
transform intentionally and record its output contract.

**Symptom:** memory use remains high despite `mmap_mode="r"`.

**Recovery:** `mmap_mode` is forwarded to `numpy.load` and is most useful for
large arrays, but NPZ members and later conversions may still materialize data.
Inspect actual array types and avoid converting a full high-resolution dataset
when a sample or a batch is enough.

## Download and optional dependencies

**Symptom:** automatic download reports a generic failure.

**Recovery:** treat it as a network or dependency problem. Check connectivity
to the official Zenodo URL, install/verify torchvision, download the exact
flag/size manually if policy allows, verify the published MD5, and put the file
under the explicit root. Keep a no-network local fixture for API diagnosis.

**Symptom:** `fire` is missing and `python -m medmnist` does not start.

**Recovery:** install the documented runtime dependency or use the Python APIs
directly. Do not replace a failed CLI parse with an unreviewed bulk command.

## Evaluation and output

**Symptom:** `Evaluator` rejects a root/file or `evaluate` asserts on the first
dimension.

**Recovery:** create the root, use the exact flag/size NPZ, and make the score
row count equal `evaluator.labels.shape[0]`. Scores are probabilities/scores,
not already-argmaxed labels. Binary accepts a 1D score or uses the last column
of a 2D score; multilabel requires `(N, L)`; multiclass/ordinal require one
column per class.

**Symptom:** ROC-AUC fails because a class has no positive or negative example.

**Recovery:** do not fabricate a metric. Check the split and fixture labels;
use a representative validation fixture or report that AUC is undefined. For
multilabel, every label column used in the average needs both classes.

**Symptom:** `parse_and_evaluate` cannot identify a dataset or split.

**Recovery:** use the standard filename with flag, optional `_size`, split, and
`@run`, for example
`pneumoniamnist_64_test_[AUC]0.900_[ACC]0.800@run1.csv`. The parser reads an
index column and headerless score columns and resolves the dataset through the
default root. For an isolated custom root, use direct `Evaluator` evaluation
or an explicit controlled wrapper rather than moving data into a default root
without approval.

**Symptom:** export fails or output is incomplete.

**Recovery:** create a new output directory, ensure all three split files exist
for the CLI `save` command, use `postfix="gif"` for 3D, and set
`write_csv=False` only when CSV output is intentionally unwanted. A montage
selects `length * length` samples; use `replace=True` for a tiny fixture.
Remember that the serializer appends to an existing CSV, so reruns can create
duplicates.

## Safety and scope

`download` can fetch substantial data, `clean` deletes downloaded `*mnist*.npz`
files, and the development-only `test` loops over all subsets and writes many
outputs. Run them only in an explicitly isolated context. MedMNIST is not
intended for clinical use; benchmark scores and labels must not be presented as
clinical diagnoses.
