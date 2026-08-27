# Troubleshooting

## `mxnet` or `mxnext` import fails

Symptoms:

- `ModuleNotFoundError: mxnet`
- `ModuleNotFoundError: mxnext`
- config import fails before `get_config(...)` returns

Likely causes:

- The repo root is not on `PYTHONPATH`.
- The external `mxnext` dependency is missing.
- The environment does not have a compatible MXNet wheel.

Fix:

- Run the launcher from the repo root.
- Verify the repo checkout is importable as a module tree.
- Install the required MXNet / mxnext stack before trying a GPU run.

## `mx.gpu(...)` or CUDA context errors

Symptoms:

- `mx.gpu` cannot create a context.
- GPU count is zero.
- Training, test, or speed inference exits immediately on context creation.

Likely causes:

- No CUDA backend is installed.
- The MXNet wheel does not match the driver / CUDA stack.
- The current host does not expose a usable GPU backend.

Fix:

- Use a CUDA-capable environment that matches the repository's legacy MXNet expectation.
- Keep `KvstoreParam.gpus` aligned with visible device IDs.
- For pure inspection, use `scripts/inspect_config.py` instead of launching training.

Note:

- The private verification report for this production batch did **not** obtain a working CUDA backend, so no native GPU run should be claimed as validated from this skill tree alone.

## Shape inference or static-shape mismatch

Symptoms:

- Symbol shape inference fails.
- A config that worked for one dataset fails on another with shape or padding errors.
- Speed benchmarking crashes when `--shape` does not match the config.

Likely causes:

- `ResizeParam` and `PadParam` disagree with each other.
- `max_num_gt` or `max_len_gt_poly` is too small for the dataset.
- The model expects a different number of pyramid levels, classes, or RoI sizes.

Fix:

- Re-check `ResizeParam.short/long`, `PadParam.short/long`, and the anchor shape helpers.
- Re-run `scripts/inspect_config.py --train` and `--test` to compare the returned namespaces.
- For speed tests, pass the exact static input shape expected by the config.

## Checkpoint not found or wrong epoch

Symptoms:

- Missing `checkpoint-000X.params`
- Test runs evaluate the wrong weights
- Resume training loads the wrong checkpoint

Likely causes:

- `pTest.model.prefix` points to the wrong experiment.
- `pTest.model.epoch` does not match the saved checkpoint number.
- Training resume was attempted without updating `OptimizeParam.schedule.begin_epoch`.

Fix:

- Check `experiments/<name>/` for the saved `checkpoint-000X.params` files.
- Use `--epoch N` for `detection_test.py` when you want a different evaluation epoch.
- Edit the config schedule when resuming training; there is no separate resume CLI flag.

## COCO API or annotation issues

Symptoms:

- `pycocotools` import fails.
- `COCOeval` cannot load annotations.
- `mask_test.py` fails before evaluation.

Likely causes:

- `pycocotools` is not installed.
- `TestParam.coco.annotation` is missing or points at the wrong annotation file.
- The roidb split name does not match the expected result file path.

Fix:

- Install the COCO Python API used by the repository.
- Verify `data/cache/<split>.roidb` and `TestParam.coco.annotation` refer to the same dataset split.
- For test configs that set `annotation = None`, rely on the roidb-to-COCO fallback only when the roidb is valid.

## NMS or post-processing problems

Symptoms:

- Empty results after evaluation.
- Segmentation results are malformed.
- `set_nms` or `softnms` paths fail.

Likely causes:

- `TestParam.nms.type` does not match the configured post-processing code path.
- The class-aware / class-agnostic box layout was misread.
- Mask configs require a valid `mask_score` / `segm` branch.

Fix:

- Confirm whether the config produces `[n, 4]` or `[n, 4 * num_class]` boxes.
- Keep `min_det_score` consistent with the detector family.
- For `set_nms`, make sure the proposal count fields it depends on are still present.

## Worker, thread, or memory pressure

Symptoms:

- Training stalls in the loader.
- CPU memory spikes.
- Evaluation takes too many worker threads.

Likely causes:

- `loader_worker` or `loader_collector` is too high for the host.
- `batch_image` is too large for the GPU or the host memory.
- Many-GPU evaluation creates one executor per visible GPU.

Fix:

- Reduce `General.loader_worker` first.
- Then reduce `batch_image` or the number of visible GPUs.
- On very small hosts, keep test-time loader counts conservative.

## FP16 or distributed instability

Symptoms:

- FP16 runs diverge or overflow.
- Distributed training hangs or syncs incorrectly.
- A multi-GPU job behaves differently from a single-GPU job.

Likely causes:

- The config toggled FP16 without a compatible model family.
- `KvstoreParam.gpus` or `kvstore` does not match the intended topology.
- The environment cannot support the required NCCL / CUDA combination.

Fix:

- Start from a known FP16-ready config instead of turning it on blindly.
- Keep `batch_image` as a per-GPU value.
- For a single-GPU debug run, switch the config to one visible GPU and use `kvstore = "local"`.

## Config import confusion

Symptoms:

- `importlib.import_module` cannot find the config.
- The script works from one directory but not another.

Likely causes:

- The config argument still looks like a file path instead of a module path.
- The repo root is not importable.

Fix:

- Use the `config/...py` form that the launchers expect.
- Let `scripts/inspect_config.py` print the resolved module name before you launch a long job.
