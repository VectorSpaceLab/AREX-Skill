---
name: classification-workflows
description: "Route and validate PointCNN TensorFlow 1.x graph-mode
  classification workflows, settings, inputs, and run artifacts for the
  supported datasets."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Classification workflows

Use this sub-skill to prepare or run the repository's **classification** trainer. It covers ModelNet40, ScanNet object classification, TU-Berlin, Quick Draw, MNIST, and CIFAR-10. This is legacy TensorFlow 1.x graph-mode code; use a compatible Python/TensorFlow 1.x environment and do not infer GPU/custom-op readiness from an import alone.

## Route first

- Use [data-preparation](../data-preparation/SKILL.md) for acquisition, conversion, and full HDF5/file-list validation.
- Use [evaluation-and-artifacts](../evaluation-and-artifacts/SKILL.md) for prediction/metric workflows and artifact interpretation.
- Use [core-xconv-and-operators](../core-xconv-and-operators/SKILL.md) for model internals, augmentation operators, and native operator diagnostics.
- For cross-cutting compatibility failures, use [troubleshooting](../../references/troubleshooting.md).

## Safe preflight

From the PointCNN project root (or an equivalent checkout containing the trainer and its Python modules), first validate inputs without creating checkpoints:

```bash
python3 skills/disco/point-cnn/sub-skills/classification-workflows/scripts/validate_classification_inputs.py --help
python3 skills/disco/point-cnn/sub-skills/classification-workflows/scripts/validate_classification_inputs.py \
  --train-files /path/to/train_files.txt --val-files /path/to/test_files.txt \
  --model pointcnn_cls --setting modelnet_x3_l4
```

The validator checks file-list existence, relative HDF5 resolution, `data`/`label` presence and compatible leading dimensions, rank/feature width, integer labels, and the expected class-count range. It is deliberately read-only. Quick Draw is special: its setting loads an NPZ directory and performs stroke-to-point mapping through `map_fn`; validate that directory and `categories.txt` separately before running.

## Select a workflow and configuration

Use the common trainer directly; do not copy the historical backgrounding launchers. The required flags are:

```text
train_val_cls.py -t/--path TRAIN -v/--path_val VAL -s/--save_folder OUT \
                 -m/--model MODEL -x/--setting SETTING
```

Optional flags are `-l/--load_ckpt CHECKPOINT`, `--epochs N`, `--batch_size N`, `--log FILE` (use `-` for stdout), `--no_timestamp_folder`, and `--no_code_backup`. `--path_val` is required in practice for every standard HDF5 setting; Quick Draw's loader ignores its second argument and uses the NPZ directory passed to `--path`.

The model is dynamically imported from `-m` (normally `pointcnn_cls`) and the setting is imported from that model's directory using `-x`. Verify both names before a long run:

```bash
python3 train_val_cls.py --help
python3 -m py_compile train_val_cls.py pointcnn_cls.py pointcnn_cls/modelnet_x3_l4.py
```

Run a bounded smoke with a tiny fixture, not a benchmark:

```bash
python3 train_val_cls.py -t /tmp/pcnn/train_files.txt -v /tmp/pcnn/val_files.txt \
  -s /tmp/pcnn-smoke -m pointcnn_cls -x modelnet_x3_l4 \
  --epochs 1 --batch_size 2 --no_timestamp_folder --no_code_backup --log -
```

TensorFlow graph construction or execution may still require the legacy dependency stack and can be slow. Stop after a bounded smoke; do not claim accuracy from it.

## Dataset routes

| Dataset | Setting | Input contract / notes |
|---|---|---|
| ModelNet40 | `modelnet_x3_l4` (also aligned, feature, no-X, wider, yxz, or 5-layer variants) | Train and test file lists of HDF5 files; 40 classes, normally XYZ plus optional normals. |
| ScanNet objects | `scannet_x2_l4` | Prepared train/test HDF5 lists; 17 classes in the checked-in setting; XYZ plus RGB features are expected by the conversion. |
| TU-Berlin | `tu_berlin_x3_l4` | Prepared fold HDF5 lists; 250 classes, 512 points, XYZ plus normals. |
| Quick Draw | `quick_draw_full_x2_l6` | `--path` is the NPZ directory containing `categories.txt` and category NPZ files; `--path_val` is ignored by this loader; 345 classes and on-the-fly stroke mapping; high RAM usage. |
| MNIST | `mnist_x2_l4` | HDF5 train/test lists produced by conversion; 10 classes, 4 channels (XYZ + scalar pixel feature), 160 sampled points in setting. |
| CIFAR-10 | `cifar10_x3_l4` | HDF5 train/test lists produced by conversion; 10 classes, 6 channels (XYZ + RGB), 512 sampled points in setting. |

Dataset download and conversion are intentionally not run by this skill. Follow the data-preparation route and confirm that every file-list line resolves relative to its file-list directory. Do not use segmentation HDF5 lists here.

## Input and setting contract

`data_utils.load_cls` opens each listed HDF5 and concatenates `data` and `label`. If a `normal` dataset exists, it concatenates it to `data` along the final axis; otherwise only `data` is used. Every file must therefore have consistent sample count, point count, and feature width. Labels are squeezed to one integer per sample. Expected `data` is rank 3 `(samples, points, channels)` and labels are `(samples,)` after squeeze. Labels must be in `[0, num_class)`.

Settings expose `load_fn`, `balance_fn`, `map_fn`, `keep_remainder`, `num_class`, `sample_num`, batch/training schedule, augmentation ranges, pooling/X-Conv parameters, optimizer, `data_dim`, `use_extra_features`, and related flags. The trainer splits the first three channels as XYZ and treats remaining channels as features only when configured. A frequent hard failure is normals/RGB present in HDF5 while `data_dim` or `use_extra_features` does not match the selected setting; choose a matching configuration rather than silently dropping channels.

`keep_remainder=True` is used by the checked-in classification settings. The final batch can be smaller than `batch_size`; the trainer computes a matching transform/index batch. If adapting a setting with `keep_remainder=False`, incomplete batches are dropped and an undersized fixture may produce zero training batches.

## Augmentation and pooling behavior

Training samples use `pointfly.get_indices` with the setting's sample count and optional `pool_setting_train`, plus random rotation/scaling and jitter. Validation uses the validation ranges and `pool_setting_val`. Normals are rotated when `with_normal_feature=True`; non-normal extra features are passed through. `pointcnn_cls.Net` pools the final fully-connected point features during evaluation before producing `num_class` logits. Model variants differ in X-transformation, sorting, feature usage, X-Conv depth/width, and normal handling; preserve the setting/model pair.

## Outputs, resume, and side effects

With timestamping enabled (default), output is a new directory named from model, setting, timestamp, and process id beneath `--save_folder`. With `--no_timestamp_folder`, output is written directly to the supplied folder. The trainer writes `log.txt` (unless overridden), `ckpts/iter-<global_step>` checkpoint files, and `summary/` TensorBoard event files. Unless `--no_code_backup` is given, it copies the trainer's code directory into the run directory. These are intentional write side effects; use a disposable output directory for smoke tests.

At startup, `--load_ckpt` restores the exact graph-compatible checkpoint. Without it, the trainer attempts the latest checkpoint in the run's `ckpts/` directory. A checkpoint with a different class count, feature width, model variant, or variable names will fail restore; create a fresh output directory or select the matching setting. Never overwrite a valuable run while testing.

## Verification boundary

Native candidates are `train_val_cls.py --help`, setting import/`py_compile`, and a tiny HDF5 contract fixture. Full training, dataset conversion, and benchmark claims are excluded. TensorFlow 1.15 and the legacy `tf.contrib`/`tf.layers` APIs were observed during inspection, but the available GPU smoke and custom operator smoke did not complete; required backend execution remains blocked/partial. Classification does not require the segmentation FPS custom op, but it still requires a functioning TensorFlow 1.x graph-mode stack.

See [configurations](references/configurations.md), [CLI and run layout](references/cli-and-run-layout.md), and [classification troubleshooting](references/troubleshooting.md) for the detailed matrix and recovery steps.
