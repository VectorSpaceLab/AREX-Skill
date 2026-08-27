# Model and Data Artifacts

## Purpose

Read this before moving between easy12306 sub-skills. The repository uses a small set of hard-coded legacy filenames; future agents should preserve their roles even when using bundled adapters with explicit paths.

## Required for pretrained inference

| Artifact | Owner | Required by | Meaning | Validation |
| --- | --- | --- | --- | --- |
| `model.h5` | text prompt classifier | `inference` | Deployed Keras/TensorFlow model that classifies cropped prompt text into the 80-label vocabulary. | `sub-skills/inference/scripts/check_inference_assets.py --text-model model.h5`; optionally `--load-models`. |
| `12306.image.model.h5` | image-tile classifier | `inference` | Deployed Keras/TensorFlow model that classifies each 67x67 object tile into the same 80 labels. | `sub-skills/inference/scripts/check_inference_assets.py --image-model 12306.image.model.h5`; optionally `--load-models`. |
| `texts.txt` | shared label vocabulary | all model workflows | UTF-8, exactly 80 non-empty rows; zero-based row index is model class id. | Root [label-vocabulary.md](label-vocabulary.md) and each sub-skill checker. |
| captcha image | inference input | `inference` / `data-preparation` | Full 12306 captcha image with prompt text and 2x4 object grid. | `sub-skills/inference/scripts/check_inference_assets.py --captcha-image <img>` or data-prep diagnostic. |

## Generated or training-time artifacts

| Artifact | Produced/consumed by | Expected schema or role | Notes |
| --- | --- | --- | --- |
| `data/data.npz` | `data-preparation` | arrays `texts` shaped `(N,19,57)` and `images` shaped `(N,8,8)` packed hash bytes | Created from captcha images after crop/tile/hash extraction. |
| `texts.npz` | `text-modeling` | arrays `texts` and `labels`; `texts` reshaped to `(-1,h,w,1)` after division by 255; labels usually sparse ids | Base prompt-text training data. |
| `texts.v2.npz` | `text-modeling` | additional statistical text data; labels may be one-hot/vote matrix for merge workflows | Used by later fine-tuning paths. |
| `model.v1.0.h5` | `text-modeling` | first text CNN model artifact | Source workflow saves without optimizer. |
| `model.v1.9.h5` | `text-modeling` | fine-tuned text model with categorical hinge loss | Built from `model.v1.0.h5` plus v2 data. |
| `model.v2.0.h5` | `text-modeling` | deeper text CNN fine-tune artifact | Not the same as deployed `model.h5` unless copied/renamed intentionally. |
| `data.npy` / `labels.npy` | `text-modeling` | ad hoc prediction/visualization arrays | Used by `_predict()`/`show()` style exploratory labeling. |
| `captcha.npz` | `image-modeling` | arrays `images` shaped `(N,H,W,3)` and `labels` as sparse ids or 80-column vote/probability matrix | Statistical image-tile training set. |
| `captcha.test.npz` | `image-modeling` | arrays `images` and `labels` for manual validation | Used as validation/evaluation data. |
| `images.npz` | `data-preparation` / `text-modeling` | hash-to-label vote table from image hashes and predicted text labels | Created by the hash-label aggregation workflow. |
| `loss.jpg` | modeling workflows | matplotlib loss plot | Generated review artifact, not required for inference. |
| `classify/`, `errors/`, `imgs/` | data/model diagnostics | generated directories | Treat as user/workflow outputs, not runtime skill content. |

## Artifact handoff rules

1. Keep `texts.txt` synchronized with every model. A correct model with the wrong label order is operationally wrong.
2. Validate file existence, label counts, and array schemas before loading `.h5` models or starting training.
3. Do not treat downloaded pretrained models as bundled skill assets. The original README referenced external storage, but this skill only records the expected contract.
4. Do not run full training or download loops as smoke tests. Use the bundled inspection scripts for fast checks and ask for explicit approval before network or long-running work.
5. When adapting workflows, prefer explicit artifact paths over hard-coded working-directory filenames while preserving artifact roles and output class order.
