# Troubleshooting

This reference covers cross-cutting Transformers failures. Use sub-skill troubleshooting files for workflow-specific symptoms.

## Import Errors

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError` for a base dependency such as `regex`, `tokenizers`, `safetensors`, or `huggingface_hub` | Incomplete base install or partial editable install | Reinstall `transformers`, then run `python -m pip check` and a version import check. |
| `AutoModel`, `Trainer`, or model class raises PyTorch missing error | Base install without PyTorch | Install a PyTorch wheel suitable for the host, then verify `import torch` and the model import. |
| Vision processor raises Pillow/torchvision errors | Vision extras missing or incompatible | Install Pillow and a torchvision version compatible with PyTorch; retry a processor import. |
| Tokenizer class needs SentencePiece/tiktoken/mistral-common | Model-specific tokenizer backend missing | Install only the backend named in the error; re-run `AutoTokenizer.from_pretrained(..., local_files_only=True)` when possible. |
| CLI import fails before showing `--help` | CLI module imports optional packages such as `requests` or serving/client helpers | Install the missing package or the serving extra; run `scripts/transformers_skill_preflight.py --check-cli`. |

## Hub, Network, And Credentials

- Use `local_files_only=True` when network access is not allowed.
- Use `revision` to pin Hub assets.
- For private or gated models, authenticate with Hugging Face Hub tooling and pass `token=True` rather than embedding secrets.
- If downloads hang or time out, distinguish network issues from dependency/import issues before changing code.
- Use `trust_remote_code=True` only after reviewing the model repository's custom code.

## Device, Dtype, And Memory

- Do not set both `device` and `device_map` unless the called API explicitly supports that combination.
- Prefer `dtype="auto"` for portable examples; use `float16`/`bfloat16` only after hardware support is known.
- CUDA availability requires a compatible PyTorch wheel, visible GPU, and sufficient driver support.
- MPS/ROCm/vendor accelerators may lack support for some attention, quantization, or compile features.
- For OOM errors, reduce batch size, sequence length, `max_new_tokens`, or switch to quantization/offload only after confirming backend support.

## Workflow Conflicts

- Generation: avoid sampling-only parameters such as `temperature` or `top_p` when `do_sample=False` unless the API explicitly tolerates them.
- Training: align `eval_strategy`, `save_strategy`, and `load_best_model_at_end`; verify label columns and collator output keys.
- Serving: do not combine incompatible optimizations such as compile and continuous batching when the serving docs or preflight reject them.
- Quantization: choose one quantization method and match it to hardware, serialization needs, PEFT compatibility, and serving requirements.
- Contribution: do not edit generated model files when a `modular_<model>.py` source exists; regenerate instead.

## Safe First Commands

```bash
python scripts/transformers_skill_preflight.py --check-imports
python scripts/transformers_skill_preflight.py --check-cli --check-serving
python sub-skills/generation/scripts/generation_config_smoke.py --max-new-tokens 8 --do-sample false
python sub-skills/training/scripts/training_args_smoke.py --output-dir /tmp/transformers-smoke --max-steps 1 --no-write
```

These commands are designed to avoid model downloads, long-running servers, and training side effects unless the caller explicitly opts into them.
