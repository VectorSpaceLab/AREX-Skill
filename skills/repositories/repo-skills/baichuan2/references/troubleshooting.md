# Cross-Cutting Troubleshooting

Use this reference when the route is not yet clear or the failure happens before a sub-skill-specific workflow starts.

## Model weights, network, and access

**Symptoms**
- `from_pretrained(...)` hangs or fails.
- Hugging Face reports missing files, gated access, or remote-code errors.
- A local directory lacks tokenizer/config/model files.

**Actions**
1. Confirm the model id: `baichuan-inc/Baichuan2-7B-Chat`, `Baichuan2-13B-Chat`, `Baichuan2-7B-Base`, or `Baichuan2-13B-Base`.
2. Use `trust_remote_code=True` for official Baichuan2 checkpoints.
3. If using a local directory, verify it contains model config, tokenizer files, and weight files.
4. Do not run Chat wrappers against Base checkpoints; switch route or model family.

## CUDA and PyTorch mismatch

**Symptoms**
- `torch.cuda.is_available()` is false on a GPU host.
- Import errors mention unsupported CUDA libraries, missing kernels, or undefined symbols.
- Transformers or PEFT imports fail after installing a newer package version.

**Actions**
1. Install a PyTorch wheel compatible with the host driver, Python version, and GPU.
2. Keep the Transformers and PyTorch versions mutually compatible; if a mirror serves a much newer Transformers release, upgrade the PyTorch wheel or pin Transformers lower.
3. Run:

```bash
python scripts/check_baichuan2_env.py --workflow all --require-cuda
```

A CPU import is not enough for CUDA-native quantization, Chat demos, or DeepSpeed training.

## BitsAndBytes and optional compiled-op warnings

BitsAndBytes and DeepSpeed may print warnings about `CUDA_HOME` or optional compiled ops. Treat them as non-blocking only when:

- imports succeed,
- PyTorch CUDA tensor allocation succeeds,
- the chosen workflow's helper dry-run or import-validation check passes.

For quantization, run:

```bash
python scripts/check_baichuan2_env.py --workflow deployment --require-cuda --check-bitsandbytes-op
```

If the small BitsAndBytes operation fails, do not claim quantization is verified.

## CPU deployment is slow by design

Baichuan2 CPU deployment uses float32 loading and avoids CUDA/BitsAndBytes. It is useful for CPU-only correctness checks, not high-throughput serving. If the user needs interactive speed or 4-bit/8-bit memory reduction, route to deployment and prefer a CUDA path.

## Optional packages from the original requirements

The original requirement files contain a broad set of packages. Do not install every optional package blindly:

- `xformers` is optional training acceleration.
- `cpm_kernels` and `transformers_stream_generator` are not directly imported by the distilled helpers.
- `bitsandbytes` is required only for quantization paths.
- `deepspeed` and `peft` are required for the fine-tuning routes, not for simple inference.

## Route-specific errors

- Inference/API/CLI/Web failures: read `sub-skills/inference/references/troubleshooting.md`.
- Quantization, CPU loading, or checkpoint conversion failures: read `sub-skills/deployment/references/troubleshooting.md`.
- Training data, DeepSpeed, LoRA, or hostfile failures: read `sub-skills/fine-tuning/references/troubleshooting.md`.
