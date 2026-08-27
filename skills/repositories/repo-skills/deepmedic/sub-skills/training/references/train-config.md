# DeepMedic train-config reference

A train config is executed as Python source by `TrainConfig(abs_path_to_cfg)`.
Use literals, lists, tuples, dictionaries, booleans, `None`, and comments only;
do not use shell syntax. Relative paths are resolved against the config file's
directory by the DeepMedic parser. The model config is a separate input to
`deepMedicRun -model` and is outside this reference.

## Minimum and output settings

```python
sessionName = "tinySmoke"
folderForOutput = "./output"
tensorboard_log = False
channelsTraining = ["./lists/train_t1.cfg", "./lists/train_t2.cfg"]
gtLabelsTraining = "./lists/train_labels.cfg"
# roiMasksTraining = "./lists/train_roi.cfg"
numberOfEpochs = 1
numberOfSubepochs = 1
numOfCasesLoadedPerSubepoch = 1
numberTrainingSegmentsLoadedOnGpuPerSubep = 8
batchsize_train = 2
num_processes_sampling = -1
```

`sessionName` defaults to `trainSession`; `tensorboard_log` defaults to false;
`batchsize_train` is required. The application accepts `dataframe_train` as an
alternative to direct lists. A training dataframe must contain one or more
`channel_*` columns, a `ground_truth` column, and may contain `roi_mask` and
`prediction_filename`; channel columns are sorted alphabetically. Do not
provide a dataframe with a different case ordering than the label list.

The direct lists are interpreted as follows:

| Key | Value | Requiredness |
|---|---|---|
| `channelsTraining` | list of file-list paths, one per modality | required without `dataframe_train` |
| `gtLabelsTraining` | file-list path, one label per case | required without `dataframe_train` |
| `roiMasksTraining` | file-list path, one mask per case | optional |
| `folderForOutput` | main session output directory | required |
| `cnnModelFilePath` | checkpoint prefix to load | optional; `-load` wins |
| `tensorboard_log` | boolean | optional, default `False` |

Each channel list and the label/mask lists must have the same case count and
order. File-list lines beginning with `#` or blank lines are ignored. A line
containing exactly `-` is a zero-filled missing modality sentinel for channel
lists. Paths inside a list are relative to that list file when resolved by the
runtime. NIFTI validity and preparation are covered by the data-preparation
skill, not this training skill.

## Sampling

The training key names are:

```python
typeOfSamplingForTraining = 3
proportionOfSamplesToExtractPerCategoryTraining = [1., 1.]
# weightedMapsForSamplingEachCategoryTrain = ["./lists/weights_fg.cfg", ...]
```

`SamplingType` accepts exactly four integer selectors:

| Selector | Name | Categories and map behavior |
|---:|---|---|
| `0` | Foreground/Background | foreground first, background second; uses GT and optional ROI, or exactly two weight maps |
| `1` | Uniform | one category; uniform over the volume or positive ROI, or one weight map |
| `2` | Whole-Image | one category; current implementation derives the same whole-volume/ROI map behavior as uniform, despite old comments saying not implemented |
| `3` | Per-Class | one category per output class, class `0` first; uses GT/ROI or one weight map per class |

The default training selector is `3`; the default validation selector is `1`.
For selectors `0` and `3`, proportions are normalized internally and must have
one item per category. For selectors `1` and `2`, proportions are ignored and
forced to `[1.0]`. Weight-map lists must have exactly as many category list
files as the selected type and each file must have one map per case. Negative
weight values are rejected. Empty categories are removed and the remaining
category probabilities are renormalized; if every category is empty, sampling
cannot proceed.

Sampling excludes centers too near image edges for the chosen high-resolution
segment. Sampling `n` segments distributes them among at most
`numOfCasesLoadedPerSubepoch` randomly selected subjects, then shuffles samples
and labels together. A non-positive or too-small sample budget can result in
zero full batches. Keep `numberTrainingSegmentsLoadedOnGpuPerSubep` at least
`batchsize_train` and preferably divisible by it.

Validation uses parallel keys with the `Val` suffix:

```python
performValidationOnSamplesThroughoutTraining = True
performFullInferenceOnValidationImagesEveryFewEpochs = False
channelsValidation = ["./lists/val_t1.cfg", "./lists/val_t2.cfg"]
gtLabelsValidation = "./lists/val_labels.cfg"
# roiMasksValidation = "./lists/val_roi.cfg"
typeOfSamplingForVal = 1
numberValidationSegmentsLoadedOnGpuPerSubep = 3000
batchsize_val_samples = 50
```

If either validation mode is enabled, `channelsValidation` is required. Sample
validation requires `gtLabelsValidation`. Full-volume validation requires a
positive `numberOfEpochsBetweenFullInferenceOnValImages` (default `1`) and,
when any prediction/probability/feature output is enabled, a
`namesForPredictionsPerCaseVal` list with one safe name per case. Full-volume
validation is expensive; run it infrequently during production and disable it
for a first smoke test.

## Epoch and sampling budgets

| Key | Default | Meaning |
|---|---:|---|
| `numberOfEpochs` | `35` | stopping target stored in trainer state |
| `numberOfSubepochs` | `20` | subepochs per epoch and metric/report cadence |
| `numOfCasesLoadedPerSubepoch` | `50` | maximum subjects loaded for one sampling job |
| `numberTrainingSegmentsLoadedOnGpuPerSubep` | `1000` | total train segments requested per subepoch |
| `batchsize_train` | none | train batch size; must be set |
| `num_processes_sampling` | `0` | `-1` sequential, `0` one sampling thread, positive child-process count |
| `numberValidationSegmentsLoadedOnGpuPerSubep` | `3000` | validation sample budget |
| `batchsize_val_samples` | `50` | validation sample batch size |
| `batchsize_val_whole` | `10` | full-volume inference batch size |

DeepMedic samples before each subepoch's training and validates first when
sample validation is enabled. `num_processes_sampling=0` overlaps sampling
with the current work using one thread; `-1` performs sampling in the main
thread and is easiest to debug. Parallel sampling can multiply file and memory
pressure.

## Learning-rate schedules

Select with `typeOfLearningRateSchedule`; the code asserts one of `stable`,
`predef`, `poly`, `auto`, or `expon`.

```python
learningRate = 0.001
whenDecreasingDivideLrBy = 2.0
numEpochsToWaitBeforeLoweringLr = 5
```

- `stable`: keeps the initial learning rate constant.
- `predef`: lowers at the integer epoch boundaries in
  `predefinedSchedule`, dividing by `whenDecreasingDivideLrBy` each time.
  `predefinedSchedule` is mandatory for this selector, for example
  `predefinedSchedule = [17, 22, 27]`. Epoch boundaries are interpreted by
  TensorFlow's piecewise-constant operation.
- `poly`: holds the initial value until `numEpochsToWaitBeforeLoweringLr`
  (default is roughly one third of `numberOfEpochs`), then follows the code's
  polynomial decay over the remaining epochs with exponent `0.9`, and holds
  the final value after the configured end.
- `auto`: requires sample validation. It tracks the best mean validation
  accuracy, considers an improvement significant only above
  `min_incr_of_val_acc_considered` (default `0.0`), waits
  `numEpochsToWaitBeforeLoweringLr` epochs, and divides the current rate by
  `whenDecreasingDivideLrBy`. Without sample validation the parser exits with
  an explicit configuration error.
- `expon`: supported by the current trainer but treated as legacy in source
  comments. Configure `paramsForExpSchedForLrAndMom = [final_learning_rate,
  final_momentum]` if using it. The code interpolates the learning rate after
  its wait window; verify the resulting logged LR for a production run because
  the momentum expression is legacy and its endpoint behavior is not as
  intuitive as the other schedules.

Schedule state is part of the trainer checkpoint. A normal resume restores it;
`-resetopt` discards it and reconstructs schedule state from the new config.

## Optimizer and regularization

```python
sgd0orAdam1orRms2 = 2
classicMom0OrNesterov1 = 1
momentumValue = 0.6
momNonNorm0orNormalized1 = 1
learningRate = 0.001
```

The selector is exact: `0` is custom SGD, `1` is custom Adam, and `2` is
custom RMSProp. SGD and RMSProp use momentum; `classicMom0OrNesterov1` selects
classic (`0`) or Nesterov (`1`) updates, and
`momNonNorm0orNormalized1` selects the gradient multiplier behavior. Valid
momentum values are inclusive `[0.0, 1.0]`.

Adam keys and defaults are `b1Adam=0.9`, `b2Adam=0.999`,
`epsilonAdam=1e-8`. RMSProp keys and defaults are `rhoRms=0.9` and
`epsilonRms=1e-4`. The source comments note that `1e-6` previously caused
unstable gradients in one trial; treat epsilon as a deliberate numerical
choice.

```python
losses_and_weights = {"xentr": 1.0, "iou": None, "dsc": None}
L1_reg = 0.000001
L2_reg = 0.0001
# Optional class-cost schedule:
# reweight_classes_in_cost = {"type": "per_c", "prms": [1., 1.], "schedule": [0, 10]}
```

At least one of `xentr`, `iou`, or `dsc` must have a non-`None` weight. L1 and
L2 regularization are added to the total cost. The hidden class-cost option
supports `type=None`, frequency weighting (`freq`), or per-class weights
(`per_c`) with one weight per output class and a two-element schedule.

## Augmentation dictionaries

Set either augmentation key to `None` or omit it to disable that level.
Validation never receives training augmentation.

Image-level affine augmentation is configured under `augm_img_prms_tr`:

```python
augm_img_prms_tr = {
    "affine": {
        "prob": 0.5,
        "max_rot_xyz": (15., 15., 15.),
        "max_scaling": 0.10,
        "seed": 7,
        "interp_order_imgs": 1,
        "interp_order_lbls": 0,
        "interp_order_roi": 0,
        "interp_order_wmaps": 1,
        "boundary_mode": "nearest",
    }
}
```

Defaults for omitted affine fields are probability `0.0`, rotations
`(45.,45.,45.)`, scaling `0.1`, no seed, image interpolation `1`, label/ROI
nearest-neighbor interpolation `0`, weight-map interpolation `1`, and
`nearest` boundary mode. Labels and masks must use interpolation order `0`;
using linear interpolation on labels corrupts class ids. Affine transforms are
applied to channels, labels, ROI, and sampling weight maps together and can be
slow.

Sample-level augmentation is configured under `augm_sample_prms_tr`:

```python
augm_sample_prms_tr = {
    "hist_dist": {
        "shift": {"mu": 0., "std": 0.05},
        "scale": {"mu": 1., "std": 0.01},
    },
    "reflect": [0.5, 0.0, 0.0],
    "rotate90": {
        "xy": {"0": 0.8, "90": 0.1, "180": 0.0, "270": 0.1},
        "yz": None,
        "xz": None,
    },
}
```

Histogram distortion samples per-channel shift and scale from Gaussian
parameters and applies `(image + shift) * scale`. Use `None` for either
`shift`, `scale`, or `reflect` to disable that operation. `reflect` contains
one probability per spatial axis. `rotate90` contains `xy`, `yz`, and `xz`
planes; each plane's four probabilities are normalized internally. The segment
must be isotropic for a requested plane rotation. Augmentation uses random
state and is not a reproducibility guarantee unless all relevant seeds and
data-loading order are controlled.

Deprecated compatibility keys exist (`reflectImagesPerAxis`, `performIntAugm`,
`sampleIntAugmShiftWithMuAndStd`, `sampleIntAugmMultiWithMuAndStd`), but prefer
the dictionaries above. `augm_params_tr` is rejected as deprecated rather than
silently converted.

## Preprocessing and compatibility checks

```python
run_input_checks = True
padInputImagesBool = True
norm_verbosity_lvl = 0
norm_zscore_prms = {
    "apply_to_all_channels": False,
    "apply_per_channel": None,
    "cutoff_percents": [5., 95.],
    "cutoff_times_std": [3., 3.],
    "cutoff_below_mean": False,
}
```

Input checks default to true and validate labels against the model's class
count. Padding defaults to true. Z-score normalization is disabled unless
`apply_to_all_channels=True` or `apply_per_channel` is a boolean list matching
training channel count. These two selectors are mutually exclusive. Cutoffs
may be percentile or standard-deviation bounds according to the preprocessing
implementation. Keep normalization policy identical between training and
inference unless there is a deliberate reason to change it.

## Validation output controls

```python
saveSegmentationVal = True
saveProbMapsForEachClassVal = [True, True]  # one boolean per class
suffixForSegmAndProbsDictVal = {"segm": "Segm", "prob": "ProbMapClass"}
numberOfEpochsBetweenFullInferenceOnValImages = 5
```

`saveProbMapsForEachClassVal` defaults to one `True` per output class when
full inference is active. `saveSegmentationVal` defaults true. Prediction names
are resolved into the training session's prediction directory. Feature-map
saving is available through the corresponding `saveIndividualFmsVal` and
min/max index settings, but it can consume substantial storage; leave it off
unless a specific diagnostic requires it.
