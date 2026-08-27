# Conversion utilities

Fengshenbang-LM includes utilities for delta weights, TensorFlow-to-PyTorch conversion, Diffusers-to-original Stable Diffusion conversion, and LLaMA HF/Fengshen/tensor-parallel conversion. This reference records what they do and how to plan them safely. Do not run conversion utilities from this skill unless the user explicitly approves model/checkpoint mutation.

## Conversion safety preflight

Before any real conversion, require:

1. **Input identity**: exact source format, model family, checkpoint directory/file layout, and whether the checkpoint is complete or delta-only.
2. **Output identity**: new output directory/file. Never use an input path as output.
3. **Mutation approval**: conversion writes large files; some utilities remove or overwrite existing output directories.
4. **Storage estimate**: target can be as large as the full model plus temporary shards.
5. **Dependency check**: `torch`, `transformers`, optional `diffusers`, optional tokenizer packages, and the installed Fengshen package.
6. **Backend/RAM**: most conversions are CPU/RAM/storage-bound but large LLaMA/Taiyi conversions may still need very large memory.
7. **Backup plan**: source checkpoints should be read-only or backed up.

Use the planners first:

```bash
python ../scripts/plan_ziya_conversion.py --source-format hf --target fs-finetune --model-size 13b --gpus 8 --vram-gb 80
python ../scripts/check_recipe_requirements.py --recipe conversion --device cpu --precision fp32
```

## Utility catalog

| Utility module | Purpose | Required inputs | Output/mutation | Important warnings |
|---|---|---|---|---|
| `fengshen.utils.apply_delta` | Add delta weights to a base LLaMA-compatible checkpoint to create a full target checkpoint | `--base-model-path`, `--delta-path`, `--target-model-path`, optional `--low-cpu-mem` | Writes target model, tokenizer, config; low-memory mode splits temporary shards; existing target directory may be removed | Requires compatible base/delta shapes; confirm rights to base model; never target the base or delta directory. |
| `fengshen.utils.make_delta` | Subtract base weights from target weights to create delta weights | `--base-model-path`, `--target-model-path`, `--delta-path`, optional hub repo id | Writes delta checkpoint shards and tokenizer | Requires same architecture; large RAM/storage; output should be fresh. |
| `fengshen.utils.convert_tf_checkpoint_to_pytorch` | Convert compatible TF BERT/ALBERT-style checkpoint to PyTorch state dict | `--tf_checkpoint_path`, `--bert_config_file`, `--pytorch_dump_path` | Writes a PyTorch dump file | Config must match checkpoint; output is a state dict, not necessarily a full HF directory. |
| `fengshen.utils.convert_diffusers_to_original_stable_diffusion` | Convert a local Diffusers Stable Diffusion pipeline directory to original `.ckpt` style weights | `--model_path`, `--checkpoint_path`, optional `--half` | Writes a large checkpoint file | Expects local `unet`, `vae`, and `text_encoder` weights; no model download should be allowed unless explicit. |
| `fengshen.utils.llama_convert.hf_to_fs` | Convert Hugging Face LLaMA checkpoint to Fengshen LLaMA format | `--input_path`, `--output_path` | Writes Fengshen model and tokenizer | Input must be complete HF checkpoint, not delta-only; may require `sentencepiece`/LLaMA tokenizer support. |
| `fengshen.utils.llama_convert.fs_to_hf` | Convert Fengshen single-shard LLaMA checkpoint to HF format | `--input_path`, `--output_path` | Writes HF model and tokenizer | Input should be a non-TP Fengshen checkpoint; LoRA merge behavior may be applied by model modules. |
| `fengshen.utils.llama_convert.convert_fs_llama_tp` | Split Fengshen LLaMA weights into tensor-parallel shards | `--input_dir`, `--output_dir`, `--model_parallel_size` | Creates `part_<rank>` outputs and per-rank weight maps | Config attention heads and hidden dimensions must divide by TP size; choose TP before training. |
| `fengshen.utils.llama_convert.merge_lt_mp_to_hf` | Merge Lightning/model-parallel Fengshen checkpoint shards to HF | `--model_parallel_size`, checkpoint path, output path | Reads multiple rank checkpoints and writes HF output | Exact checkpoint layout must match the training run; use only after inspecting checkpoint structure. |
| `fengshen.utils.llama_convert.fs_merge_weight` | Merge model weights such as adapter/LoRA-style components inside Fengshen LLaMA | `--input_path`, `--output_path` | Writes merged Fengshen output | Confirm adapter semantics; output is mutating and should be separate. |

## Command skeletons

These are shapes only. Replace placeholders with approved local paths and run only after preflight.

### Apply delta

```bash
python -m fengshen.utils.apply_delta \
  --base-model-path <base_llama_checkpoint> \
  --delta-path <delta_checkpoint> \
  --target-model-path <new_full_hf_output> \
  --low-cpu-mem
```

### Make delta

```bash
python -m fengshen.utils.make_delta \
  --base-model-path <base_checkpoint> \
  --target-model-path <full_target_checkpoint> \
  --delta-path <new_delta_output>
```

### HF LLaMA to Fengshen

```bash
python -m fengshen.utils.llama_convert.hf_to_fs \
  --input_path <hf_model_dir> \
  --output_path <new_fengshen_model_dir>
```

### Fengshen to tensor-parallel shards

```bash
python -m fengshen.utils.llama_convert.convert_fs_llama_tp \
  --input_dir <fengshen_model_dir> \
  --output_dir <new_fengshen_tp_dir> \
  --model_parallel_size <tp_size>
```

### Fengshen single-shard to HF

```bash
python -m fengshen.utils.llama_convert.fs_to_hf \
  --input_path <fengshen_model_dir> \
  --output_path <new_hf_output_dir>
```

### Diffusers pipeline to original Stable Diffusion checkpoint

```bash
python -m fengshen.utils.convert_diffusers_to_original_stable_diffusion \
  --model_path <local_diffusers_pipeline_dir> \
  --checkpoint_path <new_output.ckpt> \
  --half
```

### TF checkpoint to PyTorch dump

```bash
python -m fengshen.utils.convert_tf_checkpoint_to_pytorch \
  --tf_checkpoint_path <tf_checkpoint_prefix_or_dir> \
  --bert_config_file <bert_config_json_or_dir> \
  --pytorch_dump_path <new_pytorch_model.bin>
```

## Format compatibility notes

### Delta checkpoints

- Delta weights are not independently runnable full checkpoints.
- Apply delta only when base and delta architectures match exactly.
- Low-memory delta application can reduce peak RAM by splitting files, but it still writes full model outputs and temporary shards.

### Hugging Face versus Fengshen LLaMA

- HF format is expected by standard Transformers inference and bitsandbytes quantized loading.
- Fengshen format is expected by the Fengshen LLaMA full fine-tune example and Megatron model-parallel utilities.
- Tensor-parallel Fengshen format contains rank-specific subdirectories; use the same `model_parallel_size` during training and later loading.

### Diffusers versus original Stable Diffusion checkpoint

- Diffusers layout is a directory with components such as UNet, VAE, scheduler, tokenizer, and text encoder.
- Original `.ckpt` style conversion consolidates weights into one checkpoint file.
- Conversion depends on key mapping; mismatched Diffusers versions or missing components cause key errors or incomplete outputs.

### TensorFlow to PyTorch

- The converter is for compatible BERT/ALBERT-style checkpoints and config files.
- It writes a PyTorch state dict; a downstream wrapper may still be needed to produce a full `save_pretrained`-style directory.

## Troubleshooting

| Failure | Likely cause | Action |
|---|---|---|
| Output directory disappears or is replaced | Delta application target existed and utility removed/recreated it | Use a fresh target path; restore from backup if needed. |
| Shape mismatch during delta or conversion | Base/delta/model config mismatch | Stop; inspect config dimensions and model family before retry. |
| `pytorch_model.bin.index.json` missing or inconsistent | Sharded checkpoint layout incomplete | Verify all shard files and weight map before conversion. |
| TP conversion assertion on divisibility | Attention heads or hidden dimension not divisible by requested TP size | Choose a TP size that divides the config dimensions. |
| Missing tokenizer files | Source checkpoint lacks tokenizer artifacts | Provide compatible tokenizer directory; do not mix unrelated tokenizers. |
| Diffusers converter cannot find component weights | Input is not a local Diffusers pipeline directory | Download/cache separately if permitted, then retry with local path. |
| `sentencepiece` or tokenizer import error | LLaMA tokenizer dependency missing | Add dependency to environment plan; do not modify checkpoints while resolving imports. |
| CPU RAM exhausted | Conversion loads large model/shards | Use low-memory mode if available, larger RAM host, or staged conversion. |
