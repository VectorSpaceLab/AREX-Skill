# language-models troubleshooting

## Purpose

Read this when a GPT-family module, tokenizer helper, or MoE/flash-attention catalog fails to import or resolve a config.

## Common failures

### `ModuleNotFoundError: No module named 'tokamax'` or `qwix`

**Likely cause:** The MoE / flash-attention path pulled in optional packages that are not installed.

**Recovery:** Install the optional dependency set required by the specific GPT family you are inspecting, then re-run the import or config probe.

**Note:** Some catalogs import MoE helpers transitively even when you are only trying to inspect a config name. If that happens, use the family module that does not require the missing optional package, or install the dependency.

### `AttributeError` involving `jax.core.Effect` or a Flax/JAX incompatibility

**Likely cause:** The installed JAX and Flax versions are out of sync with the GPT optional dependencies.

**Recovery:** Reinstall the compatible package set for the AXLearn GPT workflow, then re-run the import.

### Tokenizer file not found

**Likely cause:** The vocabulary helper could not find the tokenizer JSON or SentencePiece model under the configured data directory.

**Recovery:**

- Set `DATA_DIR=FAKE` to use the packaged repository data where supported.
- Or point `DATA_DIR` to the directory that contains the tokenizer file.

### `named_trainer_configs()` is empty or missing the expected key

**Likely cause:** The wrong family module was imported, or the config name uses a different version/model-size suffix.

**Recovery:** List the exported names with `scripts/inspect_gpt_configs.py` and compare them to the expected family.

## Recovery order

1. Confirm whether the task is about a family module or the shared GPT catalog.
2. Check optional dependency coverage for `tokamax`, `qwix`, and flash-attention paths.
3. Verify the tokenizer file path or `DATA_DIR`.
4. Only then debug mesh-shape or trainer-override issues.
