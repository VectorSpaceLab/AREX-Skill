# UI-S1 Troubleshooting

| Symptom | Likely cause | Recovery |
|---|---|---|
| JSONL validator reports missing `steps` or `action_content` | Incomplete trajectory rows | Repair rows before training/eval; optionally normalize `check_options` from `action_content`. |
| Evaluator cannot parse model response | Missing `<action>` tag or invalid action JSON | Prompt/serve model with UI-S1 tagged response format; inspect raw response. |
| Ray startup fails | Port conflict or distributed env mismatch | Set `MASTER_ADDR`, `MASTER_PORT`, `WORLD_SIZE`, `RANK`; stop stale Ray processes privately. |
| vLLM errors on model length/images | Model length, image limit, or memory utilization too high | Reduce `actor_rollout_ref.rollout.max_model_len`, `limit_images`, `n`, or GPU memory utilization. |
| Flash-attn import/build fails | Wheel/PyTorch/CUDA mismatch | Install a version matching the prepared CUDA/PyTorch stack; do not compile blindly on a laptop. |
| OOM at startup | Batch/rollout settings sized for 8 GPUs | Lower batch sizes, rollout `n`, max lengths, tensor parallel assumptions, and maybe model size. |
| Checkpoint merge cannot find shards | Wrong backend/layout or local_dir | Match `--backend` to the checkpoint format and inspect checkpoint contents before merge. |
| Upload fails or leaks | Missing Hugging Face token or accidental public upload | Avoid `--hf_upload_path` unless explicit upload approval and private token are configured. |

CPU-only validation cannot clear live UI-S1 training/eval verification. Record GPU/model/data gaps explicitly.
