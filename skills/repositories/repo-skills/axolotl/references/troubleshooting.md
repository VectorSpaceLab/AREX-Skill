# Axolotl Cross-Cutting Troubleshooting

Use this reference when the symptom spans install/import, optional dependencies, config validation, model/data access, hardware, or workflow routing. For method-specific failures, route to the nearest sub-skill after the first triage.

## First Triage Order

1. Run the root environment checker: `python scripts/check_axolotl_environment.py --json`.
2. If Axolotl is installed, ask the user to run `axolotl --help`, `axolotl agent-docs --list`, or `axolotl config-schema --field <field>` in the same environment.
3. Run the relevant bundled static helper for the task family.
4. Run `axolotl preprocess config.yaml --debug` only when tokenizer/model/data access is available and the user accepts the runtime cost.
5. Run training, vLLM, distributed, model-loading, or merge/inference commands only after config/data/model/backend checks pass.

## Common Symptoms

| Symptom | Likely cause | Next route |
| --- | --- | --- |
| `axolotl: command not found` | Package not installed in active environment or console script directory not on `PATH` | `cli-and-operations` install checks |
| `ModuleNotFoundError` during CLI import | Partial install, dependency conflict, optional backend missing | `cli-and-operations`, then method/model/performance sub-skill named by the missing package |
| YAML parses but Axolotl rejects fields | Wrong field spelling, schema drift, wrong method section, nested config mismatch | `data-and-configs` plus `axolotl config-schema` |
| `preprocess --debug` shows empty labels | Wrong `type`, `field_messages`, role mappings, `roles_to_train`, or chat template | `data-and-configs` |
| SFT/pretraining loss is NaN, zero, or spikes | Data masking, LR, precision, packing, sequence length, OOM, stale prepared data | `sft-and-pretraining` |
| DPO/KTO/ORPO errors mention missing chosen/rejected/label fields | Preference data shape or method mismatch | `preference-tuning` |
| GRPO reward crashes or all rewards are zero | Reward function signature/shape, vLLM mismatch, dataset prompt/completion fields | `rl-and-rewards` |
| Gated model or tokenizer fails | Credentials/network/trust_remote_code/tokenizer/processor settings | `model-loading-and-adapters` |
| Flash Attention, xformers, bitsandbytes, vLLM, torchao, or kernel import fails | Optional dependency and hardware/runtime mismatch | `distributed-and-performance` or `model-loading-and-adapters` depending on the feature |
| NCCL, Ray, DeepSpeed, or FSDP launch fails | Topology/config/env mismatch, missing JSON, unsupported parallel combination | `distributed-and-performance` |

## Optional Dependency Rule

Do not install all Axolotl extras by default. Add extras only for the workflow the user is actually using:

- vLLM serving or GRPO generation: vLLM-related runtime.
- DeepSpeed: DeepSpeed extra and matching torch/CUDA stack.
- Flash Attention or ring attention: compatible GPU, PyTorch, CUDA, and package versions.
- Ray: Ray extra and worker environment parity.
- Quantization or compression: the quantization backend named by the config.

## Static Helpers Are Not Runtime Proof

Bundled scripts in this skill intentionally avoid model downloads, tokenization, GPU kernels, training, vLLM services, and destructive writes. Passing them means the input is structurally plausible, not that Axolotl can train it. Escalate to installed Axolotl checks when runtime facts matter.

## Privacy and Safety

- Do not paste API tokens, Hugging Face tokens, cloud credentials, private paths, or full environment dumps into reusable skill content.
- Ask before launching long training, downloading models/datasets, starting vLLM services, mutating environments, or running distributed jobs.
- Prefer small local fixtures and static checks before expensive native commands.
