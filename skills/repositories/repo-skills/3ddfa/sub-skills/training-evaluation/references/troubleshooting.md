# Troubleshooting

## CUDA or device errors

**Symptom:** `torch.cuda` errors, invalid device ordinals, or a model that fails before the first batch.

**Cause:** `train.py` is CUDA-centric. It sets the primary GPU explicitly and wraps the model in `DataParallel(...).cuda()`.

**Fix:**

- Make sure the requested `--devices-id` values exist and are visible to CUDA.
- When adapting a recipe to one GPU, use a single device id and reduce batch size.
- Do not expect the stock training path to run on CPU without code changes.

## Resume does not continue the optimizer

**Symptom:** `--resume` loads weights, but the learning-rate schedule or momentum state feels like a fresh run.

**Cause:** The bundled checkpoints save only the model `state_dict` and the epoch number.

**Fix:**

- Treat resume as a warm start, not a full-state restore.
- Set `--start-epoch` manually.
- If you need true optimizer resume, patch the save/load logic.

## Filelist or parameter mismatch

**Symptom:** indexing failures, wrong samples, or validation data that silently looks inconsistent.

**Cause:** `DDFADataset` indexes the param file by the filelist order. There is no automatic alignment check.

**Fix:**

- Make sure each filelist has the same number of entries as the matching param file.
- Make sure the sample order is identical.
- Run `scripts/validate_training_args.py` before launching training.

## `--resample-num` seems ignored

**Symptom:** changing `--resample-num` in the shell recipe has no visible effect.

**Cause:** the current `train.py` does not forward that value into the loss constructors.

**Fix:**

- Use the shipped defaults if you just want the canonical recipes.
- Patch `train.py` and the loss constructors if you need a different resample count.

## PDC recipe confusion

**Symptom:** the PDC shell recipe does not look like a plain parameter MSE run.

**Cause:** the shipped `training/train_pdc.sh` currently passes `--loss=vdc`.

**Fix:**

- If you want a plain PDC baseline, switch the flag to `--loss=pdc`.
- Keep the rest of the template aligned with the same data layout and GPU plan.

## Benchmark data missing

**Symptom:** `benchmark.py` cannot find `test.data/...` or the cropped test lists.

**Cause:** the cropped benchmark package has not been unpacked into `test.data/`.

**Fix:**

- Unpack the cropped AFLW / AFLW2000 data into `test.data/`.
- If you already have prediction params, use the param-only helper path instead of the full image pipeline.

## Metric interpretation looks odd

**Symptom:** the reported mean does not match an external script or paper table.

**Cause:** the AFLW helper prints the average of the three yaw-bin means, not a sample-weighted mean over the whole set.

**Fix:**

- Report the same metric definition as the code used.
- For AFLW2000, always state whether you used the original or reannotated ground truth.
