# Inference troubleshooting

Use the first concrete error in the session log, not the final catch-all
message. DeepMedic logs a traceback when the top-level session catches an
exception.

## Configuration and path failures

**`TestConfig` loads but required data is `None`.** The parser returns `None`
for an absent variable. Confirm `folderForOutput`, `channels`, and
`namesForPredictionsPerCase` for legacy input, or provide a valid `dataframe`.
Remember that paths in a config are relative to the config file, while a
command-line `-load` path is relative to the process working directory.

**Case count mismatch or wrong case ordering.** Every channel list, ROI list,
label list, and legacy output-name list must have the same number of entries.
Compare rows after removing comments and blank lines. Channel lists are zipped
by row; a single shifted row silently pairs the wrong modality with a case.

**Output names are rejected or unexpected.** Names must not contain `/` or
start with `.`. The saver appends `_Segm.nii.gz` or
`_ProbMapClassN.nii.gz` to a basename. If a name already has `.nii.gz`, the
extension is removed before appending. A dataframe's `prediction_filename`
column replaces the legacy names list.

**No files appear where expected.** The test session nests results below
`<folderForOutput>/predictions/<sessionName>/predictions/`; feature files go in
the sibling `features/` directory. Check the configured `sessionName`,
custom suffix dictionary, and the log's printed output paths. Use the bundled
presence checker only against the actual prediction directory.

## Checkpoint and architecture failures

**No checkpoint / random initialization prompt.** Provide `cnnModelFilePath`
or `-load`. In automation, do not accept random initialization. A directory is
resolved with TensorFlow's latest-checkpoint lookup; verify that it contains the
intended checkpoint.

**`NotFoundError` on restore.** Give the checkpoint prefix ending at
`.model.ckpt`. Do not give `.index`, `.meta`, or
`.data-00000-of-00001`. Verify that the prefix's companion files exist and are
readable. The package has an interactive helper that may offer to shorten an
accidentally overlong prefix; non-interactive runs should correct the path
before retrying instead of relying on the prompt.

**`DataLossError`, variable not found, or shape mismatch.** Rebuild the graph
using the exact model configuration that made the checkpoint. Compare class
count, input channels, normal/subsampled/FC pathway structure, number of layers,
kernels, subsampling factors, residual/lower-rank choices, and FC sizes. A
checkpoint from a superficially similar model is not compatible. Do not solve a
restore error by disabling input checks or changing the test data.

**Segment dimension error.** `segmentsDimInference` must be at least as large
as the normal pathway receptive field. Reduce it only to another valid size;
changing architecture to fit a checkpoint is not a valid inference repair.

## NIFTI, ROI, and preprocessing failures

**NIFTI load error or an assertion about dimensions.** DeepMedic accepts 2D
NIFTI by expanding a singleton third axis and accepts 4D only when the fourth
axis is 1. Confirm files are readable, not multi-volume time series, and use
`.nii`/`.nii.gz`. Check every modality, ROI, and label for the same 3D shape.

**Label class error.** Labels are rounded to integer type on load. With input
checks enabled, any label greater than `numberOfOutputClasses - 1` is rejected.
Remap labels to background 0 and consecutive IDs, or use the correct model;
do not simply turn off checks to hide invalid classes.

**Empty or all-zero prediction with an ROI.** The tile generator skips tiles
with no positive ROI and postprocessing zeros all outputs outside the ROI.
Inspect ROI dimensions, affine, orientation convention, and positive voxel
count. A mask in another space can eliminate every tile. Run once without the
ROI only as a diagnostic, not as a replacement for a required ROI.

**Border artifacts or truncated edges.** Keep `padInputImagesBool=True` for
full border coverage. With padding disabled, the code intentionally does not
pad and edge predictions may be incomplete. Confirm that output shape returns
to the original shape after unpadding.

**NaN/Inf after normalization.** Z-score normalization can divide by zero for
a constant eligible region. Check ROI occupancy and intensity variance. Disable
normalization only if the model was trained without it; otherwise fix the input
or normalization policy to match training.

**Unexpected intensity or poor DSC despite valid files.** Inference
normalization must match training. Compare whether training used ROI-based
z-score, percentile/std cutoffs, and `cutoff_below_mean`. Also verify that the
channel list order matches the model's expected modality order.

## Tiling, memory, and performance

**Out-of-memory or process killed.** Lower `batchsize` first. Then choose a
smaller valid `segmentsDimInference`; it changes per-tile memory and speed but
must remain no smaller than the receptive field. Restrict the ROI when a valid
ROI exists. Do not request feature maps during the first full-volume test.

**Inference is unexpectedly slow.** Full-volume tiling performs a forward pass
for every tile. A larger valid inference segment can reduce tile count but
increases memory. A positive ROI can skip empty tiles. CPU is useful for
correctness but can be much slower for large 3D models.

**Feature stitching error or missing feature files.** Set
`saveIndividualFms=True` only with three pathway structures whose layer entries
match the model. Each selected range is `[low, high)` and empty lists skip a
layer. Start with one layer and a small range such as `[0, 1]`. The runtime
clamps a high bound above the layer's FM count, but it cannot repair missing
layer entries or malformed nesting.

**Disk exhaustion while saving features.** Every selected activation is
stitched as a float32 volume and saved separately. Number of output files and
bytes scale with cases × selected maps × volume voxels. Narrow ranges, split
sessions, or omit features. The old documentation's all-FMs 4D option is not
wired into the current `TestSession` inference path.

## Device/runtime failures

**`-dev` rejected.** Valid values are `cpu`, `cuda`, and `cuda` followed by an
integer, such as `cuda0`. A bare or differently spelled device value fails
before the session starts.

**GPU requested but TensorFlow cannot initialize CUDA.** Confirm the installed
TensorFlow build, CUDA, cuDNN, driver, and GPU compute capability are mutually
compatible. Verify device visibility in the log. Run the same configuration on
CPU to separate runtime issues from checkpoint/data issues. Do not treat a
fallback warning as proof that a CUDA request succeeded.

**CPU run uses unexpectedly large memory.** TensorFlow's test session creates a
compatibility session with generous device counts. Keep tile `batchsize` low,
avoid simultaneous feature extraction, and run one case at a time when
necessary.

## Output validation failures

**Checker reports missing probabilities.** Confirm `saveProbMapsForEachClass`
length and booleans, the model's class count, and `--prob-classes` passed to
the checker. A disabled class is an intentional absence; rerun the checker
with the actual enabled class expectation or enable it in a new session.

**Checker reports missing features.** Ensure `--require-features` was used
only when `saveIndividualFms=True`, and point `--feature-dir` at the session's
`features` sibling. Check the exact case basename and selected ranges. The
checker never creates, renames, or deletes outputs.

**DSC is NA.** `calculate_dice` returns NA when the relevant GT foreground is
empty. Preserve NA in summaries and inspect class prevalence; it is different
from a failed prediction with DSC 0.
