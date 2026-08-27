# Test configuration reference

DeepMedic test configuration files are trusted Python files. `TestConfig` loads
the file with the package's `Config` class, and missing variables become
`None`; requiredness is enforced later by path construction or model/session
code rather than by a single schema validator. Keep configs small, explicit,
and version-controlled with the experiment.

## Core variables

| Variable | Requiredness | Meaning and effective default |
|---|---|---|
| `sessionName` | optional | Output-session name; defaults to `testSession`. |
| `folderForOutput` | required | Main writable output directory. Relative paths are resolved relative to the test config. |
| `cnnModelFilePath` | required in practice unless `-load` is used | TensorFlow checkpoint prefix or checkpoint directory. `-load` overrides it. |
| `channels` | required for legacy input | List of channel-list files; one entry per model input channel. Each list has one NIFTI path (or `-`) per case. |
| `namesForPredictionsPerCase` | required for legacy input | List of one output name per case. Use names without `/` or a leading `.`; the source includes a name-convention helper, although this current test-session path does not call it consistently. |
| `dataframe` | alternative to `channels` | CSV path. Columns `channel_*` are sorted alphabetically; optional `ground_truth`, `roi_mask`, and `prediction_filename` columns are recognized. |
| `roiMasks` | optional | List file with one ROI NIFTI per case. Missing means full-volume tiling. |
| `gtLabels` | optional | List file with one label NIFTI per case. Supplying it enables DSC reporting. |

Do not set both input styles casually. If `dataframe` is not `None`, the
session takes channels, labels, ROIs, and output names from the CSV and does
not use the legacy `channels`, `roiMasks`, `gtLabels`, or names list for those
values. A dataframe with no `prediction_filename` column falls back to
DeepMedic's generated `pred_caseN.nii.gz` names for multiple cases (or uses the
prediction directory for a single case). The CSV is read with pandas and paths
that are relative to it are normalized against the CSV directory.

A minimal legacy shape is:

```python
sessionName = "unseen_cases"
folderForOutput = "/work/results"
cnnModelFilePath = "/models/task.final.model.ckpt"
channels = ["/inputs/channel_t1.list", "/inputs/channel_flair.list"]
namesForPredictionsPerCase = "/inputs/prediction_names.list"
```

The channel list files and optional ROI/label list files are plain text: blank
lines and lines beginning with `#` are ignored; `-` is reserved for a
zero-filled input channel. The number of rows must match across all lists. A
zero-filled channel still counts toward the model input-channel count. Although
the current parser does not invoke its name-convention helper on every path,
keep output names free of `/` and a leading `.` so the generated files remain
portable and predictable.

## Saving and naming

| Variable | Effective default | Notes |
|---|---|---|
| `saveSegmentation` | `True` | Boolean. Set false only when segmentation is intentionally not needed. |
| `saveProbMapsForEachClass` | `[True] * n_classes` | List of booleans; a true entry saves that class's map. An empty list is treated as all true. |
| `suffixForSegmAndProbsDict` | `{"segm": "Segm", "prob": "ProbMapClass"}` | Custom suffix dictionary. Probability class index is appended to `prob`. |
| `batchsize` | `10` | Number of tiles processed per TensorFlow forward pass. Smaller values reduce peak memory; larger values may improve throughput. |
| `saveIndividualFms` | `False` | Enables selected activation-map reconstruction. |
| `minMaxIndicesOfFmsToSaveFromEachLayerOfNormalPathway` | `[]` when FM saving is off | Per-layer `[low, high)` ranges, zero-based. |
| `minMaxIndicesOfFmsToSaveFromEachLayerOfSubsampledPathway` | `[]` when FM saving is off | Same contract for subsampled pathways. |
| `minMaxIndicesOfFmsToSaveFromEachLayerOfFullyConnectedPathway` | `[]` when FM saving is off | Same contract for FC pathways. |

The saver derives the output path from each case name:

- A name ending `.nii.gz` or `.nii` has that extension removed, then receives
  `_<suffix>.nii.gz`.
- Any other name receives `_<suffix>.nii.gz`.
- A single case with a name that is an existing directory is written as
  `<directory>/<suffix>.nii.gz`; do not rely on this special case for portable
  manifests.
- Individual feature names are `<case-base>_pathway<P>_layer<L>_fm<F>.nii.gz`
  in the session `features` directory. Pathway, layer, and FM numbering are
  zero-based.

The parser does not use the old documentation's `saveAllFmsIn4DimImage`
variable in this testing path. The current inference routine saves individual
feature maps through `saveIndividualFms`; any 4D helper is not wired into
`TestSession`'s current output path. Treat that older option as a documentation
mismatch, not as a promise of a 4D file.

## Preprocessing and checks

| Variable | Effective default | Behavior |
|---|---|---|
| `run_input_checks` | `True` | Checks label values against the model class count when labels are present. Keep true during first runs. |
| `padInputImagesBool` | `True` | Reflect-pads channels, labels, and ROI by the unpredicted margin so borders can be covered. Outputs are unpadded before saving. |
| `norm_verbosity_lvl` | `0` | `0` no normalization details, `1` per-subject timing, `2` per-channel stats. |
| `norm_zscore_prms` | no channel normalization | Dictionary described below. |

The z-score dictionary starts with:

```python
norm_zscore_prms = {
    "apply_to_all_channels": False,
    "apply_per_channel": None,
    "cutoff_percents": None,
    "cutoff_times_std": None,
    "cutoff_below_mean": False,
}
```

Set `apply_to_all_channels=True` **or** provide a boolean list in
`apply_per_channel`, never both. A per-channel list must have one boolean per
`channels` entry. Percentile cutoffs are `[low, high]` in `[0, 100]`; standard
deviation cutoffs are `[low, high]` positive multipliers. If an ROI exists,
normalization statistics are computed from positive ROI voxels; otherwise all
voxels are eligible. A zero standard deviation can make normalization
non-finite, so inspect logs and output values when a modality is constant.

Input checks are not a full registration validator. Before invoking DeepMedic,
check that all modalities, labels, and ROIs for a case have the same spatial
shape and intended affine. Labels are rounded/cast to int16 when loaded if
needed; ROI values are rounded/cast to int16 when needed. Class IDs above
`numberOfOutputClasses - 1` raise an error when checks are enabled.

## Output/session folders

`folderForOutput` is expanded to an absolute main folder. The test session
creates:

```text
<folderForOutput>/logs/
<folderForOutput>/predictions/<sessionName>/predictions/
<folderForOutput>/predictions/<sessionName>/features/
```

The logger writes `<sessionName>.txt` in `logs`. Prediction NIFTIs are in the
nested `predictions` folder; feature NIFTIs are in the sibling `features`
folder. The output folder is created before configuration paths are compiled,
so a relative `folderForOutput` is interpreted from the config file, not from
the final prediction directory.

## Checkpoint and architecture invariants

`TestSessionParameters` resolves a config checkpoint relative to the config
file. A command-line checkpoint is made absolute relative to the current
working directory and replaces the config value, with a warning if both were
provided. If the config value is a directory, TensorFlow's
`latest_checkpoint()` is used. Otherwise the supplied prefix is restored
verbatim after the package's checkpoint-prefix adjustment helper.

The graph is built from the model config before restore. It creates the `net`
variable scope, builds placeholders for the test segment dimensions, and uses
a TensorFlow v1-compatible `Saver` over the network variables. A checkpoint
must therefore match variable names and shapes. Matching only the number of
classes is insufficient: input channels, path count, kernels, layers,
subsampling, and FC dimensions all matter.

## Feature range syntax

When `saveIndividualFms=True`, provide three structures indexed by pathway
type: normal, subsampled, and fully connected. Each structure should have one
entry per layer. Use `[]` for a layer that is not requested; use `[low, high]`
for a half-open FM range. The runtime clamps `high` to the actual number of
FMs in that layer, but malformed structure lengths can still fail while
stitching. Confirm layer count and FM count in the model/session log before a
large request.

Feature maps are reconstructed from the same tiles as predictions. Subsampled
pathway activations are expanded by the pathway's subsampling factor and
cropped to the high-resolution output dimensions. This is why they are useful
for visualization but should not be interpreted as native-resolution logits.
Saving a full volume for many layers and maps allocates one float32 volume per
selected map and then writes each map separately. Limit ranges, cases, or run
features in a separate pass.
