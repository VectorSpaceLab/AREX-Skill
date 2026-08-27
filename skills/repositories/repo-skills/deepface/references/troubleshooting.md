# Cross-Cutting Troubleshooting

Read this before deep workflow debugging when the failure is import, dependency, model-weight, optional backend, input, API, or service related.

| Symptom | Likely cause | Recovery |
|---|---|---|
| `ModuleNotFoundError: No module named 'deepface'` | Package not installed in the active Python environment. | Install with `pip install deepface`, then run `python scripts/check_deepface_environment.py`. |
| `No module named 'tf_keras'` or a message saying TensorFlow requires `tf-keras` | TensorFlow/Keras version uses Keras 3 behavior while DeepFace or RetinaFace expects legacy Keras compatibility. | Run `pip install tf-keras`, then retry `from deepface import DeepFace`. |
| TensorFlow logs say CUDA drivers are missing | Installed TensorFlow cannot use CUDA. | This is not a DeepFace import failure. Use CPU, or install a compatible CUDA/TensorFlow stack only if acceleration is required. |
| Import fails inside optional detector or database modules | Optional dependency missing. | Route to `sub-skills/model-and-backend-selection/` for detector extras or `sub-skills/datastore-search/` for database clients. |
| Model build/load fails after an interrupted download | The weight cache has an incomplete or wrong file. | Ask before deleting the specific cached weight file, then rebuild only the one needed model. |
| `Confirm that ... exists` | Local path does not exist in the runtime process. | Use an application-visible path or pass a NumPy array/file object. |
| `Input image must not have non-english characters` | Path string contains non-ASCII characters. | Pass a NumPy array or move/copy to an ASCII-only path. |
| `Failed to decode image` | File-like object or base64 content is not a valid image. | Validate JPEG/PNG bytes first; route to `detection-and-demography` input checker. |
| HTTP 401 from the API | Bearer auth is enabled and token is missing or wrong. | Add `Authorization: Bearer <token>` or disable auth for local testing. |
| API database route says connection details are missing | DB env vars are not configured. | Set `DEEPFACE_CONNECTION_DETAILS` or backend-specific variables and validate with the datastore helper. |

## Model Weights And Network

DeepFace downloads weights when a model is built for the first time. Avoid building all models unless the user explicitly asks for a full model-cache preparation pass. Treat remote image URLs and API calls as network operations too.

## Diagnostic Helper

From this skill directory:

```bash
python scripts/check_deepface_environment.py --json
```

The helper checks imports and inventories without building models, downloading weights, connecting to databases, or opening a webcam.
