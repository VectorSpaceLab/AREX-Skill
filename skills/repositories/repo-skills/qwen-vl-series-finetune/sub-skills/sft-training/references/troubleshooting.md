# Troubleshooting

## Symptom: training crashes around CUDA or Flash Attention

Likely cause:

- Qwen3.5 is running with Flash Attention 2 enabled.
- The CUDA runtime is present but the local toolkit or kernel path is unstable.

Fix:

- Use `--disable_flash_attn2 True` for Qwen3.5.
- Fall back to the SDPA path.

## Symptom: LoRA and vision flags conflict

Likely cause:

- QLoRA is combined with trainable vision knobs.

Fix:

- Freeze the vision tower for language-only LoRA.
- If you need trainable vision features, keep the precision/quantization choices compatible with the repo notes.

## Symptom: video batches fail or misread media

Likely cause:

- `fps` and `nframes` were both set.
- The video media path does not resolve through the declared folder.

Fix:

- Keep one video sampling knob.
- Re-run the multimodal validator before training.

## Symptom: DeepSpeed import or save behavior looks odd

Likely cause:

- The environment lacks a working CUDA toolkit for extension checks.
- The chosen ZeRO template does not match the memory budget.

Fix:

- Use the environment diagnostic.
- Try the ZeRO-2 or offload templates before escalating to a more complex configuration.
