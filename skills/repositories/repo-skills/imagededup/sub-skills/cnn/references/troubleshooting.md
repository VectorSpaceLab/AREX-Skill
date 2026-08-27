# CNN troubleshooting

## `No value provided for model and/or transform in model_config ..`

- The `CustomModel` wrapper is incomplete.
- Fix: supply both a model and a transform.

## `Consider setting a custom model name in model_config ..`

- The wrapper still uses the default name.
- Fix: set a specific model name so future readers can tell the model apart from the packaged default.

## `Please provide a valid directory path!`

- The path passed to `encode_images` or directory-based duplicate search is not a directory.
- Fix: pass a real image directory.

## `Please provide either image file path or image array!`

- `encode_image` received an unsupported input type.
- Fix: pass a file path or numpy array.

## `Threshold must be a float between -1.0 and 1.0`

- The similarity threshold is not a float in the valid range.
- Fix: use a float between `-1.0` and `1.0`.

## Warnings about `recursive` or `num_enc_workers`

- These warnings usually mean an `encoding_map` was supplied and the directory-only flags are irrelevant.
- Fix: remove the irrelevant flag rather than suppressing the warning.

## Worker-count behavior differs by platform

- The CNN encoding path parallelizes only on Linux.
- Fix: on other platforms, expect `num_enc_workers` to be coerced to `0`.

## Device selection is not what you expected

- `CNN()` uses CUDA only when `torch.cuda.is_available()` is true.
- Fix: inspect the active environment's torch build and GPU visibility.
- A successful CPU import does not prove the CUDA path works.

## First-use model download problems

- The default pretrained wrapper may need to download weights the first time it is instantiated.
- Fix: allow network access, warm the cache, or use a custom model when offline.

## Custom model shape mistakes

- A custom model that does not return one feature vector per image will usually fail later in encoding or duplicate search.
- Fix: ensure the transform and model agree on the expected input shape and output feature size.

## Plotting or evaluation issues nearby

- If you already have a duplicate map and only need metrics or a figure, move to the evaluation sub-skill instead of staying here.

## When to escalate

- If the request is actually about hash encodings or Hamming distance, switch to the hashing sub-skill.
- If the request is actually about scoring or plotting a duplicate map, switch to the evaluation sub-skill.