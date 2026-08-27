# OpenRLHF Troubleshooting Router

Use this reference for cross-cutting issues before diving into workflow-specific troubleshooting.

## Install and Import

| Symptom | Likely cause | Route |
| --- | --- | --- |
| `import openrlhf` works but training imports fail | Top-level package import is lighter than the full ML runtime dependency stack | Read `sub-skills/operations-and-utilities/references/installation-and-runtime.md` |
| `flash-attn` fails while installing | Torch/CUDA build order, missing matching wheel, missing compiler/toolkit, or unsupported Python/CUDA combination | Read `sub-skills/operations-and-utilities/references/troubleshooting.md` |
| DeepSpeed, Ray, vLLM, or CUDA imports fail | Optional/runtime dependencies are missing or incompatible with the host | Use `sub-skills/operations-and-utilities/scripts/check_openrlhf_runtime.py` |
| HuggingFace model load fails | Network/auth/cache/model-id issue, not an OpenRLHF command-shape issue | Verify model access before changing OpenRLHF flags |

## Data and Config

| Symptom | Likely cause | Route |
| --- | --- | --- |
| Missing `input`, `output`, `prompt`, `chosen`, or `rejected` keys | CLI key flags do not match dataset records | Use `sub-skills/data-preparation/` |
| Chat-template output looks duplicated or malformed | Mixing `--data.apply_chat_template` with a plain `--data.input_template` workflow | Read `sub-skills/data-preparation/references/data-formats.md` |
| Multimodal run fails on images or media tokens | Image key, placeholder count, or VLM prompt processing mismatch | Read `sub-skills/data-preparation/references/troubleshooting.md` and `sub-skills/rl-agent-training/references/troubleshooting.md` |
| Training truncates too aggressively | `--data.max_len`, packing, tokenizer, or prompt template assumptions are wrong | Validate a tiny sample before launching training |

## Training and Runtime

| Symptom | Likely cause | Route |
| --- | --- | --- |
| SFT/RM/DPO command has wrong keys or flags | Dataset mode and training CLI are mixed | Use `data-preparation` first, then `supervised-preference-training` |
| PPO/RL command confuses algorithm options | Advantage estimator, sample count, partial rollout, or reward source mismatch | Use `sub-skills/rl-agent-training/references/cli-reference.md` |
| Ray ignores or overrides expected env vars | Runtime env defaults versus user-provided environment variables | Use `operations-and-utilities`; repository tests cover preservation of `NCCL_DEBUG`, `TOKENIZERS_PARALLELISM`, and `RAY_ENABLE_ZERO_COPY_TORCH_TENSORS` |
| OOM or stalled training | Batch sizes, vLLM engine count, tensor parallelism, ZeRO stage, packing, or colocated actors are too aggressive | Start with the relevant training sub-skill, then route to operations for runtime diagnostics |

## Safety Guidance

Do not run full OpenRLHF examples as default verification. Most training scripts require GPUs, model downloads, datasets, Ray/vLLM services, distributed process launchers, or long runtimes. Prefer command generation, tiny data validation, helper script `--help`, and source-backed review unless the user explicitly asks to execute a full workflow.
