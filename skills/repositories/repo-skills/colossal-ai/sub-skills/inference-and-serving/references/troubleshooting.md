# Inference and Serving Troubleshooting

## Model and tokenizer failures

- Model path missing: ask for a local path or explicit download approval.
- Tokenizer mismatch: use the tokenizer from the same model family or repository.
- Private model access denied: require a token through the model library's normal secret handling; do not hard-code credentials.
- Diffusion pipeline import error: install compatible `diffusers`, torch, and model-specific dependencies in the inference environment.

## Parallelism failures

- `tp_size` mismatch: match `--nproc_per_node` to `--tp_size` for tensor-parallel generation unless the script documents otherwise.
- Patched diffusion parallelism mismatch: align `patched_parallelism_size` or script flags with launched processes.
- Distributed initialization error: route to `../installation-and-launch/SKILL.md`.

## CUDA and memory failures

- OOM during prefill: reduce `max_batch_size`, `max_input_len`, prompt length, or TP layout.
- OOM during decoding: reduce `max_output_len`, KV cache block count, batch size, or speculative drafter size.
- CUDA graph failure: disable `use_cuda_graph` until basic generation works.
- Optimized kernel failure: disable `use_cuda_kernel`, high precision, or fused features, then re-enable one at a time.

## Speculative decoding failures

- Drafter and main model tokenizer mismatch: use compatible model families.
- Low acceptance or bad output: validate main model generation first, then tune drafter size and `max_n_spec_tokens`.
- GLIDE class import failure: verify the GLIDE model implementation and its dependencies.

## Service failures

- Port in use: choose another port and confirm firewall rules.
- Client benchmark fails before first request: validate a manual request before adding Locust/traffic generation.
- Throughput benchmark unstable: pin batch size, prompt length, output length, dtype, and CUDA graph/kernel settings.
