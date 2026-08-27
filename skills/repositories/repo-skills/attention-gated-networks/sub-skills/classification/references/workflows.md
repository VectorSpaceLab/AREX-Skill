# Classification Workflows

## Purpose

Read this for practical ultrasound classification runs, model inspection, and
attention-map export. The source repo is legacy PyTorch code; treat every
workflow as CUDA-first unless you have patched the source to run on CPU.

## Install and smoke check

After installing the repository and its dependencies, run the root environment
checker from the generated skill:

```bash
python ../../scripts/check_env.py --repo-root /path/to/Attention-Gated-Networks --mode classification
```

The expected signal is a CUDA model construction plus an output line like:

```text
classification-output=(2, 14)
check-env-ok
```

If this fails before model construction, read the root troubleshooting reference
and this sub-skill's [troubleshooting](troubleshooting.md).

## Train a Sononet classifier

1. Copy one of the bundled config patterns from the source repository into your
   run directory. Use the plain Sononet config for a baseline and one of the
   grid-attention configs for attention experiments.
2. Replace the dataset path in `data_path.us` with the current HDF5 file.
3. Confirm that `model.output_nc` matches the number of `label_names` in the
   HDF5 file.
4. Confirm the sampler branch:
   - use `weighted2` for the documented ultrasound setup;
   - use the plain weighted branch for non-14-class experiments;
   - use `stratified` only if you accept its hard-coded 14-class assumption.

The checkout/package, HDF5 file, and any trained checkpoint are external runtime
inputs. For every relative `--config`, pass `--repo-root`; the helper resolves
the config from that root and config-relative data paths from the config parent.
Run `check_env.py --config ...` first to reject unavailable or private `/vol/...`
paths rather than pretending the dataset exists.
5. Keep `model.gpu_ids` non-empty when using unmodified source modules.
6. Start training with the bundled replacement script:

```bash
python scripts/run_classifier.py \
  --repo-root /path/to/Attention-Gated-Networks \
  --config path/to/config.json \
  --mode train
```

The script loads `json_opts.training.arch_type`, builds `UltraSoundDataset` for
`train`, `val`, and `test`, constructs `get_model(json_opts.model)`, and writes
checkpoints below `model.checkpoints_dir/model.experiment_name`.

### Debug-only model inspection

The source root CLI exposes `--debug`, but the debug path calls GPU timing
helpers that can run many benchmark iterations. Prefer the generated smoke
checker for fast shape and model-construction validation.

## Evaluate a classifier checkpoint

1. Use the same model and data config family as training.
2. Set `model.isTrain` to `false`, set `model.path_pre_trained_model` when using
   a specific checkpoint file, or set `model.which_epoch` when loading from the
   experiment checkpoint directory.
3. Run the bundled replacement:

```bash
python scripts/run_classifier.py \
  --repo-root /path/to/Attention-Gated-Networks \
  --config path/to/config.json \
  --mode test
```

The script accumulates classification loss and metrics, writes plots/logs via
`Visualiser`, and serializes `test_result.pkl` in the model save directory.

## Choose an attention classifier

| Goal | Config/model fields |
| --- | --- |
| Baseline ultrasound classifier | `model.type='classifier'`, `model.model_type='sononet2'` |
| Grid-attention classifier with mean aggregation | `model.type='aggregated_classifier'`, `model.model_type='sononet_grid_attention'`, `aggregation_mode='mean'`, `aggregation='mean'` |
| Deep-supervision grid attention | `aggregation_mode='deep_sup'`, `weight=[1, 0.1, 0.1, 0.1]`, `aggregation='idx'`, `aggregation_param=0` |
| Fine-tuning aggregation layer | `aggregation_mode='ft'` |

`sononet_grid_attention` exposes attention layers named
`compatibility_score1` and `compatibility_score2`. The generated overlay helper
uses those names by default.

## Export attention overlays safely

The source `visualise_attention.py` is not reusable as-is: it hard-codes private
config paths, output directories, and visualization sampling choices. Use the
bundled helper instead:

```bash
python scripts/export_attention_overlay.py \
  --repo-root /path/to/Attention-Gated-Networks \
  --config configs/config_sononet_grid_att_8.json \
  --output-dir /tmp/ag-net-attention \
  --synthetic
```

For real data, save one preprocessed 2D image as a NumPy array and pass
`--input-npy sample.npy`. If you have a trained checkpoint, pass
`--checkpoint path/to/checkpoint.pth`. The helper writes per-layer overlays,
attention arrays, input arrays, and a mean overlay into the output directory.

## Validation checklist before expensive runs

- `python scripts/run_classifier.py --help` works.
- `python ../../scripts/check_env.py --repo-root /path/to/repo --mode classification` succeeds.
- HDF5 keys and labels match [data-layout](data-layout.md).
- The config's `visualisation.display_id` is `0` or a Visdom server is running.
- The checkpoint directory is writable.
- CUDA memory is adequate for the chosen `batchSize`, image size, and feature scale.
