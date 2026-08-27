# Configuration Troubleshooting

## Purpose

Use this when a config file, registry extension, or dataset layout does not behave the way the docs say it should.

## Common failures

### Nested config overrides do not apply

**Symptoms**
- A value in the final config still looks like the base config.
- `--cfg-options` changes one field but leaves a nested field untouched.

**Likely causes**
- The override path does not match the actual nested structure.
- `_delete_=True` was needed but omitted.

**Recovery**
- Print the merged config with `scripts/print_config.py`.
- Update the override path or add `_delete_=True` when replacing a nested dict.

### Custom class not found in the registry

**Symptoms**
- `KeyError` or registry build failure when a custom model/loss/hook name is used.

**Likely causes**
- The module was never imported.
- `custom_imports` points at the wrong module path.
- The class was added to the wrong registry.

**Recovery**
- Import the module in the relevant `__init__.py`, or use `custom_imports`.
- Re-run the config printer to make sure the import happens before build time.

### Dataset or pipeline keys do not match

**Symptoms**
- A loader or collector complains about missing keys.
- Translation inputs come out empty or the wrong domain is used.

**Likely causes**
- Paired vs unpaired folder layout is wrong.
- The pipeline expects `img_a`/`img_b` but the collector is producing different names.
- `sample_img2img_model` was used with a config that is not a translation model.

**Recovery**
- Check `references/data-formats.md`.
- Match the pipeline keys to the expected dataset output names.
- Use the translation sub-skill only with a `BaseTranslationModel` subclass.

### Loss mapping with `data_info` fails

**Symptoms**
- A custom loss receives the wrong tensor or raises a key error.

**Likely causes**
- `data_info` names do not match the model's output dict.
- The loss expects a dict but is called with a bare tensor.

**Recovery**
- Inspect the model's `train_step` output dict.
- Map the loss inputs to the exact output keys.
- Re-test with a tiny config before entering a full training run.

### Runtime hook or optimizer config does nothing

**Symptoms**
- The training loop runs, but the hook or optimizer change is not visible in logs.

**Likely causes**
- The hook name is not registered.
- The config block is in the wrong place.
- A distributed setting conflicts with the chosen hook.

**Recovery**
- Verify the class is in the correct registry.
- Confirm the runtime block is under the config name expected by the runner.
- Compare with the patterns in `docs/en/tutorials/customize_runtime.md`.

## When to escalate

Ask for help or a narrower scope when the issue needs:

- A repo code change.
- A new package dependency.
- A data-layout rewrite.
- A backend change from CPU to CUDA or vice versa.
