# Adapter Workflows

## Merge path

The bundled merge helper plans and can execute a command equivalent to running the copied source from the skill root:

```bash
cd <this-skill-root>
PYTHONPATH=src${PYTHONPATH:+:$PYTHONPATH} python src/merge_lora_weights.py --model-path <adapter-path> --model-base <base-model> --save-model-path <merged-output> --safe-serialization
```

Prefer the helper so paths are derived from the skill location:

```bash
python scripts/adapter_command.py merge --model-path <adapter-path> --model-base <base-model> --save-model-path <merged-output> --safe-serialization
# add --run only when the merge should actually write the output checkpoint
```

## Load path

- If the checkpoint looks like a LoRA adapter, `load_pretrained_model` loads the base model and then merges the adapter.
- If the checkpoint is already merged, the loader treats it like a standard model.
- The merge path should never guess a base model; keep `model-base` explicit.

## Output-path rules

- Always use an explicit save path for merges.
- Treat the merge target as an output artifact, not a source artifact.
- Do not overwrite a previous merge unless the user explicitly asks for it.

## Quantization notes

- Serving can use 4-bit or 8-bit loading when the user needs it.
- Use the model-compatibility reference for the Qwen3.5 Flash Attention fallback.
