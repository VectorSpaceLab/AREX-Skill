# Inference workflows

## A. Prepare a portable test run

1. **Freeze the architecture identity.** Record the model configuration file
   version/hash, number of input channels, number of output classes, pathway
   definitions, and `segmentsDimInference`. The latter controls speed and
   memory but must be at least the normal-path receptive field. Do not alter
   architecture values merely to make a checkpoint load.
2. **Inventory each case.** For each channel, make one list row per case. Make
   sure the row order is identical in all channel, ROI, label, and prediction
   name lists. Inspect NIFTI shapes and affines before running. A missing
   optional ROI or label should be omitted consistently rather than represented
   by a path that does not exist.
3. **Choose preprocessing deliberately.** Use padding for normal border
   coverage. Enable z-score normalization only when it matches the training
   preprocessing; normalization changes the model's input distribution. Keep
   `run_input_checks=True` for initial runs.
4. **Choose outputs deliberately.** Leave segmentation and probabilities on for
   a first run. If probabilities are not needed, disable individual classes
   explicitly. Request a small feature range only after ordinary prediction
   succeeds.
5. **Choose a checkpoint prefix.** The path must identify a TensorFlow
   checkpoint prefix ending at `.model.ckpt`; do not append `.index` or a data
   shard. A checkpoint directory is valid when its latest checkpoint is the
   intended one.

## B. Run CPU smoke inference

Use the installed executable and package environment, not a source-tree path:

```text
deepMedicRun -model /work/config/model.cfg -test /work/config/test.cfg -load /models/run.final.model.ckpt -dev cpu
```

Use one small case and a reduced `batchsize` if memory is uncertain. Confirm
that the log reports the intended case count and says parameters were loaded.
The CLI catches and logs exceptions; inspect the log and exit status instead of
assuming a successful shell return means predictions are valid.

The CPU smoke pass is also the safest way to identify config/list path errors,
shape mismatch, class-label errors, checkpoint prefix mistakes, and output
naming problems before allocating GPU resources.

## C. Run CUDA inference

After a CPU smoke pass, use:

```text
deepMedicRun -model /work/config/model.cfg -test /work/config/test.cfg -load /models/run.final.model.ckpt -dev cuda0
```

`cuda0` masks the process to physical GPU 0 and binds the TensorFlow graph to
its masked GPU 0. `cuda` leaves available GPUs visible and lets TensorFlow
choose. `cpu` explicitly clears `CUDA_VISIBLE_DEVICES`. Verify the selected
runtime in the session log/device listing and with the host's own GPU monitor;
do not infer GPU use from the command alone. If CUDA initialization fails,
repeat the smoke run on CPU and resolve TensorFlow/CUDA/cuDNN compatibility
rather than changing the model or data.

For memory pressure, lower `batchsize` first. If a single tile still cannot fit,
reduce `segmentsDimInference` while preserving the receptive-field minimum and
then re-check that the checkpoint architecture itself was not changed.

## D. Understand tiling and ROI behavior

For the normal pathway, DeepMedic computes `outp_pred_dims` from the input
segment and CNN and uses that as the tiling stride. Each tile produces class
probabilities for its central predicted region. The stitcher places those
regions at the correct offset after the unpredicted margin; it does not average
overlapping predictions. The tile generator extends the final tile to the far
boundary, so edge coverage is complete when padding is enabled.

With an ROI, a tile is skipped if the ROI portion of that tile contains no
positive voxel. This is a compute optimization. After stitching and unpadding,
all predicted classes are multiplied by the ROI, so the saved segmentation and
probability maps are zero outside it. An ROI that is empty or misregistered can
therefore produce an apparently empty result; check ROI shape and positive
voxel count before interpreting it.

With `padInputImagesBool=False`, inference can be faster but border coverage
may be incomplete. The code does not add padding in this mode, so use it only
when the task accepts the border behavior.

## E. Evaluate DSC

Provide `gtLabels` only for cases whose labels are aligned with the channels.
DeepMedic evaluates after unpadding and calculates, for every class:

- **DICE1:** whole-volume prediction versus whole-volume GT.
- **DICE2:** ROI-masked prediction versus whole-volume GT.
- **DICE3:** ROI-masked prediction versus ROI-masked GT.

Class 0 in the report is whole foreground (`prediction > 0` and `GT > 0`),
while classes 1 through `n_classes - 1` are exact rounded labels. The direct
API `calculate_dice(pred_seg, gt_lbl)` returns `-1` when GT has no positive
voxels; the reporting layer renders this as NA. Do not replace NA with zero in
aggregate analyses. If there is no ROI, DICE2 and DICE3 collapse to the whole
volume comparison in practice.

A DSC log is a model/data check, not a substitute for validating NIFTI geometry.
Record class count, ROI use, and whether any class was absent when comparing
runs.

## F. Validate saved outputs

From the session's nested prediction directory, run:

```text
python scripts/check_inference_outputs.py /work/results/predictions/session/predictions caseA caseB --prob-classes 3
```

If features were requested, provide the sibling directory and require them:

```text
python scripts/check_inference_outputs.py /work/results/predictions/session/predictions caseA caseB --prob-classes 3 --require-features --feature-dir /work/results/predictions/session/features
```

The checker is presence-oriented and does not mutate files. Follow it with a
NIFTI-aware check in the consuming pipeline for shape, affine, finite values,
label range, and probability normalization. If custom suffixes were used,
pass `--seg-suffix` and `--prob-suffix` to mirror the config.

## G. Feature-map-only pass

Use a separate test session when possible. Set `saveSegmentation=False` and
select only the `[low, high)` ranges needed from each pathway/layer. Keep the
same model config, checkpoint, input lists, ROI, padding, normalization, and
batch size as the prediction pass. This isolates storage-heavy visualization
from the clinically relevant segmentation outputs. There is no current
`TestSession` switch that writes all activations as one 4D image; use the
individual FM output behavior documented in the test-config reference.

## H. Programmatic API use

For an installed package, the low-level session path is conceptually:

```python
from deepmedic.frontEnd.configParsing.testConfig import TestConfig
cfg = TestConfig("/work/config/test.cfg")
```

The public session orchestration is still CLI-oriented: the test session builds
its TensorFlow graph from model parameters, restores a `Saver`, and calls
`inference_on_whole_volumes`. Treat the argument list to that routine as an
internal compatibility surface. If calling it directly, preserve the order of
channels, labels, ROI paths, output names, suffix dictionary, batch size,
preprocessing options, FM ranges, and input shapes exactly as the package
session supplies them.
