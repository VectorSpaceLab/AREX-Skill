# ColossalAI Installation and Backend Notes

- Distribution/import name: `colossalai`.
- Console script: `colossalai`, with `check` and `run` subcommands.
- Observed version for this skill: `0.5.0`.
- The project is Linux-oriented; Windows is not supported by setup.

## Baseline installation

```bash
pip install colossalai
python -c "import colossalai; print(colossalai.__version__)"
colossalai check -i
```

For source-style inspection or development, install a compatible PyTorch build first, then:

```bash
python -m pip install -r requirements/requirements.txt
python -m pip install -e .
```

Use `BUILD_EXT=1 python -m pip install .` only when you intentionally want ahead-of-time CUDA extension compilation and have compatible PyTorch, CUDA toolkit, compiler, and GPU architecture. Without `BUILD_EXT=1`, ColossalAI can still build some kernels lazily at runtime.

## Backend checks

```bash
python - <<'PY'
import torch
print(torch.__version__, torch.version.cuda)
print(torch.cuda.is_available(), torch.cuda.device_count())
if torch.cuda.is_available():
    print(torch.cuda.get_device_name(0), torch.cuda.get_device_capability(0))
PY
colossalai check -i
```

Primary ColossalAI workflows are CUDA-centric. CPU can validate import, config parsing, and CLI help, but it is only a partial substitute for distributed training, Gemini/ZeRO, ShardFormer, or inference acceleration.

## Optional performance dependencies

Treat these as optional unless the user asks for the exact feature:

- Apex: selected fused normalization paths.
- flash-attn: selected Transformer/LLM attention acceleration paths.
- TensorNVMe: async checkpoint save and NVMe/offload paths.
- vLLM/OpenAI/Pangu/LangChain/Chroma and other application dependencies: app-specific and often incompatible with the core environment.
