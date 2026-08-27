# Installation and Extras

## Base Install

Use the base package when the task is ordinary trainer/API/CLI inspection or simple training setup:

```bash
pip install trl
python - <<'PY'
import trl
from trl import SFTTrainer, DPOTrainer, GRPOTrainer, RewardTrainer
print('trl import ok')
PY
```

For repository development, use an editable install:

```bash
pip install -e .
trl --help
trl env
```

TRL requires Python `>=3.10` and depends on `accelerate`, `datasets`, `jinja2`, `packaging`, and `transformers`. Base installs do not include every backend, service integration, or development tool.

## Optional Extras

Install extras only for workflows that actually need them:

| Extra | Use when | Common reason not to install |
| --- | --- | --- |
| `peft` | LoRA/QLoRA/adapters through `peft_config` or CLI `--use_peft` | Not needed for full-model training or read-only inspection |
| `vllm` | GRPO/RLOO vLLM generation or `trl vllm-serve` runtime | Large GPU/service dependency; help can work without serving |
| `deepspeed` | DeepSpeed ZeRO training | Heavy compiled/runtime stack; skip unless distributed training requires it |
| `kernels` | Transformers kernels/hub-kernels acceleration | Optional performance path, version-sensitive |
| `liger` | Liger Kernel training flags | Optional performance path |
| `quantization` | bitsandbytes 4-bit/8-bit loading | Hardware and wheel sensitive |
| `vlm` | Vision-language model examples and multimodal processing dependencies | Not required for text-only training |
| `math_verify` | Math answer verification rewards | Only needed for math-verification reward workflows |
| `openreward` | `trl.experimental.openreward` integrations | Requires OpenReward SDK and often credentials or services |
| `harbor` | `trl.experimental.harbor` integrations | Requires Python/version/backend support plus sandbox dependencies |
| `quality`, `test`, `dev` | contributor checks and full test/dev workflow | Broad and unnecessary for runtime use |

## Environment Checks

- Run `trl env` for a package/system summary.
- Run `trl --help` and the relevant subcommand `--help` before constructing commands.
- Use `scripts/check_trl_environment.py` for a self-contained diagnostic that can check importability, metadata, CLI help, and optional extras.
- Treat GPU availability and optional package importability as separate facts: base TRL can import on CPU even when vLLM, DeepSpeed, bitsandbytes, or CUDA are unavailable.

## Inspection Baseline Used for This Skill

This skill was generated from a verified base editable install of TRL `1.7.0.dev0`. The inspection environment used CPU Torch to avoid unnecessary CUDA downloads. Optional extras were intentionally not installed; workflow-specific references describe when to add them.
