# Experiment layout and lifecycle

## What `prep_exp` establishes

The live `utils.exp_utils.prep_exp` signature is:

```text
prep_exp(dataset_path, exp_path, server_env, use_stored_settings=True,
         is_training=True)
```

It returns the constructed config with runtime fields added:

- `exp_dir = exp_path`
- `test_dir = <exp_dir>/test`
- `plot_dir = <exp_dir>/plots`
- `experiment_name = exp_path.split("/")[-1]`
- `server_env = server_env`
- `created_fold_id_pickle = False`

For a new training-style experiment directory, the function creates `exp_dir`
and `plots`, and copies `configs.py` and `default_configs.py`. Depending on
`use_stored_settings`, it then copies model/backbone/config snapshots. The
implementation uses shell `cp`, `os.mkdir`, and source-relative paths; it is
not transactional and does not robustly quote paths. A failed copy can leave a
partial directory. Inspect before retrying and do not delete or overwrite a
partial snapshot without approval.

When stored settings are selected, the experiment snapshot is the source of
truth. The selected `model.py` and `backbone.py` are copied to temporary
`models/tmp_model.py` and `models/tmp_backbone.py` under the configured source
root, and `cf.model_path`/`cf.backbone_path` are redirected there. The source
checkout is therefore mutable during the legacy test path. Use a disposable
workspace or a controlled copy and record the exact snapshot version.

## Expected tree after preparation

A typical experiment directory is:

```text
<exp_dir>/
├── configs.py
├── default_configs.py
├── model.py
├── backbone.py
├── plots/
├── exec.log                 # after a logger is created
├── fold_ids.pickle          # for non-hold-out CV, created by data workflow
└── fold_<N>/                 # one per selected fold
    ├── exec.log
    ├── <epoch>_best_checkpoint/
    │   ├── params.pth
    │   ├── monitor_metrics.pickle
    │   └── epoch_ranking.npy
    ├── last_checkpoint/
    │   ├── params.pth
    │   ├── monitor_metrics.pickle
    │   └── epoch_ranking.npy
    └── ... plots/predictions/metrics ...
```

The exact set of outputs depends on the model, data loader, mode, and whether a
run completed. The directory is a versioned experiment snapshot, not a
portable dataset. `fold_ids.pickle` is not expected for a hold-out test set in
the same way; the loader instead uses the configured test path.

`ModelSelector` saves a last checkpoint every epoch and ranked best checkpoints
according to the configured validation criteria. It may remove checkpoints
that fall out of the top-k set. That deletion is part of training behavior and
is one reason this sub-skill never runs training as a validation step.

## Recommended lifecycle

### 1. Inspect and author

- Copy an existing experiment configuration into a new experiment module.
- Set `root_dir`/raw paths/preprocessed paths, `dim`, `model`, channels, patch
  sizes, classes, schedule, and hold-out/CV policy.
- Construct `configs(False)` in the inspection environment and print only
  relevant fields. Check that model/backbone files and data metadata exist.
- Keep `server_env=False` unless the deployment paths and data staging policy
  are explicitly available.

### 2. Onboard data

For a real dataset, use the data/preprocessing workflow and validate metadata
and array shape before any execution. For toy onboarding, generate a bounded
fixture with [generate_toy_fixture.py](../scripts/generate_toy_fixture.py),
then use a copied toy config whose `root_dir`, `pp_name`, `pp_data_path`,
`pp_test_name`, `pp_test_data_path`, and `n_train_val_data` match the fixture.
The original toy config requests 1,500 train/validation records; a bounded
fixture must lower that value or the toy loader asserts.

### 3. Prepare an experiment snapshot

Review the copy/mutation caveat first. `create_exp` is useful for cloud/job
submission because it captures configs and model scripts, but it is not a
transactional dry run. Prefer a fresh, dedicated `exp_dir`, confirm its parent
exists, and retain the log. Do not point it at the generated skill tree.

### 4. Select folds and run jobs

Use a bounded explicit fold list for a controlled job. For non-hold-out data,
ensure fold metadata is created by the data workflow. For hold-out data, ensure
the test path has the same schema as training data. Use stored settings when
resuming/testing a snapshot; keep the source and snapshot model versions
aligned.

### 5. Test or analyze

Testing expects model checkpoints and invokes the CUDA-backed predictor. It is
not covered by a successful config import. Analysis expects saved raw
predictions and can aggregate/evaluate without constructing a training model,
but still requires valid prediction records and stored config settings. Route
outputs and prediction schemas to
[inference-and-evaluation](../../inference-and-evaluation/SKILL.md).

## Toy fixture onboarding

The checked-in toy generator creates 320x320 two-plane `.npy` records (image
plus segmentation), per-record metadata pickles, and an aggregated
`info_df.pickle`. Its original entry point imports `configs` as a top-level
module and starts a 12-process pool; invoking it from the wrong directory can
fail with `ModuleNotFoundError`, and its default three experiments contain
thousands of files. It is reference evidence, not the safe helper.

Use the bundled helper instead:

```bash
python sub-skills/configuration-and-experiments/scripts/generate_toy_fixture.py \
  --output-dir /absolute/work/toy_mdt \
  --height 32 --width 32 --train-count 4 --test-count 2 --seed 7
```

The helper:

- generates deterministic, vectorized 2D image/segmentation pairs with a
  binary foreground label, suitable for schema/fixture checks rather than a
  complete historical loader manifest;
- writes separate `train/` and `test/` directories plus one JSON `manifest.json`
  and refuses to overwrite a non-empty output directory;
- caps counts and side lengths; it never starts a process pool, imports
  `configs`, runs a loader, or touches a source checkout;
- requires NumPy only. To use the historical loader, create the loader's
  expected manifest format separately and validate it before execution.

This is an onboarding fixture, not a performance benchmark or medical dataset.
A small fixture can validate paths and metadata only. It cannot validate model
quality or substitute for real preprocessing. For loader shape/metadata rules,
continue to [data-and-preprocessing](../../data-and-preprocessing/SKILL.md).
