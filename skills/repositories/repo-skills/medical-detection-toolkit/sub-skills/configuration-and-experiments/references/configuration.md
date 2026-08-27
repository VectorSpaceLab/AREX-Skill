# Configuration contract

This reference distills the configuration behavior from `default_configs.py`
and the three checked-in experiment configurations. It is a contract for
inspection and authoring, not a promise that old training code runs on a
modern stack.

## Constructor order and subclass shape

A new experiment is conventionally an `experiments/<name>/configs.py` module
with a lowercase class named `configs`:

```python
from default_configs import DefaultConfigs

class configs(DefaultConfigs):
    def __init__(self, server_env=None):
        self.root_dir = "/data/project"       # experiment-specific inputs
        self.dim = 2                           # 2 or 3
        self.model = "retina_unet"             # dispatch key
        DefaultConfigs.__init__(self, self.model, server_env, self.dim)
        self.pp_data_path = "/data/project/preprocessed"
        # set channels, patch sizes, schedule, classes, and model-specific knobs
```

The base initializer signature is:

```text
DefaultConfigs(model, server_env=None, dim=2)
```

The live inspection environment confirms this signature. The base initializer
sets `model`, `dim`, `source_dir`, `input_df_name`, and `model_path`; it also
sets common I/O, loader, architecture, schedule, testing, and MRCNN defaults.
The subclass must set `model` and `dim` before calling it. Settings assigned
later intentionally override base defaults.

The experiment configurations import `DefaultConfigs` from the repository root
and use `configs(server_env=None)`. They are not package-independent modules:
import them with the repository/package import context available, and do not
copy their absolute example data paths into a new project.

## Model and dimension selection

The checked-in choices are:

| Choice | Evidence-backed use | Configuration consequences |
|---|---|---|
| `dim=2` | toy and LIDC examples | `patch_size_2D`, 2D backbone shapes, 4-coordinate boxes; optional neighbouring slices can expand channels |
| `dim=3` | PET/CT TNM example | `patch_size_3D`, 3D backbone shapes, 6-coordinate boxes, different z strides and augmentation constraints |
| `mrcnn` | toy default | shared MRCNN-style model-specific defaults |
| `retina_unet` | LIDC and PET/CT defaults | Retina anchor expansion and stride-1 decoder behavior |
| `retina_net` | shared dispatch and comments | Retina anchor expansion without the `retina_unet` stride-1 setting |
| `detection_unet` | shared dispatch | segmentation-to-object aggregation settings from `add_det_unet_configs` |
| `ufrcnn` | shared dispatch; LIDC additionally changes segmentation/FRCNN flags | MRCNN-style settings with U-FRCNN-specific overrides |
| `ufrcnn_surrounding` | shared default dispatch only | do not select unless the installed model/config implementation supports it |
| `prob_detector` | shared default dispatch and PET/CT model branch | probabilistic monitoring/latent settings; verify that the target checkout contains the implementation |

The comments in the source mention `detection_unet` twice and do not constitute
an exhaustive compatibility matrix. Treat the model dispatch dictionary in the
actual version as authoritative. A missing dispatch key raises a `KeyError`
while constructing the config; an unavailable model file fails later when the
CLI dynamically imports `cf.model_path`.

For 2D/3D changes, set all dimension-dependent values together:

- `patch_size_2D` / `pre_crop_size_2D` versus `patch_size_3D` /
  `pre_crop_size_3D`, then derive `patch_size` and `pre_crop_size` from `dim`.
- `channels` and `n_channels`; if `n_3D_context` is non-`None` with `dim=2`,
  `n_channels` becomes `len(channels) * (2 * n_3D_context + 1)`.
- model-specific feature-map, anchor, pool, box-standard-deviation, window,
  and backbone-shape settings. Do not hand-copy these internals without using
  [models-and-architectures](../../models-and-architectures/SKILL.md).
- augmentation angles: the checked-in 3D configs disable elastic deformation
  and x/y rotations and retain z rotation. A 2D configuration may use x
  rotation and elastic deformation.
- whether 2D predictions are merged into 3D (`merge_2D_to_3D_preds`). This is a
  data/inference contract; route details to the sibling nodes.

## Paths and stored data

Common base values include:

- `source_dir`: computed from the installed source location, or replaced by a
  legacy hard-coded deployment path when `server_env` is true.
- `backbone_path`: `models/backbone.py` by default.
- `model_path`: `models/<model>.py` by default.
- `input_df_name`: `info_df.pickle` by default.
- `root_dir`, `raw_data_dir`, `pp_dir`, `pp_name`, `pp_data_path`, and
  `pp_test_data_path`: experiment-specific and often machine-specific.

The examples illustrate three distinct layouts:

- **Toy:** separate `train` and `test` directories under a selected toy mode;
  `hold_out_test_set=True`; 2D; one channel; `n_train_val_data=1500` in the
  original example.
- **LIDC:** raw NRRD and preprocessing paths are separate from the
  preprocessed path; test reuses the same preprocessed root; `hold_out_test_set`
  is false, so cross-validation fold metadata supplies the test split.
- **PET/CT TNM:** 3D, two channels, hold-out test data, and a separate
  `pp_test_out_path` in the example. Its validation is disabled despite a
  `val_mode` value being present.

Use paths that are readable and writable by the invoking job. Validate the
preprocessed data contract in
[../data-and-preprocessing/references/data-formats.md](../../data-and-preprocessing/references/data-formats.md)
before creating an experiment. Never embed a private data acquisition path in
an exported skill or fixture.

## Schedule and class contract

Values that must agree rather than merely be present:

- `learning_rate` must have one entry per `num_epochs`; PET/CT explicitly
  asserts this. A schedule shorter than the epoch loop is a config error.
- `class_dict` maps foreground integer IDs to display names; background is 0.
  `head_classes` is normally foreground class count plus background. Align
  `class_dict`, annotation labels, `num_seg_classes`, and model heads.
- `report_score_level`, `patient_class_of_interest`, `ap_match_ious`,
  `model_selection_criteria`, and `min_det_thresh` must name metrics/classes
  that the evaluator can produce.
- `hold_out_test_set` determines whether testing reads a separate
  `pp_test_data_path` or uses a fold-derived test subset.
- `val_mode` is `val_sampling` or `val_patient` in the examples. Set the
  corresponding `num_val_batches` or `max_val_patients` when applicable.
- `select_prototype_subset` is an optional bounded dataset subset. It does not
  repair a dataset smaller than `n_train_val_data` in the toy loader.

Common shared defaults from `DefaultConfigs` include seed 0, 8 workers locally
(or 16 for `server_env`), `n_cv_splits=5`, test mirroring enabled, no hold-out
set, `merge_3D_iou=0.1`, one monitoring figure, CSV prediction output, and
`max_test_patients="all"`. Experiment settings can override all of these.

## Safe authoring checklist

Before invoking the CLI, statically or interactively verify without training:

1. `configs(server_env=False)` imports and constructs with the intended model
   and dimension.
2. `cf.model_path`, `cf.backbone_path`, and the data paths resolve under the
   intended installation/workspace; example paths such as `/path/to/raw/data`
   are not left active.
3. `len(cf.learning_rate) == cf.num_epochs` and class/metric names are aligned.
4. `patch_size`, `pre_crop_size`, channels, and annotation dimensionality agree.
5. `n_cv_splits` and requested folds agree with hold-out versus CV behavior.
6. A bounded toy fixture has enough records for `n_train_val_data`, or the
   copied toy config explicitly lowers that value.
7. The experiment directory policy is chosen: create a new directory, resume
   from a complete snapshot, or stop and repair the snapshot with approval.

A successful config import is not proof that the model, custom operations,
data loader, or CUDA runtime is usable.
