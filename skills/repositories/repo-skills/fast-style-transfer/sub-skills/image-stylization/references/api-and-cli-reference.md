# Image Stylization API and CLI Reference

## Bundled image stylization runtime flags

| Flag | Required | Default | Meaning |
| --- | --- | --- | --- |
| `--checkpoint CHECKPOINT` | yes | none | Checkpoint directory or checkpoint path/prefix to restore. |
| `--in-path IN_PATH` | yes | none | Image file or directory of images. |
| `--out-path OUT_PATH` | yes | none | Output file or directory. |
| `--device DEVICE` | no | `/gpu:0` | TensorFlow device for computation. |
| `--batch-size BATCH_SIZE` | no | `4` | Batch size for directory feed-forwarding. |
| `--allow-different-dimensions` | no | false | Group directory images by shape instead of requiring one shared shape. |

`evaluate.check_opts` asserts that checkpoint and input paths exist. When `--out-path` already exists and is a directory, it also asserts the directory exists and validates batch size.

## Verified callable signatures

```python
evaluate.ffwd(data_in, paths_out, checkpoint_dir, device_t='/gpu:0', batch_size=4)
evaluate.ffwd_to_img(in_path, out_path, checkpoint_dir, device='/cpu:0')
evaluate.ffwd_different_dimensions(in_path, out_path, checkpoint_dir, device_t='/gpu:0', batch_size=4)
evaluate.ffwd_video(path_in, path_out, checkpoint_dir, device_t='/gpu:0', batch_size=4)
transform.net(image)
utils.get_img(src, img_size=False)
utils.save_img(out_path, img)
utils.scale_img(style_path, style_scale)
```

## API behavior notes

### `evaluate.ffwd`

- `data_in` may be a list of image paths or a numpy array-like batch.
- `paths_out` must contain output paths.
- If path-based input is used, every image in a batch must match the first image shape unless grouped through `ffwd_different_dimensions`.
- Batch size is capped at the number of output paths for each invocation.
- The function restores a TensorFlow checkpoint before running predictions.

### `evaluate.ffwd_to_img`

Convenience wrapper for a single image. It calls `ffwd` with batch size 1 and defaults to device `/cpu:0`.

### `evaluate.ffwd_different_dimensions`

Groups input/output pairs by image shape, then calls `ffwd` for each shape group.

### `transform.net`

Builds the feed-forward transform network. A safe graph-build check with a tiny static placeholder was verified during skill creation. Running it with restored weights still requires a compatible checkpoint.

### `utils.get_img` and `utils.save_img`

`get_img` loads RGB image data and expands grayscale inputs to three channels. `save_img` clips numeric arrays to `[0, 255]`, converts to `uint8`, and writes image files.

## Device strings

Use TensorFlow device syntax such as `/cpu:0` or `/gpu:0`. The CLI default is `/gpu:0`, but CPU is often the safest debug setting when GPU TensorFlow is not verified.
