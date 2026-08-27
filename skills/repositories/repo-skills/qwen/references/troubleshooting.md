# Cross-cutting Troubleshooting

## Install and import

- `ModuleNotFoundError: transformers_stream_generator`, `tiktoken`, `accelerate`, or `einops`: install the narrow base requirements file in the active environment and rerun `python scripts/check_qwen_environment.py --check-dependencies`.
- A missing top-level `qwen` distribution is expected for this historical repository: it is primarily scripts, recipes, and checkpoint-side remote code rather than an installable package. Validate the documented dependencies and the specific helper or server instead of trying `import qwen`.
- If a server imports but a web demo does not, keep the API/base environment separate from the Gradio web extra; do not upgrade every package blindly.

## Checkpoint and remote code

- `qwen.tiktoken` not found: the checkpoint is incomplete, the model files were not fetched with Git LFS, or a local export omitted tokenizer assets. Re-check the local directory before changing Python code.
- `Tokenizer class QWenTokenizer does not exist`: keep `trust_remote_code=True` on tokenizer/model loads and check that the checkpoint-side code is present. Older PEFT versions may be needed for the historical tokenizer behavior.
- Sharded checkpoint load failures usually mean missing or partially downloaded shards. Compare the local files with the model manifest and prefer a complete ModelScope snapshot or a verified local copy.
- Gibberish during streaming can be caused by stale checkpoint-side tokenizer/model code or byte-token decoding. Refresh the checkpoint-side code before changing generation parameters.

## Model and task mismatch

- Instruction-following is poor when a base `Qwen-*` model is used for a chat prompt. Route to the corresponding `Qwen-*-Chat` checkpoint.
- Unexpected memory use is often a combination of model size, precision, batch size, sequence length, KV cache, and automatic device placement. Reduce one dimension at a time and record the device map.
- CPU-only inference is supported but can be extremely slow. Do not present it as a performance fallback for production.
- `use_cache_quantization` and FlashAttention are not a safe combined assumption. The repository documents that KV-cache quantization and FlashAttention cannot be used together; choose one path and inspect the loaded config.

## Optional backends

- FlashAttention install failures are usually unsupported GPU generation, mismatched torch/CUDA ABI, missing compiler/toolkit, or an unnecessary optional dependency. First remove it and prove the native path works.
- AutoGPTQ errors commonly indicate an incompatible torch/CUDA/Transformers/Optimum/PEFT matrix. Use a matching prebuilt wheel or an isolated environment; do not repair a user environment silently.
- vLLM/FastChat errors can come from GPU compute capability, dtype mismatch, missing ChatML template, tensor-parallel size, or model remote-code support. Check the serving sub-skill's topology before changing flags.
- DeepSpeed/QLoRA/FSDP errors often reflect incompatible combinations. Read the fine-tuning matrix before switching ZeRO stages or precision.

## API, data, and service failures

- A `400` from the local OpenAI-compatible API usually means no user message, invalid role ordering, an odd user/assistant history, or function-calling requested with streaming. Validate the message array before starting the server.
- A Docker helper refusing a checkpoint means `config.json` is absent at the mount source. Fix the checkpoint path, not the container image.
- Bind services to loopback by default. Use `0.0.0.0` only when network exposure is deliberate, and add authentication or an upstream access control layer.
- DashScope and other hosted services require credentials and network access. Never put API keys in generated scripts or test fixtures.

## Evaluation and safety

- Benchmark scripts need exact dataset layouts and often a checkpoint/GPU. A command that starts successfully is not a valid score unless the dataset, model, seed, and result files are recorded.
- HumanEval executes model-generated code. Use a robust sandbox and explicit approval; do not enable arbitrary execution as an import smoke test.
- Preserve the Qwen license and run application-specific red-teaming before public deployment; model outputs may be inaccurate or harmful.
