# Training troubleshooting

- **Missing class data or prompt**: when prior preservation is enabled without a concept manifest, both class fields are required.
- **Malformed concept JSON**: validate the manifest before launching the accelerator job.
- **Modifier-token count mismatch**: the modifier token list and initializer token list must be the same length or the initializer list must be longer.
- **Duplicate modifier token**: the target tokenizer already contains the token string you chose.
- **Initializer token is multi-token**: pick an initializer that encodes to exactly one token.
- **Wrong freeze mode**: use `crossattn_kv` for the default K/V-only update or `crossattn` for full cross-attention updates.
- **xformers unavailable**: install the optional dependency or leave the flag off.
- **bitsandbytes missing**: do not use `--use_8bit_adam` until the package is installed.
- **OOM or slow training**: reduce the batch size, enable gradient checkpointing, use fp16/bf16, or lower the resolution.
- **SDXL memory pressure**: the XL branch is heavier and needs more VRAM than the standard diffusers route.
- **Real-prior retrieval is blocked**: switch to a local prior bundle or wait for network access before enabling `--real_prior`.
- **Hub push fails**: verify the token, repository id, and output directory before retrying.
