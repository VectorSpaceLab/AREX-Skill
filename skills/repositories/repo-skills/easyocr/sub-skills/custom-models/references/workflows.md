# EasyOCR Custom Model Workflows

This reference explains how EasyOCR loads a custom recognition bundle.

## 1. Bundle layout

The bundle must share one stem across three files:

- `<stem>.pth` — the trained weights
- `<stem>.yaml` — the recognition configuration
- `<stem>.py` — the model definition

Place the YAML and Python file in `user_network_directory`. Place the weight
file in `model_storage_directory`.

Typical default locations are under `~/.EasyOCR/` unless the caller overrides
them with constructor arguments or environment variables.

## 2. Minimal load pattern

```python
import easyocr

reader = easyocr.Reader(
    ['en'],
    recog_network='custom_example',
    user_network_directory='~/.EasyOCR/user_network',
    model_storage_directory='~/.EasyOCR/model',
)
```

The `recog_network` value must match the shared stem.

## 3. YAML fields that matter most

The bundle YAML should provide at least:

- `imgH` — model image height if the bundle uses a custom height.
- `lang_list` — the language list the bundle supports.
- `character_list` — the output character set.
- `network_params` — constructor arguments for the custom `Model` class when
  the bundle is not one of the built-in generations.

## 4. Compatibility rules

- The requested `lang_list` must be compatible with the bundle's supported
  languages.
- If `imgH` is set, EasyOCR uses it when preparing recognition crops.
- The `.py` file must be importable from `user_network_directory`.

## 5. Validation before load

Use the bundled validator before trying to load the model:

```bash
python scripts/check_bundle.py /path/to/custom_example
```

This catches the most common bundle mistakes before the runtime path fails.

## 6. When to prefer the built-in models instead

If the task only needs ordinary OCR on built-in languages, use the inference
sub-skill. Reserve custom bundles for cases where the caller explicitly has a
trained recognition model or needs a private model family.
