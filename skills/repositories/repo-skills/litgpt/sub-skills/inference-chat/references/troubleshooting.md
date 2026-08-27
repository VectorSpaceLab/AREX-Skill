# LitGPT Inference Troubleshooting

Use this when `litgpt generate`, `litgpt chat`, specialized generation commands, or `LLM` API calls fail before or during local generation.

## Preflight Command

Run this before loading large weights:

```bash
python sub-skills/inference-chat/scripts/check_inference_inputs.py \
  --checkpoint-dir CHECKPOINT_DIR \
  --prompt "Hello" \
  --max-new-tokens 50 \
  --top-k 50 \
  --top-p 1.0 \
  --temperature 0.8
```

Add `--require-cuda` for CUDA-only routes such as sequential, tensor-parallel, or bitsandbytes quantization.

## Failure Matrix

| Symptom | Likely Cause | Fix |
| --- | --- | --- |
| Missing `checkpoint_dir` or path is not a directory | User passed a model name, typo, or unprepared checkpoint | For offline generation, use a local path. For download/conversion/validation, route to `../../checkpoint-conversion/`. |
| Missing `lit_model.pth` | Checkpoint is HF-format, partial, adapter-only, or unmerged LoRA | Route to `../../checkpoint-conversion/` for validation, conversion, or merge. `chat` can auto-merge a raw LoRA file in one narrow case, but planned workflows should merge explicitly. |
| Missing `model_config.yaml` | Directory is not LitGPT-formatted | Route to `../../checkpoint-conversion/` to convert or validate layout. |
| Missing tokenizer files | Tokenizer was not downloaded/copied or `tokenizer_dir` is wrong | Put compatible tokenizer files next to the checkpoint or provide explicit `tokenizer_dir` in Python. |
| `top_p must be in [0, 1]` | Invalid sampling value | Set `top_p` between `0` and `1`; use `0` for greedy or `1` for full distribution. |
| Output should be deterministic but varies | Sampling still enabled | Use `top_k=1`, `temperature=0`, or `top_p=0`. |
| Output is repetitive or low quality | Prompt style mismatch, overly greedy sampling, or base model used for chat | Fix prompt style/tokenizer first; then tune `temperature`, `top_k`, and `top_p`. Use chat/instruct checkpoints for chat behavior. |
| `Quantization and mixed precision is not supported` | `--quantize bnb.*` with a mixed precision string | Use true precision such as `bf16-true`, `16-true`, or `32-true`, or remove quantization. |
| `No module named bitsandbytes` or bitsandbytes plugin errors | Optional bitsandbytes dependency missing or incompatible | Install compatible bitsandbytes in a CUDA/Linux environment or remove `--quantize`. |
| CPU-only machine with sequential/TP request | Multi-device generation routes require CUDA/GPU | Use ordinary `generate`/API CPU inference for small checkpoints or move to CUDA hardware. |
| `generate_strategy='sequential'|'tensor_parallel' is only supported for accelerator='cuda'|'gpu'` | API `.distribute(...)` was called with CPU/MPS | Change accelerator to CUDA/GPU and verify devices, or use single-device CPU/MPS generation. |
| `You selected more devices ... than available` | `devices` exceeds visible CUDA devices | Reduce `devices` or adjust `CUDA_VISIBLE_DEVICES`. |
| TP divisibility errors | Tensor-parallel world size does not evenly divide model dimensions | Use a different number of devices or use sequential generation. |
| Adapter command cannot find `adapter_path` | Training output path differs from defaults | Provide explicit `--adapter_path` or route to `../../training-data/` to identify output artifacts. |
| `generate_adapter` used for LoRA output | Adapter and LoRA checkpoint formats differ | Route to `../../checkpoint-conversion/` for LoRA merge/checkpoint handling. |
| Python API tries to download | `LLM.load("org/model", init="pretrained")` receives a non-local identifier | Use an existing local checkpoint path for offline workflows, or explicitly confirm download intent. |
| `The model is not initialized yet` | `LLM.load(..., distribute=None)` followed by `.generate(...)` | Call `.distribute(...)` or `.trainer_setup()` before `.generate(...)`. |
| Random init cannot distribute | `init="random"` with unsupported `.distribute(generate_strategy=...)` path | Use pretrained checkpoint weights for multi-device inference; random init is for tests/scaffolds. |

## Checkpoint Layout Basics

A typical ready LitGPT inference checkpoint includes:

- `lit_model.pth`
- `model_config.yaml`
- At least one tokenizer file, such as `tokenizer.json`, `tokenizer.model`, `tokenizer_config.json`, `tokenizer.yaml`, or `vocab.json` plus `merges.txt`
- Optional `prompt_style.json` or compatible prompt-style metadata saved with the checkpoint

If these files are missing or inconsistent, do not try to repair generation flags. Route to `../../checkpoint-conversion/`.

## Prompt Style And Tokenizer Problems

LitGPT applies prompts through a `PromptStyle` implementation. In generation and chat routes it loads a saved prompt style from the checkpoint if present; otherwise it derives the style from the checkpoint config.

Triage:

1. Confirm tokenizer files belong to the same model family as the checkpoint weights.
2. Check whether a saved prompt style file should be present for a fine-tuned or chat model.
3. If no saved style exists, rely on `PromptStyle.from_config` only for model families LitGPT supports.
4. Use simple deterministic generation (`top_k=1`, low `max_new_tokens`) to distinguish template mismatch from sampling noise.
5. Do not force Alpaca/Llama/chat markers manually unless the checkpoint was trained for that template.

## Sampling Parameter Rules

- `top_p` must be `0 <= top_p <= 1`.
- `top_p=0` is greedy regardless of temperature.
- `temperature=0` is greedy regardless of `top_p`.
- `top_k=None` disables top-k filtering.
- `top_k=1` restricts the next token to the most likely token before other filters.
- Higher `temperature` increases randomness; use conservative values for factual or diagnostic prompts.

## Quantization And Hardware Rules

- Bitsandbytes inference quantization uses `bnb.nf4`, `bnb.nf4-dq`, `bnb.fp4`, `bnb.fp4-dq`, or `bnb.int8` where supported.
- Bitsandbytes is an optional dependency and is intended for CUDA/Linux-compatible environments.
- Do not combine `bnb.*` quantization with mixed precision.
- If the GPU lacks bf16 support, try `16-true`; if CUDA is absent, remove quantization and use CPU for only very small checkpoints.
- Sequential and tensor-parallel generation are CUDA/GPU-only routes. The ordinary `generate` and API paths can run CPU for small models but may be slow and memory-heavy.

## LoRA, Adapter, And Full-Finetune Route Mismatches

- `generate_full` expects a base checkpoint directory plus a full finetuned model file via `--finetuned_path`.
- `generate_adapter` expects a base checkpoint directory plus `.pth.adapter` weights.
- `generate_adapter_v2` expects a base checkpoint directory plus `.pth.adapter_v2` weights.
- LoRA outputs are not adapter outputs. Merge LoRA or use checkpoint handling in `../../checkpoint-conversion/` before ordinary generation.
- If a user only knows the training output directory, route to `../../training-data/` to identify what training workflow produced.

## Avoiding Accidental Downloads

`LLM.load(model, init="pretrained")` and some CLI routes can treat a non-local string as a model identifier. For no-network requirements:

1. Resolve `model` or `checkpoint_dir` to an existing local directory before calling LitGPT.
2. Run the bundled checker on that directory.
3. In Python, guard with `Path(model).is_dir()` and raise a local error before `LLM.load`.
4. Use `tokenizer_dir` only with explicit local tokenizer paths.
5. Route any requested download, conversion, or validation to `../../checkpoint-conversion/`.
