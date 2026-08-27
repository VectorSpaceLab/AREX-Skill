# Troubleshooting

## Installation and import

- If `fastdup` fails to import, confirm that the environment has the compiled dependencies the wheel needs: `numpy`, `pandas`, `scikit-learn`, `opencv-python-headless` or `opencv-python`, `Pillow`, `requests`, `sentry-sdk`, `pyOpenSSL`, and `pillow-heif`.
- On Linux, `libGL.so.1` errors usually mean the system OpenGL library is missing. Install the headless OpenCV stack or the OS package that provides `libGL`.
- For video workflows, install `ffmpeg`.
- On macOS, prefer the platform-appropriate Python and OpenCV/OpenMP combination described in the repo docs.

## Dataset and path issues

- Missing-file errors almost always mean the `filename` column does not match the actual input path layout.
- When in doubt, make annotation filenames absolute.
- If a run reports no results, lower the similarity threshold or use a larger/tinier-cleaner fixture.
- If the output is empty because images are too small or corrupted, check the input file list and the supported image formats.

## Binary feature issues

- `load_binary_feature` reshape errors mean the `d` argument does not match the saved vector width.
- Save and load with the same `d` that produced the file.

## Gallery issues

- `No connected components found` is usually a data-threshold issue rather than a crash.
- Large galleries can be slow or memory-heavy; reduce `num_images` or use `lazy_load=True`.
- `SettingWithCopyWarning` messages from pandas are noisy but are not usually fatal for the gallery helpers.

## Model-enrichment issues

- Missing `torch`, `timm`, `transformers`, `paddlepaddle`, `paddleocr`, `groundingdino`, or `segment_anything` means the matching optional workflow is unavailable.
- Many enrichment workflows download weights the first time they run.
- If the model width does not match the feature width, search and embedding steps will fail.

## Known runtime bug

- The `fastdup.datasets.FastdupHFDataset` helper currently raises a circular import in the inspected release line. Use manual annotation DataFrames instead of relying on that helper until it is refreshed.

## Cloud, archive, and video issues

- If `s3://` or `minio://` input paths fail, check the cloud sync tool and credentials or endpoint settings outside the skill tree.
- Archive workflows need the archive to be readable locally or via the configured cloud tool.
- Video workflows depend on codecs and ffmpeg availability.
