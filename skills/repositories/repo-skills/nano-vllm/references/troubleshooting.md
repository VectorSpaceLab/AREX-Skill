# Cross-cutting troubleshooting

## Install/import failures

- **`ModuleNotFoundError: flash_attn`** — install a FlashAttention build
  compatible with the installed PyTorch, CUDA toolkit, Python version, and GPU.
  `pip install` may compile from source and therefore needs a CUDA compiler and
  matching headers; a successful `torch` import alone is not enough.
- **`ImportError` from Triton or a compiled CUDA extension** — check that
  `torch.version.cuda`, the driver, the compiler/toolkit, and the extension
  build target agree. Run `python scripts/check_env.py` before changing package
  versions. Avoid mixing CPU-only PyTorch with this package.
- **`pip` resolves an incompatible dependency set** — the project declares
  lower bounds rather than a lock. Pin a mutually compatible torch/triton/
  FlashAttention set in the private environment and record it externally; do
  not modify a user-owned environment without approval.

## Backend and lifecycle failures

- **`CUDA is not available` or `NCCL` initialization fails** — this engine's
  full path is CUDA/NCCL-only. Check `nvidia-smi`, `torch.cuda.is_available()`,
  visible device count, and NCCL access. A CPU import or a mock tensor is not a
  full inference validation.
- **The process hangs on exit** — `LLMEngine` starts spawned workers for tensor
  parallelism and registers `exit()` with `atexit`. Keep construction and
  generation in a normal `if __name__ == "__main__":` entry point, avoid
  repeatedly constructing engines, and explicitly call `llm.exit()` in long-
  lived applications.
- **Port/shared-memory errors with tensor parallelism** — ranks rendezvous on
  localhost and nonzero ranks use shared memory. Use a free rendezvous port in
  a controlled deployment, ensure enough `/dev/shm`, and start with
  `tensor_parallel_size=1`.

## Model/config failures

- **`assert os.path.isdir(model)`** — pass the directory containing the model,
  not a repository id or a single weight file. The engine expects local config,
  tokenizer, and safetensors files.
- **Tokenizer/config cannot be loaded** — verify the directory is a complete
  Hugging Face Qwen3 export and that its `config.json` is readable. The engine
  calls `AutoConfig.from_pretrained` and `AutoTokenizer.from_pretrained`.
- **Unexpected parameter/missing parameter during loading** — inspect the
  model's safetensors names and Qwen3 architecture. The loader maps Q/K/V and
  gate/up projection names into packed parameters; a model family with a
  different naming/layout contract is not automatically supported.

## Capacity and runtime behavior

- **KV-cache allocation asserts or OOMs** — lower `max_model_len`, reduce
  `max_num_batched_tokens`/`max_num_seqs`, or lower the workload; then tune
  `gpu_memory_utilization` conservatively. Do not treat a larger value as a
  universal fix: it leaves less room for temporary allocations.
- **CUDA graph capture fails** — set `enforce_eager=True` to diagnose or run
  on a shape/backend combination that capture supports. Eager mode is a
  correctness fallback, not evidence that graph capture is healthy.
- **Output stops early** — EOS is honored unless `SamplingParams(ignore_eos=True)`;
  completion also stops at `max_tokens`. Check both settings before debugging
  sampling randomness.
- **Different prompt outputs appear mismatched** — `generate` returns records
  in request order after sorting internal sequence ids. Read each record's
  `text` and `token_ids`; do not assume a bare string return.
