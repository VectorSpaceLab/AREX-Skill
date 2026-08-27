# Text Modeling Troubleshooting

Use this file for failures specific to the cropped prompt-text classifier. For captcha crop creation, OCR labeling, image-tile training, or end-to-end captcha inference, route to the sibling sub-skill that owns that workflow.

## Quick diagnostic command

Run the bundled checker before a long training or fine-tuning job:

```bash
python sub-skills/text-modeling/scripts/inspect_text_training_assets.py \
  --texts-npz texts.npz \
  --texts-v2-npz texts.v2.npz \
  --labels-file labels.txt \
  --model model.h5
```

Add `--load-model` only when the user explicitly wants a Keras load check. Without that flag the script checks model-file existence only.

## Compatibility and import failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Legacy Keras imports fail, especially `keras.preprocessing` symbols in sibling scripts | Keras 3 / newer TensorFlow stack | Use Python 3.11 with Keras/TensorFlow 2.15-compatible APIs for this repo family. Avoid mixing a Keras 3 image workflow with a Keras 2 text workflow in one run. |
| `ModuleNotFoundError: No module named 'keras'` or `tensorflow` | ML stack is not installed in the active environment | Install a TensorFlow/Keras 2.15-compatible CPU stack for inspection/training unless the user has a verified environment. |
| HDF5 model load warning or custom metric error | Fine-tuned artifact may contain legacy H5 metadata or custom `acc` metric | For inference-only validation, load with `compile=False`. For training continuation, provide the custom `acc` metric exactly as described in `api-reference.md`. |

## Dataset schema failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `.npz` file lacks `texts` or `labels` | Wrong file or incomplete dataset export | Regenerate or rename the dataset so the arrays are exactly `texts` and `labels`. |
| `texts.shape[0] != labels.shape[0]` | Labels are not aligned with text crops | Rebuild the dataset pairing; do not train until every row has one target. |
| `ValueError` while unpacking text dimensions | `texts` is not shaped exactly `(n, h, w)` for the legacy loader | Convert RGB/channel-first/4D data to grayscale `(n, h, w)` before using the legacy recipe. The inspector will warn on higher-dimensional arrays. |
| Very low accuracy from the first epoch and pixel max is `<= 1` | Text images were already normalized before `load_data` divided by 255 again | Store uint8-like pixel values in `[0, 255]`, or adapt the loader to skip the extra division. |
| Sparse label ids outside `0..79` | Vocabulary mismatch or corrupt labels | Align labels with the 80-row vocabulary and re-run the asset checker. |

## `texts.v2.npz` merge failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `np.concatenate` fails for labels in `load_data_v2()` | Base labels are one-hot `(n, 80)` but v2 labels are sparse `(n,)` | Convert v2 sparse labels into one-hot or vote/soft-target matrix before using the unmodified v2 merge. |
| `categorical_hinge` or custom `acc` behaves strangely | `y_true` is sparse ids or has wrong class dimension | Use one-hot, vote, or non-negative soft-target labels shaped `(n, 80)`. |
| V2 labels are an 80-column matrix but row sums are unusual | Vote/statistical labels may not be normalized | This can be intentional. Inspect whether each row has non-negative values and at least one positive class; normalize only if the experiment requires it. |

## Model artifact confusion

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| User passes `12306.image.model.h5` to text prediction | Confusing image-tile and prompt-text models | Use `model.h5` or a text artifact such as `model.v1.0.h5`, `model.v1.9.h5`, or `model.v2.0.h5` for prompt text crops. Route tile-model work to image modeling. |
| `model.h5` missing during `predict`/batch prediction | Deployed text model artifact is absent | Train/select a text model artifact and copy or symlink it as the deployed `model.h5`, or update the prediction code to load the chosen text artifact. |
| Output probabilities have last dimension not equal to 80 | Wrong model file or incompatible final layer | Confirm the final Dense/softmax output is 80 classes and matches the label vocabulary. |

## Batch prediction and review-output failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `_predict` cannot find `data.npy` | Text crops were not produced or are in another directory | Route to data preparation to create text crops, then save them as `(n, h, w)` before prediction. |
| `show` writes confusing filenames | Filenames use integer class ids, not Chinese label names | Use the root label vocabulary to map ids to names during review; do not assume `classify/12.*.jpg` names contain semantic labels. |
| `classify/` contains stale images from an older run | Directory is reused | Clear or archive `classify/` before rerunning `show`. |
| `cv2.imwrite` silently fails | Output directory permissions or invalid image dtype/shape | Check write permissions and ensure each crop is image-like, commonly uint8 `(h, w)` or `(h, w, c)`. |

## Training-expense guidance

- Do not use `main()`, `main_v19()`, or `main_v20()` as quick verification. Use the asset checker and a tiny synthetic script first.
- Base training: 100 epochs, sparse labels, saves `model.v1.0.h5`.
- v1.9 fine-tuning: requires `model.v1.0.h5`, `texts.npz`, and compatible `texts.v2.npz`; trains another 100 epochs and saves `model.v1.9.h5`.
- v2.0 training: 10 sparse warm-up epochs plus 100 v2 fine-tuning epochs; saves `model.v2.0.h5`.
- CPU training is possible in principle but may be slow; if the user has a GPU, verify the TensorFlow backend separately before promising speedups.

## Safety boundaries

- Do not import or run credentialed OCR support code while working on text modeling; OCR labeling belongs to data preparation and requires explicit credentials/network handling.
- Do not fetch datasets or model files automatically unless the user explicitly approves the source and destination.
- Keep local environment paths and private artifact directories out of any reusable runtime instructions.
