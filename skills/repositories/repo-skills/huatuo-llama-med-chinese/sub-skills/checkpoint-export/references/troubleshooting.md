# Checkpoint export troubleshooting

## `BASE_MODEL` assertion failure

Symptom:

```text
Please specify a value for BASE_MODEL environment variable
```

Cause: the export logic reads the base model from `BASE_MODEL` and asserts that it is non-empty.

Fix:

- Pass `--base-model` to the bundled command builder and verify the emitted command includes `BASE_MODEL=...`.
- If running an adapted exporter manually, export the variable first:

  ```bash
  export BASE_MODEL=/path/or/hf-model-id
  ```

- Use a base model compatible with the adapter. A valid path still fails later if the architecture or tensor shapes do not match.

## Adapter path is unexpectedly `tloen/alpaca-lora-7b`

Symptom: the export loads the wrong adapter, downloads an unrelated Alpaca LoRA, or fails because that adapter id is unavailable.

Cause: the source export scripts hard-code `tloen/alpaca-lora-7b` in `PeftModel.from_pretrained(...)`.

Fix:

- Use the bundled command builder's `--adapter-weights` argument.
- Point it to the actual Huatuo LoRA adapter directory or compatible Hugging Face adapter id.
- For downloaded adapters, verify the directory has `adapter_config.json` and `adapter_model.bin` at its top level.

## Missing base model or adapter files

Symptoms:

- `OSError` or `FileNotFoundError` from `from_pretrained`.
- Authentication or network errors while resolving a Hugging Face id.
- Adapter config/model file not found.

Fix:

- Use local paths for offline or restricted environments.
- Confirm read permissions and available disk space.
- If using Hugging Face ids, confirm any required authentication is configured outside the generated skill content.
- Do not pass the parent directory of multiple adapters; pass the specific adapter folder containing the PEFT files.

## Architecture mismatch

Symptoms:

- Attribute errors around `model.layers`, `self_attn.q_proj`, or `base_model.model.model.layers`.
- Tensor shape mismatch during LoRA load or merge.
- `NotImplementedError` from state-dict key translation.
- Output checkpoint loads but produces invalid results.

Cause: the export logic is LLaMA-specific. State-dict export is additionally hard-coded for LLaMA-7B parameters: `dim=4096`, `n_heads=32`, `n_layers=32`, and one output shard.

Fix:

- For Bloom, Huozi, ChatGLM, or other non-LLaMA adapters, do not use state-dict mode.
- For non-7B LLaMA variants, redesign the parameter table and verify the key translation before exporting.
- For adapter inference without merging, route to the inference sub-skill instead of forcing a checkpoint export.

## CPU RAM or storage exhaustion

Symptoms:

- Process is killed with no Python traceback.
- `RuntimeError` or allocator errors during model load/merge.
- Disk fills while writing `hf_ckpt/` shards or `ckpt/consolidated.00.pth`.

Fix:

- Run on a host with enough CPU RAM for a 7B half-precision base model plus merge overhead.
- Use a large local disk for output; Hugging Face mode can produce many `400MB` shards.
- Avoid merging multiple adapters in one process; restart between attempts to release memory.
- Confirm `OUTPUT_DIR` points to a writable filesystem with enough free space.

## PEFT, Transformers, or Torch version mismatch

Symptoms:

- `merge_weights` does not merge.
- `merge_and_unload` is missing or behaves differently than expected.
- `LlamaTokenizer` or `LlamaForCausalLM` load errors after dependency upgrades.
- State-dict keys differ from the expected LLaMA key map.

Context: the repository requirements pin `peft==0.3.0`, `transformers==4.30.1`, and `accelerate==0.20.1`; `torch` must be installed separately in a compatible version.

Fix:

- Prefer a clean environment close to the pinned dependency versions when reproducing source behavior.
- If using newer PEFT, prefer an exporter that calls `merge_and_unload()` and validate the saved checkpoint by loading it back.
- If keys changed after dependency upgrades, inspect the merged model state dict and update the key translator before using state-dict mode.
- Treat a successful Python import as insufficient; perform a small load-back or checksum-level sanity check when resources allow.

## Difficult usability cases

- A user asks for state-dict export of a Bloom/Huozi adapter. Decline state-dict mode because the key translation and LLaMA-7B params do not apply; use only an architecture-specific Hugging Face export path after implementing and validating it.
- A user supplies an adapter path but leaves `BASE_MODEL` unset. Do not guess the base model; require an explicit base model path/id because PEFT adapters do not reliably encode the exact local base checkpoint needed for a safe merge.
