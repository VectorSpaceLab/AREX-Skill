# Post-training, RL, and multimodal troubleshooting

| Symptom | Likely cause | Recovery |
|---|---|---|
| `No module named modelopt` | ModelOpt is optional and absent from minimal env. | Install the supported ModelOpt/Torch variant only for the selected workflow. |
| Quantization/export rejects model | Unsupported architecture, checkpoint format, precision, or missing TE backend. | Confirm ModelOpt support matrix and checkpoint/model args; use a supported container. |
| RL config loads but rollout fails | Reward/environment schema or inference backend mismatch. | Validate config fields and run a tiny rollout/reward call before training. |
| RL metrics become NaN/spiky | Invalid loss mask, empty packed bins, bad logprobs, or unstable reward/ratio. | Check finite tensors, token counts, masks, KL/ratio ranges, and spiky-loss diagnostics. |
| VLM batch shape mismatch | Media feature shape, tokenizer, task encoder, or model provider disagree. | Inspect one batch and verify masks/feature dimensions before distributed training. |
| Media file not found on worker | Host path not mounted/shared across ranks or manifest uses local-only path. | Use shared/container-visible paths and validate from every relevant rank. |
| MIMO grid does not fit world size | Encoder/LLM TP/DP/CP/PP/EP product was copied from another topology. | Recompute the heterogeneous grid and world-size constraints. |
| GPU OOM during calibration/rollout | Large batch, media resolution, sequence length, KV cache, or checkpoint precision. | Reduce batch/resolution/sequence, enable supported recompute/sharding, and profile memory. |
| Missing HF/OpenAI inference backend | Optional dependency or endpoint credential missing. | Install/authorize the chosen backend; do not silently switch to another service. |
| `train_rl.py --help` fails before printing help on `pydantic`, `tensorboard`, `wandb`, or similar | The RL entrypoint imports optional/test-group modules before argparse help. | Install the narrow missing dependency set for parser/config validation, or record a dependency diagnostic; do not treat a CPU help check as RL runtime verification. |
| Checkpoint conversion loses an encoder | Converter does not support the model-specific multimodal key layout. | Route to the model-specific converter and validate state-dict keys before training. |

Keep external tokens, reward endpoints, and private media paths out of logs and generated scripts.
