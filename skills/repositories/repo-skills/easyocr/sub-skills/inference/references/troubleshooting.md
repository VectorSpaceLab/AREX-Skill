# EasyOCR Inference Troubleshooting

Use this page for OCR-workflow problems that are specific to ordinary EasyOCR
usage.

## Result looks wrong or unstable

### Wrong language combination

Some language families only work in specific combinations with English. If the
reader raises a compatibility error, reduce `lang_list` to one of the supported
family combinations and retry.

### Output shape confusion

- `detail=0` returns only strings.
- `detail=1` returns tuples or dicts.
- `readtext_batched` returns a list of result lists.
- `recognize` expects box lists or a full-image crop.

### Rotation and paragraph behavior

- `rotation_info` should be a real Python list when using the API.
- `paragraph=True` changes the grouping behavior and can change the number of
  returned boxes.

## CLI-specific problems

### Boolean flags act truthy

The current source uses `type=bool` for several CLI arguments. That means
non-empty strings such as `False` or `0` still behave as truthy values. If you
need a reliable false value, use the Python API or a bundled helper script
instead of the raw CLI flag.

### `rotation_info` is awkward on the CLI

The current CLI parser uses `type=list`, so list-valued input is not parsed the
way users usually expect. Pass rotation data through the Python API instead.

## Runtime and model issues

### Missing model files

If downloads are disabled and the cache is empty, `Reader` raises a missing-file
error. Either allow download once or pre-populate the cache directory.

### Unexpected CPU fallback

`gpu=True` can still fall back to CPU if no supported accelerator is available.
Check the actual `reader.device` value after construction.

### Quantization toggle surprise

The current source stores `Reader.quantize` as a one-item tuple, so disabling
quantization is not a reliable truthiness check. Verify the actual downstream
behavior if the exact CPU path matters.

### `readtextlang` is brittle

That helper expects a local `characters/` directory and is not a general
workflow entry point. Prefer `readtext` or `readtext_batched` for normal use.

## When to use the bundled smoke script

- Use `scripts/readtext_smoke.py` when you want a one-image OCR check without
  remembering all of the constructor and method options.
- Use `../../../scripts/inspect_runtime.py` when you only need an install/backend smoke.
