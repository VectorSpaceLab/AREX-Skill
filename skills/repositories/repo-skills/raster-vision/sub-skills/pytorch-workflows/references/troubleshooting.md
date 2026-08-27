# Troubleshooting

## Inspect first

Before changing config, check these outputs:

- `train/dataloaders/*.png`
- `train/log.csv`
- `train/valid_preds.png`
- `eval/validation_scenes/eval.json`
- `bundle/model-bundle.zip`
- `predict/<scene>/labels.tif`

## Common failure modes

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Example key is not recognized | The key is not in the bundled example catalog | Use the catalog or the command printer `--help` output. |
| Training expects chips but none exist | `ImageDataConfig` was chosen even though the workflow is scene-based | Switch to `GeoDataConfig` with `nochip=True`. |
| CHIP or ANALYZE outputs are missing on purpose | `nochip=True` skips those commands | Do not look for chipped data; inspect the direct-scene training outputs instead. |
| Predictions look blank or colors are wrong | Channel order, display groups, or image-channel count do not match the source | Recheck `channel_order`, `img_channels`, and `plot_options.channel_display_groups`. |
| Remote rasters fail to read in streaming mode | The URI is not readable by the configured raster source | Disable streaming or move the asset to a readable local/S3 location. |
| `external_model` import or build fails | The external repo, entrypoint, or version is incompatible | Pin the external module to the tested version and confirm the entrypoint name. |
| `external_loss_def` validation fails | The solver also sets a conflicting loss option | Remove `class_loss_weights` or `ignore_class_index` when using an external loss. |
| Fine-tuned bundle loads but predictions are wrong | The checkpoint head, class count, or band count no longer matches | Align `num_classes`, `img_channels`, `channel_order`, and `load_strict`. |
| A tiny learner test unexpectedly starts DDP on every visible GPU or fails with CUDA OOM | Raster Vision detects multiple CUDA devices and uses distributed training, while some devices are busy or memory-fragmented | For a smoke test, set `CUDA_VISIBLE_DEVICES=""` to force the documented CPU substitute, or restrict to one free GPU before rerunning; do not treat a busy-GPU OOM as proof that the config is wrong. |
| TensorBoard never appears | Logging or port forwarding was not enabled | Set `log_tensorboard=True`, `run_tensorboard=True`, and expose port 6006. |
| `xview-od` cannot find labels | The notebook-generated processed labels are missing or the `processed_uri` points at the wrong directory | Rebuild the processed data and point the example at the generated output. |
| `prediction/` exists but no polygons are written | The label store was not configured to emit vectors | Add the appropriate `LabelStoreConfig` vector output for that task. |

## Recovery pattern

1. Verify the selected example key and the runner mode.
2. Confirm the workflow is using the right data mode: scene-based versus chip-based.
3. Check the training logs and dataloader previews before changing model code.
4. If a pretrained bundle is involved, confirm that `init_weights`, class count, and channel order match the new task.
5. If the failure is still unclear, hand the issue to the `pipeline-cli`, `data-and-models`, or `cloud-and-filesystems` sub-skill as appropriate.
