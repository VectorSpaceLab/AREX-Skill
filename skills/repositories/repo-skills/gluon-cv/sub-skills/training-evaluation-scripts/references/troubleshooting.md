# Troubleshooting

Use the shortest fix that matches the symptom, then route to the owning sub-skill if the issue is really about models or data rather than command construction.

## Dataset root or annotation errors

**Symptoms**
- `FileNotFoundError` for `--dataset-root`, `--data-dir`, or `--download-dir`.
- Missing VOC/COCO/ImageNet/COCO-keypoint annotations.
- Empty class lists or no samples found.

**Fix**
- Check the family-specific root flag in `references/training-and-evaluation-scripts.md`.
- Validate the root layout before launching a long run.
- If the issue is really about dataset structure or record format, route to `../data-transforms-datasets/`.

## GPU selector parsing

**Symptoms**
- `--gpus` rejected where a family expects `--num-gpus`, `--ngpus`, `--gpu-id`, or `--gpu_ids`.
- Commands work for one family but fail for another after a flag rename.

**Fix**
- Rebuild the command with the family-specific flag spelling.
- Remember that `--gpus` is often a string list, while `--num-gpus` and `--ngpus` are integers.
- For single-GPU demo/eval scripts, check whether the family wants a string GPU list, an integer GPU count, or a single GPU id.

## Out-of-memory or batch-size pressure

**Symptoms**
- CUDA OOM, shared memory exhaustion, or dataloader stalls.
- Training crashes only after the first forward pass.

**Fix**
- Reduce `--batch-size` first.
- Then reduce workers, crop size, or data shape if the family exposes those knobs.
- Disable `--amp`, `--dali`, or distributed helpers until the baseline command is stable.

## Missing optional packages

**Symptoms**
- Import or runtime errors mentioning `DALI`, `Horovod`, `decord`, `pycocotools`, `timm`, `yacs`, or OpenCV.

**Fix**
- Install only the optional dependency that the selected family actually needs.
- If the command template is for a family that never uses the optional package, remove the optional flag instead of adding more dependencies.
- For Torch action-recognition, missing `decord` or `yacs` usually means the config-file path needs the Torch extras.

## Pretrained weights, cache, or network access

**Symptoms**
- Weight download failures.
- Cache misses for pretrained checkpoints.
- `--pretrained True` works only when the network is available.

**Fix**
- Use a local checkpoint or disable pretrained loading if the family permits it.
- Do not assume the internet is available in a research or CI run.
- If the task is really about model names or weight loading behavior, route to `../mxnet-model-zoo/` or `../torch-video-workflows/`.

## Resume or checkpoint mismatch

**Symptoms**
- Shape mismatch after `--resume`, `--resume-from`, `--resume-params`, or `--params-file`.
- Checkpoints created by one script family do not load in another family.

**Fix**
- Resume only with the same family and compatible model definition.
- For classification or pose scripts, verify whether the family wants a params file, a checkpoint prefix, or separate params/states files.
- For detection class changes, prefer a fresh fine-tune path rather than forcing a mismatched checkpoint.

## Mixed MXNet and Torch environments

**Symptoms**
- GluonCV imports with both backends present but the runtime feels heavier than expected.
- A Torch workflow is being launched in an MXNet-only environment, or vice versa.

**Fix**
- Keep the family aligned with the installed backend.
- Use the runtime warning about both frameworks as a reminder to avoid unnecessary GPU contention.
- If a backend is missing, route to the backend-owning sub-skill instead of guessing a cross-backend workaround.

## Long benchmark or training runs

**Symptoms**
- Benchmark scripts appear to hang or run far longer than expected.
- A helper command is mistaken for a runnable training job.

**Fix**
- Use the bundled helper to print a template first.
- Keep `--benchmark` and `--num-iterations` for bounded smoke checks, not for open-ended validation.
- Do not run the original long script zoo unless the task truly needs that workload.

## Pillow or legacy image support in Torch workflows

**Symptoms**
- Torch-side transforms fail around `PIL.Image.LINEAR` or similar image constants.

**Fix**
- Use a Pillow version compatible with the installed GluonCV Torch code.
- Revisit the Torch-specific sub-skill if the issue is really a video-transform dependency problem.
