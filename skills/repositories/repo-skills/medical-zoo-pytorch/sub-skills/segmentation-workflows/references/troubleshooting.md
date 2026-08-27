# Troubleshooting

| Symptom | Likely cause | What to do |
| --- | --- | --- |
| `ImportError` while importing `lib.medzoo` | Optional extras such as `torchsummary`, `torchsummaryX`, or `torchvision` are missing. | Install the missing package in the active environment before importing the model zoo. |
| `AssertionError` from `create_model` | `args.model` is not one of the uppercase factory ids. | Use the exact factory name from the model overview. |
| Shape or channel mismatch in `VNET` / `VNET2` | The input channel count does not divide the 16-channel input transition cleanly. | Use a channel count that the input transition can repeat to 16 without remainder, such as 1, 2, or 4. |
| `NotImplementedError` or missing branch in `HYPERDENSENET` | The wrong channel count was selected for the hyper-dense branch. | Use 2 channels for the 2-modality class and 3 channels for the 3-modality class. |
| `DualPathDenseNet` or `DualSingleDenseNet` fails during forward | The source implementation contains dense-feature channel math that can mismatch the classifier layer, especially on `DENSENET2`. | Prefer `DENSENET3` for a dense multi-stream smoke, or run `--include-known-broken` to surface the failure explicitly. |
| `restore_checkpoint` cannot load a checkpoint | The checkpoint path is wrong, the model structure changed, or the checkpoint came from another device layout. | Point to the file saved by `save_checkpoint` and keep the model definition aligned with the checkpoint. |
| Checkpoints are saved in an unexpected place | `save_checkpoint` expects a directory path and derives filenames from the directory basename. | Pass a dedicated checkpoint directory, not a file path. |
| Checkpoint cadence looks off in the bundled trainer | The current save condition in `Trainer` does not read as a plain every-N-epochs rule. | Verify the actual cadence on a short run before relying on it, or save manually. |
| TensorBoard files land in strange directories | `TensorboardWriter` concatenates `log_dir` strings directly. | Use a simple sandbox or a clean relative root when smoke testing. |
| Non-overlap inference fails on odd shapes | `find_crop_dims` only behaves cleanly when the crop tiles the volume; the fallback path is unreliable. | Pad or crop to compatible sizes before calling the helper. |
| Legacy inference crashes on CPU-only runs | The helper still calls `.cuda()` and also expects a checkpoint and full volume stack. | Treat the demo as reference-only unless you patch the helper locally. |
| Loss or writer code expects a tensor but gets a tuple | Some models return more than one tensor. | For `DenseVoxelNet` keep both segmentation outputs; for `ResNet3dVAE` unpack the segmentation output and the VAE tensors separately. |
| Logged per-class scores look inconsistent | Writer bookkeeping assumes the dataset label list and score vector have the same order and length. | Keep `classes` aligned with the chosen dataset label set. |

## Quick checks before debugging deeper

1. Confirm the model id and channel count.
2. Confirm the input tensor shape.
3. Confirm whether the model returns a tensor or a tuple.
4. Confirm that your checkpoint path points to the directory-derived filename you actually saved.
5. Confirm that the output directories are writable.
