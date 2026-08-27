# EasyOCR Custom Models Troubleshooting

Use this page when a custom recognition bundle does not load or behaves oddly.

## Missing bundle files

### Missing `.pth`, `.yaml`, or `.py`

EasyOCR expects the same stem across all three files. If one file is missing or
named differently, fix the stem and retry.

### Wrong directory

The YAML and Python files must be in `user_network_directory`; the weight file
must be in `model_storage_directory`. A bundle often fails simply because one of
the directories was not passed to the constructor.

## Import and YAML failures

### Python module import fails

The custom `.py` file is imported from `user_network_directory`. Make sure the
file is importable and that it defines the expected `Model` class.

### YAML parse or missing-key errors

Check that the YAML file contains the fields the bundle expects, especially
`imgH`, `lang_list`, `character_list`, and `network_params` when the custom
model needs them.

## Compatibility failures

### `lang_list` mismatch

The `lang_list` passed to `Reader` must be compatible with the bundle's own
language list. Reduce the requested languages or update the bundle metadata.

### Missing or wrong `imgH`

If the bundle uses a custom image height, an incorrect `imgH` value can change
how the crops are resized and can ruin recognition quality.

## Runtime model failures

### Missing `.pth` file with downloads disabled

If downloads are disabled, EasyOCR will not fetch the weight file. Copy the
weight into `model_storage_directory` or enable downloads once.

### `recog_network` stem typo

The value passed to `recog_network` must match the file stem exactly. A single
mismatch causes EasyOCR to look for the wrong YAML and Python module.

## Best first fix

Run `scripts/check_bundle.py` on the bundle stem or bundle directory before
changing the runtime code. That catches the common file-layout mistakes first.
