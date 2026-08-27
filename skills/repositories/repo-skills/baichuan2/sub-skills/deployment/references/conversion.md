# Checkpoint conversion for Baichuan 1 optimization reuse

## Scope

Use this reference when a user wants to apply existing Baichuan 1 compilation, quantization, or inference-optimization work to a Baichuan2 checkpoint. The conversion step normalizes the final `lm_head.weight` tensor and writes a separate converted model directory.

This reference does not validate a downstream Baichuan 1 optimization stack; it prepares the Baichuan2 checkpoint layout that such a stack expects.

## What the conversion changes

The documented conversion is intentionally small:

1. Load a single-file PyTorch checkpoint named `pytorch_model.bin`.
2. Read `lm_head.weight`.
3. Apply `torch.nn.functional.normalize(lm_head_w)`.
4. Store the normalized tensor back under `lm_head.weight`.
5. Save the checkpoint into a different model directory.

Equivalent core operation:

```python
import torch

checkpoint = torch.load("pytorch_model.bin", map_location="cpu")
checkpoint["lm_head.weight"] = torch.nn.functional.normalize(
    checkpoint["lm_head.weight"]
)
torch.save(checkpoint, "converted/pytorch_model.bin")
```

## Preconditions

- The input model directory contains a trusted `pytorch_model.bin` file. PyTorch `.bin` checkpoints are pickle-based; do not load untrusted files.
- The checkpoint is a state-dict-like mapping containing `lm_head.weight`.
- `lm_head.weight` is a tensor with at least two dimensions. The documented no-argument normalization defaults to row-wise L2 normalization (`p=2`, `dim=1`).
- The output directory is separate from the input directory. Do not overwrite the original checkpoint unless you have an external backup.
- This bundled helper targets the documented single-file `pytorch_model.bin` layout. Sharded checkpoints and `safetensors` layouts require a different conversion path.

## Bundled helper usage

Dry-run path check only:

```bash
python scripts/normalize_lm_head.py \
  --input-dir ./Baichuan2-7B-Chat \
  --output-dir ./Baichuan2-7B-Chat-lm-head-normalized \
  --dry-run
```

Dry-run plus checkpoint-key validation:

```bash
python scripts/normalize_lm_head.py \
  --input-dir ./Baichuan2-7B-Chat \
  --output-dir ./Baichuan2-7B-Chat-lm-head-normalized \
  --dry-run --validate-key
```

Write the converted checkpoint:

```bash
python scripts/normalize_lm_head.py \
  --input-dir ./Baichuan2-7B-Chat \
  --output-dir ./Baichuan2-7B-Chat-lm-head-normalized
```

The helper copies common non-weight sidecar files such as JSON tokenizer/config files and Python remote-code files unless `--no-copy-sidecars` is passed. It refuses to overwrite an existing output checkpoint unless `--overwrite` is supplied.

## Post-conversion checks

After conversion:

1. Confirm the output directory contains `pytorch_model.bin` and the expected config/tokenizer sidecars.
2. Check the reported norm statistics from the helper. Rows along `dim=1` should be approximately unit norm after conversion.
3. Run the downstream Baichuan 1 optimization or deployment stack against the converted directory, not the original checkpoint.
4. Keep the original Baichuan2 checkpoint for comparison and rollback.

## Known limitations

- The helper does not merge or rewrite sharded model indexes.
- The helper does not edit `safetensors` files.
- The helper does not prove that every Baichuan 1 optimization is semantically correct for a target workload; it performs only the documented `lm_head.weight` normalization.
