# Megatron-LM capability map

| Signal in the task | Owner | First reference |
|---|---|---|
| `pip install megatron-core`, `uv`, Python/Torch/CUDA, NGC, TE/Apex/ModelOpt/Mamba, import failure | `install-and-environment` | `sub-skills/install-and-environment/references/install-reference.md` |
| `TransformerConfig`, `GPTModel`, `HybridModel`, layer spec, process groups, TP/PP/CP/EP/DP/FSDP, MoE | `core-models-and-parallelism` | `sub-skills/core-models-and-parallelism/references/api-reference.md` and `parallelism-reference.md` |
| `pretrain_gpt.py`, `torchrun`, SLURM, JSONL, tokenizer, `.bin/.idx`, dataset cache, mock data | `training-cli-and-data` | `sub-skills/training-cli-and-data/references/training-workflows.md` and `data-workflows.md` |
| `torch_dist`, `fsdp_dtensor`, safe globals, optimizer resharding, GPT-Hybrid conversion, HF/Megatron | `checkpointing-and-conversion` | `sub-skills/checkpointing-and-conversion/references/checkpoint-reference.md` |
| offline generation, dynamic inference, `MegatronLLM`, `MegatronAsyncLLM`, coordinator, HTTP/OpenAI-compatible server | `inference-and-serving` | `sub-skills/inference-and-serving/references/inference-workflows.md` |
| ModelOpt quantization/pruning/distillation, GRPO/RL, reward environment, VLM/audio/video/MIMO | `post-training-rl-and-multimodal` | matching post-training/RL/multimodal reference |
| pytest, functional recipes, `mr-github`, golden values, CI logs, base image, `uv.lock`, PR/issue/nightly sync | `testing-ci-and-maintenance` | matching testing/CI/contribution reference |

## Multi-skill routes

- **Train from a distributed checkpoint:** install → core topology → training launch → checkpoint semantics.
- **Serve a trained model:** install → checkpoint validation → core topology → inference/server.
- **Scale a data-heavy run:** install → core topology → training/data cache → checkpoint/logging.
- **Base-image bump with golden drift:** testing/CI → install/container → testing/goldens; do not touch LTS unless requested.
- **RL/VLM post-training from an HF model:** install optional deps → checkpoint/conversion → core topology → post-training/RL/multimodal → inference/evaluation.
