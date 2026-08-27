# Data Preparation Troubleshooting

Use this when URL download, list validation, image decoding, or TFRecord writing
fails.

| Symptom | Likely cause | Recovery |
|---|---|---|
| `invalid label token` or `class id out of range` from the validator | Label tokens are not `id` or `id:confidence`, or `--num-classes` does not match the dataset | Re-check whether the file is ML-Images (`11166` classes) or ImageNet (`1000` classes); fix the row or class-count flag before conversion |
| Many URL downloads fail | Historical Flickr/OpenImages URLs may have expired, the host blocks requests, or network is unavailable | Keep invalid URLs in `--invalid-url-file`; do not treat expiry as parser failure; retry only after network approval |
| Downloaded image list has duplicate filenames | Different URLs ended in the same last path components | Use the validator to detect duplicates; rename or shard outputs before TFRecord conversion |
| `missing image` during validation or conversion | The image list uses filenames relative to a different `images` root | Pass the correct `--images-root`/`--images-dir`, or regenerate the image list from the downloader output |
| Converter refuses to overwrite a shard | Existing `.tfrecords` file is present | Choose a fresh output directory for smoke tests, or pass `--overwrite` only when replacing old output is intentional |
| TensorFlow import or TFRecord APIs are missing | The runtime is TensorFlow 2-only or not installed | Use a TensorFlow 1.x-compatible environment; if using TF2, verify that `tf.compat.v1` TFRecord writer and image decode paths work with the bundled script |
| Image decode returns zero height/width or fails | File is corrupt, not JPEG/PNG, or has an unsupported encoding | Remove the row, replace the image, or convert it to RGB JPEG before running TFRecord conversion |
| Training later reports no files found | The converter wrote shards somewhere other than the split directory the training command reads | Put shards under `<data-root>/train` and `<data-root>/val`, or set the training `--data_dir` to the parent containing those split directories |
| Finetuning labels are wrong shape | ImageNet finetuning expects scalar integer labels, while ML-Images pretraining expects dense multi-label bytes | Use `--one-hot false` for scalar class ids and `--one-hot true` for ML-Images multi-label vectors |

## Legacy downloader notes

The original downloader was written for Python 2 (`urllib.urlretrieve` and old
thread APIs). Prefer the bundled `scripts/download_urls.py` helper for Python 3
workflows. It preserves the row convention but adds `--dry-run`, `--limit`,
explicit output paths, and safer errors.

## Validation before expensive work

Before starting any full data run, require these checks:

1. A small sample passes `scripts/validate_ml_images_lists.py`.
2. A tiny TFRecord conversion writes into a temporary output directory.
3. The train/val split directory structure is explicit.
4. The intended class count matches the model/checkpoint workflow that will
   consume the data.
