# MOSS cross-cutting troubleshooting

## Start with the route

- Model class import, checkpoint family, quantization, CUDA, or Triton issue:
  [../sub-skills/model-runtime/references/troubleshooting.md](../sub-skills/model-runtime/references/troubleshooting.md).
- Prompt markers, chat generation, model/GPU selection, Jittor, or stop-token
  issue: [../sub-skills/inference/references/troubleshooting.md](../sub-skills/inference/references/troubleshooting.md).
- FastAPI, Gradio, Streamlit, request schema, port, or session-history issue:
  [../sub-skills/serving/references/troubleshooting.md](../sub-skills/serving/references/troubleshooting.md).
- SFT JSON/JSONL, plugin transcript, DeepSpeed, or training-data issue:
  [../sub-skills/fine-tuning-data/references/troubleshooting.md](../sub-skills/fine-tuning-data/references/troubleshooting.md).

## Quick diagnosis table

| Symptom | Likely cause | First action |
| --- | --- | --- |
| `ModuleNotFoundError: models` | Local MOSS source root is not importable. | Run `scripts/check_moss_env.py --repo-root /path/to/MOSS --json`. |
| `trust_remote_code` or custom class loading failure | Hugging Face Auto* load did not allow MOSS remote code or checkpoint files are incomplete. | Use `trust_remote_code=True` and verify tokenizer/config/model files. |
| CUDA unavailable or tensor allocation fails | CPU-only PyTorch, driver/runtime mismatch, hidden devices, or busy GPUs. | Run `scripts/check_moss_env.py --require-cuda`; inspect host GPU state. |
| OOM on model load or generation | Checkpoint precision/context too large for available memory. | Use the model overview memory table; reduce history/length; choose INT4 single GPU or FP16 model parallelism. |
| Quantized model rejects multiple GPUs | INT4/INT8 MOSS demos are single-GPU only. | Use one GPU or switch to FP16 `moss-moon-003-sft`. |
| Prompt echoes markers or fails to stop | Incorrect MOSS turn markers or EOS handling. | Use the prompt-format reference and `build_moss_prompt.py`. |
| API keeps wrong history | Reused or omitted `uid` unexpectedly. | Preserve returned `uid` for continuation; generate a new `uid` for a fresh chat. |
| SFT loader KeyError or bad samples | Conversation JSON/JSONL missing fields or markers. | Run `validate_sft_json.py` before tokenization. |
| DeepSpeed launch fails | Missing DeepSpeed, wrong process count, NCCL/port, or GPU memory mismatch. | Use `plan_finetune_command.py`; adjust config and install training deps intentionally. |

## Heavy actions are not smoke tests

Do not use the following as routine checks:

- full MOSS checkpoint generation;
- public network checkpoint download;
- API/UI service launch;
- multi-GPU SFT training;
- Jittor checkpoint conversion.

Use bundled dry-run helpers first. Escalate to heavy execution only when the
user's task requires it and checkpoint/network/GPU/write side effects are clear.

## License and exposure issues

MOSS separates code, model, and data licenses. Before public serving,
redistribution, commercial data use, or external API exposure, check the
specific artifact's license and user agreement. This skill provides operating
guidance, not legal approval.
