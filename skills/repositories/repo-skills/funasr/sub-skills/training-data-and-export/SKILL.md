---
name: training-data-and-export
description: "Prepare FunASR training manifests, distributed training configs,
  export artifacts, and local post-export checks."
metadata:
  disco-role: operating
disable-model-invocation: true
license: NOASSERTION
---

# Training Data and Export

Use this sub-skill when the user asks to prepare FunASR training data, build or validate JSONL manifests, launch a bounded training or fine-tuning run, reason about distributed training overrides, export a model, or run local inference against a trained/exported model.

## Route first

- **Manifest preparation or validation**: read [references/data-formats.md](references/data-formats.md), then use [scripts/make_jsonl_from_scp.py](scripts/make_jsonl_from_scp.py) and [scripts/validate_manifest.py](scripts/validate_manifest.py).
- **Training and fine-tuning command planning**: read [references/workflows.md](references/workflows.md). Do not start a long training run, large model download, or multi-GPU job unless the user explicitly asks for it.
- **Export, ONNX, and local inference after training**: read [references/export-and-onnx.md](references/export-and-onnx.md).
- **Failures and surprising behavior**: read [references/troubleshooting.md](references/troubleshooting.md) before changing data, distributed flags, checkpoints, or package/export assumptions.

## Boundaries

This sub-skill owns:

- `funasr-train`, `funasr-train-ds`, `funasr-export`, and `python -m funasr.bin.inference` command patterns.
- `scp2jsonl`, `jsonl2scp`, and `sensevoice2jsonl` data-format behavior, with safer bundled helpers for tiny fixtures and preflight checks.
- Distributed training precedence among top-level Hydra overrides, nested `train_conf`, DDP, FSDP, and DeepSpeed.
- Checkpoint retention, validated-versus-unvalidated checkpoint ranking, exported-model local inference, ONNX runtime package expectations, and wheel/package-data checks.

Route elsewhere:

- Basic transcription, subtitles, hotwords, and ordinary `AutoModel.generate()` usage: `../python-asr-pipelines/`.
- OpenAI-compatible serving, realtime WebSocket serving, MCP, Docker, runtime SDK, Triton, GGUF, or deployed smoke checks: `../serving-and-runtime/`.
- Fun-ASR-Nano, GLM-ASR, Qwen3-ASR, `AutoModelVLLM`, vLLM, and model-family acceleration caveats: `../llm-asr-and-vllm/`.

## Safe operating defaults

1. Validate manifests before training. Treat duplicate keys, missing `source`/`target`, mismatched key sets, missing local audio, and bad `source_len`/`target_len` as blockers unless the user intentionally accepts them.
2. Prefer CPU/help/static checks while drafting commands. Full training, export with model download, and ONNX runtime smoke can be slow or require optional packages.
3. Put distributed engine choices at top level when they must override a model or template config. Nested `train_conf` values are accepted, but top-level `++use_deepspeed`, `++use_fsdp`, and `++deepspeed_config` take precedence.
4. If a trained local model lacks `configuration.json`, do not guess. Use the explicit config path/name, checkpoint, token list, and CMVN file described in [references/export-and-onnx.md](references/export-and-onnx.md).
