# Inference Troubleshooting

## Purpose

Read this when checkpoint-based transcription fails or when the user wants a speed tweak that depends on optional GPU support.

## Common issues

### Model download or gated access fails

- **Symptoms:** `401`, `403`, timeout, or a dataset/model download error.
- **Likely causes:** no Hugging Face login, missing dataset acceptance, or blocked network.
- **Recovery:** sign in to the Hub, accept any dataset terms, or switch to a public tiny fixture before retrying.

### CUDA or flash-attn is missing

- **Symptoms:** `torch.cuda.is_available()` is false, `flash_attn` import fails, or the user asks for GPU speedups that are unavailable.
- **Likely causes:** CPU-only wheels, missing CUDA libraries, or an unsupported wheel tag.
- **Recovery:** use the CPU path for correctness, or install the GPU wheel only when the user truly needs the speed path.

### The wrong checkpoint is chosen for the task

- **Symptoms:** the user asks for multilingual transcription or memory-constrained inference and gets an oversized checkpoint.
- **Likely causes:** the route did not mention the English-only limitation or the smaller checkpoint option.
- **Recovery:** use `distil-large-v3` for the default path and `distil-small.en` when memory is the primary constraint.

### Long-form output looks truncated or repetitive

- **Symptoms:** the transcription is cut off, repeats near chunk boundaries, or misses timestamps.
- **Likely causes:** chunk length, generation length, or timestamp configuration is not tuned for the sample.
- **Recovery:** compare sequential and chunked long-form modes, then adjust `chunk_length_s`, `max_new_tokens`, and `return_timestamps`.

## Read next

- Use `references/workflows.md` for copyable recipes.
- If the issue is about training data, initialization, or evaluation, route to the PyTorch or Flax sub-skill instead.
