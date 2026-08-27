# LLM Fine-Tuning Troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `transformers`, `peft`, `datasets`, `vllm`, or `deepspeed` missing | `[llm]` extra not installed | Install `agilerl[llm]` in a suitable environment or choose a dry-run path. |
| vLLM import or engine init fails | Unsupported Python/CUDA/GPU/model or missing compiled wheels | Check vLLM compatibility and use CPU/Transformers dry-run for config validation. |
| DeepSpeed build/import fails | Compiler/CUDA/PyTorch ABI mismatch | Use a supported Python/Torch/CUDA combo or disable DeepSpeed for smoke checks. |
| CUDA OOM during rollout/training | Model, batch size, sequence length, or colocated rollout memory too large | Reduce batch/generation sizes, use quantization if supported, or separate rollout/training resources. |
| Chat template errors | Tokenizer lacks expected template or message schema is wrong | Inspect tokenizer chat template and run one prompt through preprocessing. |
| Reward is always zero/invalid | Reward function expects different answer format or environment state | Test reward function with known good/bad completions. |
| Preference columns missing | Dataset schema does not match DPO/preference trainer | Rename/map columns and validate one batch before training. |
| W&B login or duplicate logs | Logging enabled in multi-process run | Disable W&B for smoke checks or log only from main process. |

## Debug Checklist

1. Run optional dependency probe.
2. Confirm model/tokenizer can load in the chosen backend.
3. Validate one dataset batch and chat template.
4. Validate reward/preference fields.
5. Validate checkpoint path and logging configuration.
6. Start with a tiny max-step dry run before full training.
