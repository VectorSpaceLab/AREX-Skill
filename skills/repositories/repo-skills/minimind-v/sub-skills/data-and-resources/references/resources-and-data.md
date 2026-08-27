# MiniMind-V Resources and Data

## Purpose

Use this reference to prepare MiniMind-V resources without reopening source docs. It covers dependency subsets, resource layout, parquet schema, image placeholder behavior, and safe validation.

## Dependency subset

- Data/parquet: `datasets`, `pyarrow`, `Pillow`, `numpy`.
- Model/tokenizer: `transformers`, tokenizer files under `model/`, and backend-matched `torch`.
- Web and logging packages are optional unless the selected workflow needs WebUI or experiment logging.
- `torch`/`torchvision` are commented in requirements; install backend-specific wheels separately.

## Expected resource layout

```text
model/
  siglip2-base-p32-256-ve/
    config.json
    model.safetensors
    preprocessor_config.json
  tokenizer.json
  tokenizer_config.json
out/
  llm_768.pth
  pretrain_vlm_768.pth
  sft_vlm_768.pth
  *_moe.pth
dataset/
  pretrain_i2t.parquet
  sft_i2t.parquet
  eval_images/
```

Resource roles:

- `model/tokenizer.json` and `model/tokenizer_config.json`: MiniMind tokenizer assets; tokenizer config contains `<|image_pad|>` and chat-template behavior.
- `model/siglip2-base-p32-256-ve/`: frozen SigLIP2 vision encoder used by VLM inference, training, WebUI, and conversion initialization.
- `out/*.pth`: native PyTorch weights. `_moe` suffix corresponds to MoE variants.
- `dataset/*.parquet`: ALLaVA-style training rows.

Do not bundle or automatically fetch SigLIP2, `.pth` weights, or parquet datasets. Ask before any download and name the target relative path.

## Parquet schema

The VLM dataset loader expects each sampled row to include:

| Column | Required | Accepted shape | Meaning |
| --- | --- | --- | --- |
| `conversations` | yes | JSON string or decoded list | Chat turns used with the tokenizer chat template. |
| `image_bytes` | yes | one bytes object or list of bytes objects | Encoded image data opened with Pillow and converted to SigLIP2 tensors. |

Each conversation item should be an object with non-empty `role` and string `content`. Rows with multiple images can use a list in `image_bytes`.

## Image placeholder semantics

MiniMind-V conversation text uses literal `<image>` placeholders. During prompt construction, non-system turn content replaces each `<image>` with `image_special_token * image_token_len`. Defaults:

```text
image_special_token = <|image_pad|>
image_token_len = 64
image_ids = [12]
```

The 64 visual tokens match the SigLIP2 P32 256x256 output grid. The static validator checks row structure and image bytes; it does not enforce semantic alignment between placeholder count and image count.

## Validation workflow

1. Check that resource directories/files exist for the requested workflow.
2. Validate a parquet file before training:

```bash
python path/to/validate_vlm_parquet.py dataset/sft_i2t.parquet --max-rows 100
```

3. Interpret output:
   - `PASS`: required columns exist and sampled rows satisfy conversation/image-byte shape checks.
   - `FAIL`: missing columns, invalid JSON/list structure, missing role/content, missing image data, non-bytes payloads, or Pillow decode failures.
   - Decode is skipped if Pillow is unavailable.

The validator is read-only and never downloads, trains, serves, or loads model weights.
