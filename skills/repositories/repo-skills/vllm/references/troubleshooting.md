# Cross-Cutting Troubleshooting

Use this reference before diving into sub-skill-specific troubleshooting when the symptom is broad: install/import failure, backend mismatch, CLI discovery failure, model download/auth, or confusing workflow routing.

## Import or Install Fails

1. Check the active Python can import vLLM:
   ```bash
   python -c "import vllm; print(vllm.__version__)"
   ```
2. Check package metadata and dependency consistency:
   ```bash
   python -m pip show vllm
   python -m pip check
   ```
3. If building from a vLLM checkout, use the repository’s documented `uv` workflow and do not mix system Python packages with the repo environment.
4. Match the install variant to the hardware backend: CPU, CUDA, ROCm, XPU, TPU, or vendor-specific builds have different requirements and wheels.

## CLI Is Missing or Flags Differ

- Confirm `vllm` is installed in the Python environment that owns the shell path.
- Prefer `python -m pip show vllm` plus `which vllm` or platform equivalent to catch mixed environments.
- Use `vllm --help`, `vllm serve --help`, and `vllm serve --help=all` for current flags instead of relying on stale snippets.
- Route CLI/server behavior to `sub-skills/openai-serving/`; route memory/parallelism flags to `sub-skills/deployment-performance/`.

## Backend or Hardware Mismatch

Symptoms include CUDA unavailable, Triton disabled, unsupported dtype, missing kernels, NCCL/Ray failures, OOM, or unexpectedly slow CPU fallback.

- Collect Python, torch, CUDA/ROCm, GPU count, driver, and vLLM version facts before changing commands.
- Avoid claiming GPU readiness from an import-only check; run a bounded model/backend smoke only when the user confirms hardware and model availability.
- For OOM or capacity planning, route to `sub-skills/deployment-performance/` and adjust `--tensor-parallel-size`, `--gpu-memory-utilization`, `--max-model-len`, `--kv-cache-memory-bytes`, dtype, quantization, or CPU offload deliberately.

## Model Download, Auth, or Remote Code

- Hugging Face model access may require credentials or license acceptance.
- `trust_remote_code=True` or `--trust-remote-code` executes model repository code; ask before enabling it.
- Prefer explicit model identifiers and revisions for reproducibility.
- For local model paths, verify files exist and match the model architecture expected by vLLM.

## Wrong Workflow Route

- Python-only script and output objects: `sub-skills/offline-inference/`.
- HTTP server/client, `/v1`, auth, port, and model discovery: `sub-skills/openai-serving/`.
- JSON schema, grammar, tools, reasoning parsers, and streaming tool-call deltas: `sub-skills/structured-tool-reasoning/`.
- Images/audio/video, LoRA/adapters, embeddings, rerank, score, and pooling shapes: `sub-skills/modalities-adapters-pooling/`.
- Deployment, metrics, profiling, parallelism, memory, quantization, and benchmarks: `sub-skills/deployment-performance/`.
