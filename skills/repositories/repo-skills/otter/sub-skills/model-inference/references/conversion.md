# Checkpoint conversion reference

Conversion is expensive: every real converter loads checkpoint weights and writes a Hugging Face-style output directory. Use the bundled inspector first because it is safe and does not import `torch`, `transformers`, or `otter-ai`:

```bash
python scripts/inspect_checkpoint_conversion_args.py --list
python scripts/inspect_checkpoint_conversion_args.py --script fp32-to-fp16 --checkpoint-path CHECKPOINT --load-bit bf16 --emit-command
```

Replace `CHECKPOINT` and output paths with project-owned paths. Do not use defaults copied from old development machines; this skill intentionally requires explicit paths for risky converters.

## Conversion manifest

| Manifest id | Packaged module | Purpose | Required inputs | Output default/effect | Key warnings |
|---|---|---|---|---|---|
| `fp32-to-fp16` | `otter_ai.models.otter.converting_otter_fp32_to_fp16` | Load an Otter HF checkpoint in `fp16` or `bf16` and save it back out. | `--checkpoint_path`; optional `--load_bit {fp16,bf16}` | If `--save_path` is omitted, source behavior writes to `<checkpoint_path>-<load_bit>`. | Loads full model with `device_map="auto"`; verify disk and GPU/CPU memory first. |
| `flamingo-to-otter` | `otter_ai.models.otter.converting_flamingo_to_otter` | Load a Flamingo HF checkpoint, add Otter's `<answer>` special token, resize Llama embeddings if needed, and save through `OtterForConditionalGeneration.save_pretrained`. | `--checkpoint_path`; provide `--save_path` | Source parser permits omitted `--save_path`, but the save call needs a usable output directory; provide it explicitly. | This is for HF-format Flamingo checkpoints, not arbitrary PT state dicts. |
| `otter-to-lora` | `otter_ai.models.otter.converting_otter_to_lora` | Add PEFT LoRA metadata/modules to an Otter checkpoint and save. | Provide `--checkpoint_path` and `--save_path` explicitly. | No safe public default; helper refuses to rely on old private defaults. | Uses LoRA `r=16`, `lora_alpha=32`, `lora_dropout=0.05`; target modules depend on the language architecture. |
| `pt-to-hf` | `otter_ai.models.otter.converting_otter_pt_to_hf` | Load an existing `.pt` state dict and inject it into a pretrained Otter HF base. | `--old_ckpt_path`, `--new_hf_path`, `--pretrained_model_path` | Saves a Hugging Face model folder at `--new_hf_path`. | Known packaged-entry import defect in inspected build; verify a fixed installed build before using this route. |

## Typical plans

### Downcast an Otter HF checkpoint

Use when a full-precision HF checkpoint must be saved in lower precision:

```bash
python scripts/inspect_checkpoint_conversion_args.py \
  --script fp32-to-fp16 \
  --checkpoint-path CHECKPOINT \
  --load-bit bf16 \
  --save-path CHECKPOINT-bf16 \
  --emit-command
```

Review the emitted command, confirm available memory and disk, then run it in the project environment only when the checkpoint and output directory are intentionally selected.

### Convert a Flamingo HF checkpoint to Otter HF format

Use when the source checkpoint is already Hugging Face-compatible Flamingo:

```bash
python scripts/inspect_checkpoint_conversion_args.py \
  --script flamingo-to-otter \
  --checkpoint-path FLAMINGO_HF_CHECKPOINT \
  --save-path OTTER_HF_OUTPUT \
  --emit-command
```

The converter adds `<answer>` to the tokenizer and may resize Llama embeddings before saving as an Otter conditional-generation model.

### Add LoRA structure to an Otter checkpoint

Use only when the language architecture is one of the supported classes:

| Architecture | LoRA target modules |
|---|---|
| `LlamaForCausalLM` | `q_proj`, `v_proj` |
| `OPTForCausalLM` | `q_proj`, `v_proj` |
| `GPTJForCausalLM` | `q_proj`, `v_proj` |
| `GPTNeoXForCausalLM` | `query_key_value` |
| `MPTForCausalLM` | `Wqkv` |

```bash
python scripts/inspect_checkpoint_conversion_args.py \
  --script otter-to-lora \
  --checkpoint-path OTTER_HF_CHECKPOINT \
  --save-path OTTER_LORA_OUTPUT \
  --emit-command
```

### PT state dict to HF folder

Use this only after confirming the installed package version has a working packaged entry point:

```bash
python scripts/inspect_checkpoint_conversion_args.py \
  --script pt-to-hf \
  --old-ckpt-path MODEL_STATE.pt \
  --new-hf-path OTTER_HF_OUTPUT \
  --pretrained-model-path OTTER_HF_BASE \
  --emit-command \
  --allow-known-risk
```

The converter loads a pretrained base with `device_map="auto"`, optionally unwraps `model_state_dict`, loads the PT state with `strict=False`, and saves the output folder.

## What is not covered

- OtterHD/Fuyu checkpoints are loaded through Hugging Face Fuyu APIs for inference. The Otter conversion helpers above do not convert Fuyu/OtterHD weights.
- Training checkpoint selection, save cadence, and resume logic belong to [training](../../training/SKILL.md).
- Serving model-worker load-bit flags belong to [serving](../../serving/SKILL.md).
