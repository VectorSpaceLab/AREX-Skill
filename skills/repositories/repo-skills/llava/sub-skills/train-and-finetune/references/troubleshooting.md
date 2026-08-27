# Training and Checkpoint Troubleshooting

## Malformed training JSON

**Symptoms**
- JSON parse errors.
- The training script complains about missing fields.
- Image samples never load.

**Recovery**
- Run `scripts/validate_training_json.py` on the dataset first.
- Check that the top level is a list and that each sample has `id` and `conversations`.
- Verify the `image` path if the sample is multimodal.

## Speaker or `<image>` mistakes

**Symptoms**
- Training data looks syntactically valid but the model learns bad prompts or fails to ground images.

**Recovery**
- Confirm the turn order alternates human/gpt.
- Ensure multimodal prompts include `<image>` where the image should be read.
- Compare with the schema notes in the data-format reference.

## DeepSpeed launcher or config problems

**Symptoms**
- `deepspeed` refuses to launch.
- ZeRO stages fail to initialize.
- The script expects a config path that was not copied or edited.

**Recovery**
- Choose the correct bundled `zero2.json`, `zero3.json`, or `zero3_offload.json` template.
- Keep the config path inside the generated skill.
- Reduce batch size or switch to offload when memory is limited.

## LoRA or base-model mismatch

**Symptoms**
- Merge utilities complain that the base model is missing or incompatible.
- The loaded weights look wrong after merge.

**Recovery**
- Supply the correct `--model-base`.
- Confirm that the adapter and base belong to the same model family.
- Use the checkpoint-utilities reference to decide whether merge, delta, or consolidate is the right operation.

## Memory pressure and precision failures

**Symptoms**
- CUDA OOM during training.
- Unexpected fp16/bf16 instability.
- Training crashes after increasing batch size or image resolution.

**Recovery**
- Lower per-device batch size.
- Increase gradient accumulation.
- Use LoRA/QLoRA instead of full fine-tuning.
- Switch to a more memory-efficient DeepSpeed config.

## Version drift and optional dependencies

**Symptoms**
- `peft` or `accelerate` import errors.
- W&B logging fails.
- FlashAttention build/install errors.

**Recovery**
- Keep the pinned training stack aligned with the package metadata.
- Use only the optional dependencies you actually need.
- Avoid assuming FlashAttention is available unless you installed it intentionally.

## Projector and delta extraction confusion

**Symptoms**
- The user wants a merged checkpoint but actually has only a delta or projector file.

**Recovery**
- Read the checkpoint-utilities reference and identify whether the artifact is a LoRA adapter, a delta checkpoint, a projector weight file, or a full model.
- Use the corresponding command template instead of guessing.
