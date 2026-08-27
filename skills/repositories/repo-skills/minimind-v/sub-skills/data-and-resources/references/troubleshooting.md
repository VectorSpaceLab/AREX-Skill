# Data and Resource Troubleshooting

## Missing tokenizer or SigLIP2

Symptoms: tokenizer load fails, `model.processor is None`, image preprocessing fails, or inference/training cannot attach the vision encoder.

Recovery:

- Confirm `model/tokenizer.json` and `model/tokenizer_config.json` exist.
- Confirm `model/siglip2-base-p32-256-ve/` contains `config.json`, `model.safetensors`, and `preprocessor_config.json`.
- The VLM code does not download SigLIP2 automatically. Ask before downloading external resources.

## Missing native weights

Symptoms: native inference/training expects `out/llm_768.pth`, `out/pretrain_vlm_768.pth`, `out/sft_vlm_768.pth`, or `_moe` variants.

Recovery:

- Match dense/MoE with the `_moe` filename suffix and `--use_moe` value.
- For SFT while skipping Pretrain, use the LLM base weight (`llm_768*.pth`) rather than requiring `pretrain_vlm`.
- Do not start downloads or training to create weights unless the user approves.

## Invalid parquet schema

Symptoms: missing `conversations` or `image_bytes`, JSON decode errors, missing `role`/`content`, non-bytes image payload, or unreadable image bytes.

Recovery:

1. Run `validate_vlm_parquet.py` against the file.
2. Fix rows so `conversations` is a JSON string or list of turns.
3. Ensure each turn has string `role` and `content`.
4. Ensure `image_bytes` is bytes-like or a non-empty list of bytes-like images.
5. Install Pillow when image decode proof is required.

## Torch backend mismatch

Symptoms: torch import failure, CUDA unavailable, or `torchvision` wheel conflicts.

Recovery:

- Install torch separately for the host backend. Do not assume requirements install torch.
- Use CPU for static validation; use CUDA only when the user wants GPU inference/training and the wheel/driver are compatible.
- Do not treat a CPU import as proof of CUDA training readiness.
