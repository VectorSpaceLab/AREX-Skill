# MOSS CLI and command catalog

## Bundled PyTorch generation template

Use the bundled `scripts/run_moss_generation.py` instead of relying on the
original checkout's interactive demo. It is self-contained and dry-runs by
default.

| Flag | Values/default | Notes |
| --- | --- | --- |
| `--query` | required | User message to wrap in the MOSS prompt. |
| `--model-name` | default `OpenMOSS-Team/moss-moon-003-sft-int4`; choices `moss-moon-003-sft`, `moss-moon-003-sft-int8`, `moss-moon-003-sft-int4` | Hugging Face id or complete local directory. |
| `--device` | `cuda` or `cpu`; default `cuda` | CPU is useful for planning, not a realistic 16B generation smoke. |
| `--gpu` | default `0` | Comma-separated CUDA device ids used when executing on CUDA. |
| `--max-new-tokens` | default `128` | New tokens to generate in the optional execution path. |
| `--top-p`, `--temperature`, `--repetition-penalty` | `0.8`, `0.7`, `1.02` | Sampling controls. |
| `--execute` | off by default | Actually loads the checkpoint and runs generation. Heavy. |

Behavior:

- Dry-run mode prints the prompt and plan without importing Transformers.
- Execute mode loads tokenizer/model with `trust_remote_code=True` and uses EOS
  token id 106068.
- Quantized INT4/INT8 with multiple GPUs is rejected before execution.

Safe validation:

```bash
python sub-skills/inference/scripts/inspect_cli_flags.py --runner pytorch --model-name OpenMOSS-Team/moss-moon-003-sft --gpu 0,1 --json
python sub-skills/inference/scripts/run_moss_generation.py --query "Hello MOSS" --json
```

## Programmatic wrapper facts

The original source evidence exposed an `Inference` class with `model`,
`model_dir`, `parallelism`, and `device_map` constructor parameters. The bundled
runtime skill does not require that original wrapper to exist; use
`scripts/run_moss_generation.py` for a self-contained execution template, or
write downstream code around `AutoTokenizer` and `AutoModelForCausalLM` with
`trust_remote_code=True`.

## Optional Jittor backend notes

MOSS source evidence included a Jittor implementation with these concepts:

| Concept | Values/default | Notes |
| --- | --- | --- |
| model id | `OpenMOSS-Team/moss-moon-003-sft`; also INT4/INT8 choices | Requires Hugging Face checkpoint files. |
| generation method | `sample` or `greedy` | Sampling supports temperature/top-p/top-k. |
| `temperature`, `top_p`, `top_k`, `max_len` | `0.7`, `0.8`, `40`, `2048` | Optional Jittor generation controls. |
| GPU flag | boolean | Enables Jittor CUDA instead of CPU. |

Safe validation:

```bash
python sub-skills/inference/scripts/inspect_cli_flags.py --runner jittor --model-name OpenMOSS-Team/moss-moon-003-sft --generate sample --jittor-gpu --json
```

This only documents optional-backend choices. It does not import Jittor or
download checkpoints. Use the bundled PyTorch template unless the target task
explicitly provides and verifies a Jittor runtime.

## Common command-selection rules

- Single 3090-class GPU with memory pressure: choose INT4 or INT8, one GPU.
- Two or more GPUs for FP16: choose `OpenMOSS-Team/moss-moon-003-sft`, not a
  quantized checkpoint.
- CPU-only quick development: use prompt/flag helpers and class import checks;
  full generation is not a reliable CPU smoke for a 16B model.
- Service/API task: prepare the same model/gpu choice here, then use the
  serving sub-skill for request payloads and ports.
