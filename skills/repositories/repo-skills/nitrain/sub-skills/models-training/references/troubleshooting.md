# Troubleshooting

## Purpose

Use this for predictable model and trainer failures.

## Common failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `Architecture function ... does not exist` | The requested architecture name or dimension does not match an `antspynet` constructor. | Check `list_architectures()` and use the exact family name and dimension. |
| `Trainer` or `Loader.to_keras()` cannot import TensorFlow | The Keras/TensorFlow stack is missing. | Install `tensorflow==2.17.0` and `tf-keras==2.17.0`, then rerun the smoke helper. |
| `If task is None then optimizer and loss must be supplied` | `Trainer` was created without enough defaults. | Pass both `optimizer` and `loss`, or set an explicit task. |
| `Valid tasks: regression, segmentation, classification` | The task string is misspelled. | Use one of the supported task names. |
| `Could not infer framework from model` | The model type string did not include `keras`, `torch`, or `monai`. | Pass a supported model type or wrap the model with the intended framework. |
| `nitrain.fetch_pretrained` is not callable | The package root export is the module object in this snapshot. | Import the function from `nitrain.models.fetch_pretrained`. |
| `fetch_pretrained(...)` fails to download or cache weights | The model name is wrong, the cache path is not writable, or the host has no network access. | Check the model name, pass a writable `cache_dir`, or retry with network access. |
| `TorchTrainer` import fails from `nitrain` | The class is not exported at the package root. | Import it from `nitrain.trainers`. |
| `pip check` reports `monai` wants a newer `torch` | The torch wheel is older than the verified CPU combination. | Install `torch==2.8.0+cpu` before `monai`. |
| TensorFlow prints CUDA/TensorRT warnings | The host is CPU-only for the verified path. | Treat the warning as expected unless you are explicitly testing CUDA. |

## Recovery steps

1. Verify that the model family name exists in `list_architectures()`.
2. Confirm whether you want Keras/TensorFlow or Torch/MONAI.
3. Keep the first smoke model tiny so you can separate import issues from fit
   issues.
4. If you need pretrained weights, make sure network access or cache access is
   available.

## Good signals

- `Trainer` reports `framework=keras` for Keras models.
- `TorchTrainer` can be instantiated and a tiny MONAI model can run a forward
  pass on CPU.
- Architecture discovery returns a non-empty list.

## Hand off when

- the task has moved from model construction into inference output handling;
- the main issue is actually data loading or preprocessing;
- the user wants only a pretrained network wrapper and not the training surface.
