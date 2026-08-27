# Training And Dataset Troubleshooting

Use this reference when ControlNet training fails before or during startup. Fix dataset and checkpoint issues before tuning trainer settings.

## Dataset And JSONL Failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `prompt.json` not found | Dataset root points at the wrong directory or Fill50K was not unpacked under the expected root. | Point the validator/training script at the directory containing `prompt.json`, `source/`, and `target/`; do not point at the parent `training/` directory unless the script appends `fill50k`. |
| JSON decode error on a line | `prompt.json` is malformed JSONL, has comments, trailing commas, or was saved as a JSON array. | Rewrite as one JSON object per line with double-quoted keys and strings. Validate again. |
| Missing key such as `source` or `target` | Row schema does not match the tutorial loader. | Add `source`, `target`, and `prompt`, or adapt the custom `Dataset` to translate local names into those fields. |
| Image file missing | Relative path in `prompt.json` is wrong or file was not copied. | Make paths relative to the dataset root and ensure files exist under `source/` and `target/`. |
| Image unreadable | File is corrupt, unsupported, empty, or not actually an image. | Replace the file or convert it to a standard PNG/JPEG readable by OpenCV/Pillow. |
| Source and target shape mismatch | Paired image preprocessing resized only one side. | Regenerate pairs with matching dimensions or add paired transforms before normalization. |

Run the validator with a small `--max-items` while iterating and with `--max-items 0` for a full scan before long training.

## Key, Range, And Color Bugs

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Training runs but colors look swapped | OpenCV BGR arrays were used as RGB. | Convert BGR to RGB before normalization, or use a loader that already returns RGB and document it. |
| Model receives values in `[0, 255]` | Normalization omitted. | Return `hint = source.astype(float32) / 255.0` and `jpg = target.astype(float32) / 127.5 - 1.0`. |
| Target appears washed out or clipped | Target normalized to `[0, 1]` instead of `[-1, 1]`. | Apply the target-specific `[-1, 1]` normalization. |
| Control map overwhelms or disappears | Source/hint range or channel order is wrong. | Check `hint.min()`, `hint.max()`, shape, and RGB order on sample rows. |
| Key error for `jpg`, `txt`, or `hint` | Custom dataset returns names that do not match the YAML config. | Either return `jpg`, `txt`, and `hint`, or intentionally update `first_stage_key`, `cond_stage_key`, and `control_key` in the config. |

## Checkpoint And Config Failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Missing `control_sd15_ini.ckpt` or `control_sd21_ini.ckpt` | The SD base checkpoint was not converted into a ControlNet-initialized checkpoint. | Route to [model-and-weight-utilities](../../model-and-weight-utilities/SKILL.md) to create the initial ControlNet checkpoint. |
| Many missing or unexpected state dict keys | Checkpoint and YAML config families do not match. | Use `cldm_v15.yaml` with SD1.5-derived init checkpoints and `cldm_v21.yaml` with SD2.1-derived init checkpoints. |
| Text encoder/context dimension mismatch | SD1.5/SD2.1 or CLIP/OpenCLIP mismatch. | Recheck the base model family and config; SD2.1 uses the SD2.1/OpenCLIP-style config. |
| Training starts from random-looking behavior | Wrong initialization or missing ControlNet-attached weights. | Recreate the initialized checkpoint from the intended base model before training. |

## CUDA, Memory, And Runtime Failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| CUDA OOM at startup | Batch too large, image size too high, extra SD layers unlocked, or GPU is too small. | Set `batch_size=1`, keep `sd_locked=True`, disable extra workers, and add `accumulate_grad_batches` for effective batch size. |
| OOM after a few logging steps | Image logging or validation samples consume memory. | Increase `logger_freq`, reduce logged sample count if customized, or temporarily remove image logging for a startup test. |
| 8GB GPU still fails in low-VRAM mode | Low-VRAM mode is experimental and not guaranteed on every card/driver. | Keep batch size at 1, use accumulation, reduce image sizes if your pipeline supports it, or move to a larger GPU. |
| Training is much slower with accumulation | Accumulation trades wall-clock speed for effective batch size. | Accept slower iterations or reduce accumulation once memory allows. |
| CPU-only run hangs or is impractically slow | Full ControlNet training is GPU-oriented. | Use CPU only for dataset validation and checkpoint inspection; run actual training on GPU. |

## PyTorch Lightning Drift

The tutorial uses older Lightning syntax:

```python
trainer = pl.Trainer(gpus=1, precision=32, callbacks=[logger])
```

In newer Lightning releases, `gpus=1` may be invalid. The equivalent intent is usually:

```python
trainer = pl.Trainer(accelerator="gpu", devices=1, precision=32, callbacks=[logger])
```

Keep the ControlNet model setup, dataset keys, and checkpoint/config pairing the same while updating trainer API syntax.

## External Download And Offline Issues

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| CLIP/OpenCLIP download attempted | Text encoder weights/tokenizer are not cached for the selected model family. | Pre-populate required model caches or run in an environment where allowed downloads are available. Do not treat dataset validation as requiring this. |
| Hugging Face dataset/model unavailable | Network access is blocked or artifacts were not mirrored. | Use already-downloaded local datasets/checkpoints or request the artifacts from the user. |
| Full tutorial import triggers downloads | Importing model/training code can initialize components that fetch weights. | Use the standalone validator for dataset checks and delay full imports until runtime artifacts are ready. |

## Debug Order

1. Validate `prompt.json` and image paths.
2. Inspect a few normalized samples for keys, shapes, ranges, and RGB order.
3. Confirm the initialized checkpoint exists and matches the YAML config family.
4. Run a very short trainer smoke test with `batch_size=1`.
5. Add logging, workers, larger batch size, accumulation, and low-VRAM tweaks one at a time.
