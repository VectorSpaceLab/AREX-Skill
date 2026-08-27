# Troubleshooting

Use this guide when model creation, tokenization, preprocessing, or embedding inference fails.

## Unknown Model Architecture

Symptoms:

- `RuntimeError: Model config for '...' not found in built-ins`
- A user passes a Hugging Face repo id without the `hf-hub:` prefix.
- A local export directory is passed without the `local-dir:` prefix.

Fixes:

1. Check `open_clip.list_models()` for built-in names.
2. Use `hf-hub:org/repo` for an OpenCLIP-compatible Hugging Face repository.
3. Use `local-dir:relative/or/absolute/dir` for a directory containing `open_clip_config.json`.
4. For checkpoint files, keep `model_name` as a built-in architecture and pass the file path as `pretrained`.

## Wrong or Missing Pretrained Tag

Symptoms:

- `RuntimeError: Pretrained value '...' is not a known tag or valid file path`.
- Loading succeeds with `pretrained=None`, but semantic results are random.

Fixes:

```python
import open_clip
print(open_clip.list_pretrained_tags_by_model("ViT-B-32"))
print(open_clip.list_pretrained(as_str=True)[:20])
```

Use a tag listed for that exact architecture. If the value is a file path, confirm the file exists and matches the architecture.

## QuickGELU Mismatch and Weak Results

Symptoms:

- Warning about `QuickGELU mismatch`.
- Embeddings have valid shapes, but zero-shot/retrieval quality is much worse than expected.
- A local checkpoint from an older/OpenAI-compatible model is loaded into a non-QuickGELU architecture.

Fixes:

1. Check whether a `-quickgelu` model variant exists for the same architecture.
2. Prefer that variant for QuickGELU-trained checkpoints.
3. If no variant exists, try `force_quick_gelu=True` with the same checkpoint.
4. Re-run with `model.eval()`, normalized features, and correct preprocessing before judging quality.

## Model Left in Train Mode

Symptoms:

- Non-reproducible embeddings.
- BatchNorm/stochastic-depth behavior changes across calls.
- README-like inference code gives unstable scores.

Fix:

```python
model.eval()
with torch.no_grad():
    image_features = model.encode_image(image, normalize=True)
```

OpenCLIP models are created in train mode. Inference code should call `model.eval()` explicitly.

## Optional Dependency Missing

### `timm`

Symptoms:

- Unknown timm image encoder.
- Errors while creating ConvNeXt, EVA, SigLIP, or timm-backed vision towers.
- NaFlex transform factory import failures.

Fix: install a compatible `timm` version for the chosen model family, or choose a model that does not use a timm vision tower.

### `transformers`

Symptoms:

- HF text tower creation fails.
- CoCa `generate(...)` raises `Please install transformers for generate functionality`.
- HF tokenizer/model config errors.

Fix: install `transformers` when using HF text towers, some Hub models, or CoCa generation.

### `tokenizers` or `sentencepiece`

Symptoms:

- HF tokenizer construction fails for specific text towers.
- Multilingual XLM/Roberta/MT5 tokenizers fail to load.

Fix: install the tokenizer backend required by the named HF tokenizer.

### `tiktoken`

Symptoms:

- Modern text model config has `tokenizer_type: "tiktoken"` and tokenizer creation fails.

Fix: install `tiktoken` or choose a model with a tokenizer available in the environment.

### `huggingface_hub`

Symptoms:

- `Hugging Face hub model specified but package not installed`.
- `hf-hub:` model creation fails before config download.

Fix: install `huggingface_hub`, or use `local-dir:`/local checkpoint files instead.

### `safetensors`

Symptoms:

- A `.safetensors` checkpoint cannot load.

Fix: install `safetensors`, or provide a supported PyTorch checkpoint file.

## Hugging Face Cache or Network Failure

Symptoms:

- `Failed initial config/weights load from HF Hub ...`.
- `Failed to download file ...`.
- Offline environment blocks `hf-hub:` loading.

Fixes:

1. Confirm network access is allowed.
2. Pass `cache_dir` consistently to `create_model...` and `get_tokenizer`.
3. If network is forbidden, prepare a local export directory with `open_clip_config.json`, weights, and tokenizer files, then use `local-dir:`.
4. Remember `pretrained=` is ignored for `hf-hub:`; do not try to override missing Hub weights with that argument.

## Local Directory Config Failure

Symptoms:

- `Directory specified via 'local-dir:' schema not found`.
- `'local-dir:' specified, but config file missing`.
- `Local config ... missing 'model_cfg'`.
- Tokenizer fails for a local-dir model.

Fixes:

Expected config:

```json
{
  "model_cfg": {
    "embed_dim": 512,
    "vision_cfg": {"image_size": 224},
    "text_cfg": {"context_length": 77, "vocab_size": 49408}
  },
  "preprocess_cfg": {
    "size": 224,
    "mean": [0.48145466, 0.4578275, 0.40821073],
    "std": [0.26862954, 0.26130258, 0.27577711]
  }
}
```

Checklist:

- The directory exists and the prefix is exactly `local-dir:`.
- `open_clip_config.json` is valid JSON with top-level `model_cfg`.
- A supported checkpoint file is colocated if weights should load.
- HF tokenizer files are present in the same directory when the config uses an HF tokenizer.
- Use `load_weights=False` to separate config/tokenizer problems from checkpoint problems.

## Context Length, Padding, or EOS Validation Failure

Symptoms:

- `ValueError` mentioning `eos_id`, `pad_id`, `pad_token_id`, `pool_type`, or variable-length text.
- Text tensor shape differs from model context length.
- Modern text or HF-tokenizer model fails during `get_tokenizer`.

Fixes:

1. Use `tokenizer = open_clip.get_tokenizer(model_name, context_length=...)`, not `open_clip.tokenize`, for model-specific tokenizers.
2. If `force_context_length=N` was used for the model, pass `context_length=N` to `get_tokenizer`.
3. Ensure `open_clip_config.json` text config special token ids match tokenizer metadata.
4. For variable text configs, use the model's intended tokenizer/collator path instead of forcing legacy simple tokenization.

## CPU/CUDA Precision Misuse

Symptoms:

- fp16 operations fail on CPU.
- CUDA autocast code crashes on a CPU-only machine.
- Inputs and model are on different devices.

Fixes:

```python
device = "cuda" if torch.cuda.is_available() else "cpu"
precision = "fp16" if device == "cuda" else "fp32"
model, _, preprocess = open_clip.create_model_and_transforms(
    "ViT-B-32",
    pretrained=None,
    load_weights=False,
    device=device,
    precision=precision,
)
image = image.to(device)
text = text.to(device)
```

Only use `torch.autocast("cuda")` when `device` is CUDA. Keep CPU smoke tests in fp32.

## Preprocess Mismatch

Symptoms:

- Model loads and embeddings are finite, but scores are unexpectedly weak.
- A checkpoint family has non-default mean/std.
- Manual transforms are used instead of model-derived transforms.

Fixes:

1. Prefer `create_model_and_transforms` and use its validation transform.
2. Inspect `open_clip.get_model_preprocess_cfg(model)`.
3. Avoid hardcoding OpenAI mean/std for all pretrained tags.
4. If overriding image size, verify the model supports the new resolution and any positional embeddings are handled.

## Output Unpacking Error

Symptoms:

- `ValueError: too many values to unpack` or `TypeError` when handling model output.
- Code assumes all models return CLIP tuples.

Fixes:

- For embeddings, prefer `model.encode_image(...)` and `model.encode_text(...)`.
- For CLIP/CustomTextCLIP tuple output: expect `(image_features, text_features, logit_scale)` plus optional `logit_bias`.
- For named fields, pass `output_dict=True` when creating CLIP/CustomTextCLIP models.
- For CoCa, expect dict output from `forward`.

## CoCa Generation Failure

Symptoms:

- `model.generate(...)` raises a `transformers` installation error.
- Generation returns unexpected sequence lengths.
- Code expects training label shift inside `forward`.

Fixes:

1. Install `transformers` for generation.
2. Pass explicit generation config/token ids when defaults do not match the tokenizer.
3. Remember `seq_len` and `min_seq_len` are total sequence lengths including prompt tokens.
4. Keep label shifting in training/evaluation code; CoCa `forward` no longer performs training label slicing.

## Local Checkpoint Shape Mismatch

Symptoms:

- `load_state_dict` strict errors.
- Positional embedding or projection shape mismatches.
- Local file loads into the wrong architecture.

Fixes:

1. Confirm architecture name, image size, text context length, and vocab/tokenizer match the checkpoint.
2. Try the matching `-quickgelu` variant if applicable.
3. Use `local-dir:` with a faithful `open_clip_config.json` if available.
4. For tower-only weights, use `pretrained_image_path` or `pretrained_text_path` and expect partial-load warnings rather than strict full-model loading.

## Random-Init Results Misinterpreted

Symptoms:

- Smoke script passes but scores are meaningless.
- User expects `pretrained=None` to classify images.

Fix:

`pretrained=None` or `load_weights=False` creates an untrained/random-weight model unless tower defaults are separately enabled. Use this only for API and shape validation. For semantic inference, select a known pretrained tag, `hf-hub:` model, `local-dir:` export, or compatible local checkpoint file.
