# Training and evaluation troubleshooting

Use this guide after command construction but before or after a deliberate train/test/reval/convert run. For environment build failures or data-layout errors, route to sibling sub-skills rather than duplicating their instructions.

## Quick triage

| Symptom | Most likely area | First response |
| --- | --- | --- |
| `No such file or directory: data/imagenet_weights/<net>.ckpt` | Missing initialization weights | Route to dataset/assets to place the ImageNet initialization checkpoint or choose the correct `--weight`. |
| `NotFoundError` or TensorFlow restore error for `output/.../<net>_faster_rcnn_iter_<iters>.ckpt` | Missing/stale trained snapshot | Dry-run the expected path, check `--tag`/extra args, verify `.index`/`.meta`/`.data-*` siblings, or pass `--model` explicitly. |
| Training resumes when a fresh run was expected | Existing snapshot directory | Move old output aside or use a new tag; do not delete only one file from a checkpoint set. |
| Assertion in snapshot discovery | Mismatched `.ckpt.meta` and `.pkl` files | Restore a consistent output directory from backup or isolate a new tag. |
| NaNs during training | Learning rate/data/normalization/backend instability | Confirm config overrides, dataset annotations, initialization weights, and NMS/build health; restart from clean tag after correcting. |
| AP far below README numbers | NMS mode/build, dataset split, checkpoint mismatch, stochasticity | Confirm `TEST.MODE`, compiled NMS, dataset alias, anchor scales/ratios, checkpoint source, and expected benchmark schedule. |
| `Unknown dataset` | Wrong imdb key or missing dataset registry dependency | Use mapped aliases or route to dataset/assets for registry/layout guidance. |
| `KeyError` or type assertion in config override | Bad `--set` key/value | Use dot notation for existing keys and quote list/tuple/string values correctly. |
| Full run impossible on current host | Expensive backend/data block | Keep to dry-run/source-level guidance or obtain explicit user approval plus required assets/backend. |

## Missing ImageNet initialization weights for training

Training commands load `data/imagenet_weights/<net>.ckpt` through `--weight`. If the file is absent or named differently:

1. Confirm the selected net: `vgg16`, `res50`, `res101`, `res152`, or `mobile`.
2. Confirm the expected checkpoint prefix in the command-builder output.
3. Route to [dataset-and-assets](../../dataset-and-assets/SKILL.md) to place or symlink the correct Slim/ImageNet checkpoint.
4. If using a custom initialization file, build a direct command with an explicit `--weight` by editing the printed dry-run command; record that it no longer exactly follows the shell launcher.

Do not silently substitute a trained Faster R-CNN checkpoint as an ImageNet initialization checkpoint.

## Missing trained checkpoint for testing

The test launcher predicts the model path from dataset alias, net, tag, and mapped iterations:

```text
output/<net>/<train_imdb>/<tag>/<net>_faster_rcnn_iter_<iters>.ckpt
```

TensorFlow restore normally needs the checkpoint prefix plus sibling files such as `.index`, `.meta`, and `.data-00000-of-00001` depending on TensorFlow version.

If testing fails to find the model:

1. Dry-run the command with the same `--dataset`, `--net`, `--iters`, and `--set` pairs.
2. Check whether extra config tokens created a tag slug; source launchers put extra runs under that slug instead of `default`.
3. Check whether training was stopped before the final iteration. Use the latest complete snapshot prefix explicitly with `--model`.
4. Check whether the config's `EXP_DIR` differs from the net name; custom configs can change output paths.
5. If using pretrained model-zoo outputs, route to dataset/assets for the expected symlink/output layout.

## Stale snapshots and resume surprises

Training auto-resumes if snapshots exist in the output directory. `find_previous()` sorts matching snapshots by modification time, ignores snapshots taken at `stepsize + 1`, and requires `.ckpt.meta` and `.pkl` counts to match.

Safe recovery patterns:

- For a clean run, move the whole old directory aside:
  `output/<net>/<train_imdb>/<tag>/`.
- For a comparison run, use new config tokens or an explicit `--tag` so output/TensorBoard directories are isolated.
- For a real resume, keep checkpoint files and the `.pkl` metadata together. The `.pkl` restores NumPy/data-layer state and last iteration.
- Do not mix snapshots from different datasets, net configs, or tags in one directory.

Remember that TensorFlow random state is not fully restored, so resumed results can diverge even when metadata is valid.

## NaNs during training

The README points users to historical NaN discussion, and the repo's design has several practical risk factors: TensorFlow 1.x GPU nondeterminism, small batch size, dataset annotation issues, stale snapshots, and config overrides.

Triage checklist:

1. Verify the dry-run command did not accidentally change `TRAIN.STEPSIZE`, `TRAIN.LEARNING_RATE`, `TRAIN.GAMMA`, `ANCHOR_SCALES`, or `ANCHOR_RATIOS` to incompatible types/values.
2. Confirm the correct ImageNet initialization checkpoint for the selected net; wrong checkpoint scopes can leave variables poorly initialized or fail restore.
3. Confirm dataset annotations and roidb filtering are sane through dataset/assets guidance; empty/invalid boxes can reduce usable minibatches.
4. Confirm NMS/native extensions and TensorFlow backend are compatible through installation guidance.
5. Start from a clean tag after corrections so a corrupted or unstable snapshot is not restored.
6. If using a long COCO or custom schedule, reduce scope for diagnosis before attempting a full benchmark run.

Do not claim a universal fix; record the changed variable and rerun plan.

## Config override failures

Common invalid overrides:

- `--set TRAIN.STEPSIZE 80000` fails because the config expects a list, not an integer. Use `--set TRAIN.STEPSIZE '[80000]'`.
- `--set ANCHOR_SCALES 8,16,32` fails or parses unexpectedly. Use `--set ANCHOR_SCALES '[8,16,32]'`.
- `--set TEST.MODE nms` is valid because a bare string falls back to the raw string when `literal_eval` fails.
- Unknown keys fail by assertion or `KeyError`; check key spelling and nesting.
- Type mismatches are intentional; the repo does not coerce integers to floats or strings to booleans except through Python literal parsing.

When extra overrides are passed through the original shell launcher, they also affect the tag slug. A forgotten extra pair can make outputs appear missing from `default`.

## AP mismatch or benchmark caveats

Reported AP values are not strict regression-test targets. The README notes:

- VOC results can vary because TensorFlow GPU training is nondeterministic; best numbers from 2-3 attempts were reported.
- COCO results are usually closer but still schedule/backend dependent.
- `TEST.MODE nms` is default; `TEST.MODE top` may be slightly better and slower.
- NMS correctness materially affects AP. A bad GPU NMS build can produce suspicious results.
- The implementation keeps small proposals and uses no final score threshold, which affects comparability with other Faster R-CNN variants.
- COCO README benchmark numbers mention longer 900k/1190k schedules, while the shell launcher maps `coco` to 490k.

When debugging AP:

1. Verify dataset split exactly (`pascal_voc` vs `pascal_voc_0712` vs `coco`).
2. Verify the checkpoint was trained for the matching dataset/schedule.
3. Verify anchors/ratios are the mapped values unless intentionally changed.
4. Verify `cfg.TEST.MODE`, `cfg.TEST.NMS`, `--num_dets`, and `--comp`.
5. Verify CPU/GPU NMS implementation and `USE_GPU_NMS` routing.
6. Report AP as a reproduction attempt with the full command and environment, not as proof of repository correctness.

## Reval failures

`tools/reval.py` expects an output directory containing `detections.pkl` and uses the selected imdb's evaluator.

If it fails:

- Check that `detections.pkl` exists in the output directory from `tools/test_net.py`.
- Check that the reval `--imdb` matches the dataset used to produce detections.
- Use `--nms` only when saved detections need NMS applied before evaluation; do not double-apply NMS without reason.
- `--matlab` needs a working MATLAB VOC-evaluation path and is not a generic fix for Python evaluator failures.
- COCO reval requires COCO annotation layout and pycocotools availability.

## Deprecated VGG16 conversion failures

The converter is narrow:

- Only VGG16 snapshots are supported.
- It derives the input directory by replacing `/vgg16/` with `/vgg16_depre/` in the output directory.
- It expects old checkpoint variables with VGG scope names that can be rewritten to the newer names.
- It copies the `.pkl` metadata file after saving the converted TensorFlow checkpoint.

If conversion fails, verify old snapshot prefix, old output location, `.pkl` presence, TensorFlow checkpoint readability, and dataset/tag-derived output directory. Do not use this path for ResNet/MobileNet or non-repository checkpoint formats.

## Expensive-run recovery policy

Full train/test commands are not smoke tests. If a run is missing data, weights, CUDA/NMS build, or a compatible TF1 runtime:

1. Stop and report the precise missing prerequisite.
2. Keep any partial outputs intact unless the user authorizes cleanup.
3. Use dry-run commands and source-level checks to continue planning without pretending verification passed.
4. Ask for explicit approval before launching long GPU training, dataset-wide evaluation, downloads, or benchmark reproduction.
