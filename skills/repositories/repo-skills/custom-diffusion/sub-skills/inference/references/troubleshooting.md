# Inference troubleshooting

- **CUDA is missing**: the sampler expects a CUDA runtime. Do not treat a CPU import as a valid substitute for this route.
- **Model cache is missing**: the base model and tokenizer must be available locally or downloadable from the Hugging Face cache path you are using.
- **Compressed delta passed without the matching flag**: inspect the layout and make the sampler flag match the checkpoint payload.
- **Uncompressed delta passed as compressed**: the sampler should not try to reconstruct `u` / `v` factors unless the checkpoint actually contains them.
- **Prompt file has blank lines**: remove them before sampling so you do not generate empty prompts.
- **Prompt filename collisions**: long prompts are truncated when the montage file is named, so shorten or normalize them if files overwrite each other.
- **Wrong freeze mode**: the delta must be sampled with the same freeze mode that produced it.
- **SDXL path mismatch**: use the XL pipeline for XL checkpoints and the standard path for non-XL checkpoints.
- **Network download failures**: model downloads are outside the sample layout contract; cache the model first when network access is unreliable.
