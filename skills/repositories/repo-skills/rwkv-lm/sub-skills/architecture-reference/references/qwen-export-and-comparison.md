# Qwen3.5 export and RWKV-7 comparison

## What the repository compares

The RWKV-LM comparison scripts juxtapose RWKV-7 tensors with Qwen3.5 text-model
tensors. They are not claiming the checkpoints are drop-in compatible. The goal
is to compare parameter counts, state sizes, layer roles, and qualitative tensor
families.

Examples from the repository notes:

- RWKV-7 V65536-L24-D1024 has roughly 450M parameters.
- Qwen3.5 V248320-L24-D1024 is larger because of vocabulary and architecture
  differences.
- RWKV-7 state size is independent of prompt length, while Qwen GQA state grows
  with token count.

## Exporting Qwen text state

Use `scripts/export_qwen_text_state.py` to create a `.pth` file from a Hugging
Face model id or local directory. The helper:

- reads `config.json`
- loads `.safetensors` or `.bin` shards
- drops vision projector/tower tensors
- strips the `model.language_model.` prefix when present
- drops MTP tensors
- writes `<output>.json` metadata with dtype counts and tensor counts

Run with `--local-files-only` when network access is not approved.

## Comparison workflow

1. Export the Qwen text checkpoint.
2. Provide a local RWKV-7 `.pth` checkpoint.
3. Confirm both checkpoints are CPU-loadable with `torch.load` or safetensors.
4. Compare shape tables before comparing logits.
5. Use fixed probe text and deterministic tokenizer settings.

## Common mismatch sources

- Qwen tokenizer and RWKV tokenizer produce different token ids.
- Vision or MTP tensors were not removed from the Qwen export.
- `language_model` prefixes were not stripped.
- RWKV checkpoint is from a different model size than the hard-coded shape
  assumptions.
- A checkpoint was saved through a training wrapper that adds `_forward_module.`
  or similar prefixes.

Treat these as conversion/debugging issues, not training-data issues.
