# Finetuning Troubleshooting

Use this reference before launching or rerunning a costly training job. Most failures can be caught by validating manifests and reviewing the rendered command first.

## Data and manifest symptoms

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `KeyError: 'conversations'` or missing turn text | Data followed the README prose typo `conversation` instead of the actual `conversations` key. | Rename to `conversations`; validate with `scripts/validate_finetune_data.py`. |
| Loss is zero or does not move | Bad SFT format, wrong placeholder policy, empty answers, or using legacy data with the wrong family rule. | Validate with `--family 2.5` for current data. For 2.5, single-image samples may omit `<ImageHere>` but multi-image samples need one token per image. For 2.0, image samples need placeholders. |
| `FileNotFoundError` for JSON or images | `data.txt` paths are relative to the training process working directory, not automatically to the manifest file. | Launch from the expected directory or use absolute paths. Use validator `--check-paths` before real training. |
| `Image format not supported` | `image` field is neither a string nor a list of strings. | Use a string for one image/video path or a non-empty string list for multiple images. |
| `Both _multi and _text are empty` | Empty JSON list, failed manifest load, or all files were filtered incorrectly. | Ensure each JSON file is a non-empty list and every `data.txt` line names a reachable JSON file. |
| Text-only samples behave as image samples, or image samples behave as text | A single JSON file mixes text-only and image-bearing samples; the mixer classifies the whole file from the first sample. | Split text-only and image-bearing samples into separate JSON files. |
| Sample counts are far larger or smaller than expected | `--given_num True` interprets manifest values as thousands; `--given_num False` interprets them as ratios. | `0.02` means 20 samples only in `given_num` mode. In ratio mode it means 2% of the file. |
| Manifest fails despite looking readable | Blank/comment lines, tabs, or paths with spaces are not handled by the source loader. | Keep `data.txt` to one path token plus optional numeric token per line. |

## Placeholder and legacy-version pitfalls

- 2.5 single image: no placeholder is required. A prompt like `Describe this image` is valid when `image` is a string.
- 2.5 multi image: use ordered placeholders such as `Image1: <ImageHere>; Image2: <ImageHere>;` and keep the count equal to `len(image)`.
- 2.0 image samples: use `<ImageHere>` for the image insertion point even for one image.
- 1.0 finetune examples are placeholder-free; do not copy UI/demo tokens into legacy finetune JSON unless a custom trainer requires them.

## Runtime and memory symptoms

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| CUDA out of memory at load or first step | 7B checkpoint, long sequence, `hd_num=18`, full-parameter tuning, or too many processes for available GPUs. | Reduce `--hd_num`, `--max_length`, loader `--batch_size`, or `--gradient_accumulation_steps`; switch to LoRA; ensure `--nproc_per_node` matches visible GPUs. |
| bf16 errors | GPU/runtime does not support bfloat16 or PyTorch build is incompatible. | Use a compatible CUDA PyTorch stack or change dtype only after testing the target model path. |
| Training hangs at distributed startup | Bad `MASTER_ADDR`, occupied `MASTER_PORT`, wrong `NNODES`/`NODE_RANK`, or launched more processes than available GPUs. | For single node, use localhost, a free port, `--nnodes 1`, `--node_rank 0`, and the actual GPU count. |
| DeepSpeed package/import error | Training extras are missing or version-incompatible. | Install the documented training stack (`deepspeed==0.12.3`, `peft==0.8.2`, compatible torch/transformers) in the runtime environment. |
| FSDP and DeepSpeed conflict | Command contains both `--deepspeed` and `--fsdp`. | Choose exactly one backend. The source shell templates are DeepSpeed; FSDP is a manual Trainer alternative. |
| Old `img_size` flag fails on 2.5 | 2.0 recipes expose `img_size`; the 2.5 trainer uses `resolution` and `hd_num`. | Remove 2.0-only flags when training 2.5. Use `--resolution` only if intentionally changing the 2.5 preprocessing resolution. |

## Batch-size confusion

The 2.5 `--batch_size` argument belongs to the custom data mixer. It is not the same as Hugging Face `--per_device_train_batch_size`. The source templates keep `per_device_train_batch_size=1` and use gradient accumulation. For tiny fixtures, start with both the internal mixer `--batch_size 1` and `--gradient_accumulation_steps 1` while checking only command shape and data validity.

For 2.0 legacy code paths, the README warns that larger batch sizes may require custom padding. Do not transfer a 2.5 command back to 2.0 without auditing the older collator/model code.

## LoRA and merge symptoms

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Adapter output exists but base model cannot be found later | PEFT adapter config records the base model path used during training. | Prefer absolute, stable base-model paths when training LoRA and when merging. |
| `merge_peft_adapter.py` assertion error | Missing `--adapter_model_name`, `--base_model_name`, or `--output_name`. | Use the bundled `entrypoints/xcomposer25/merge_peft_adapter.py`, pass all three arguments, and ensure the output directory is writable. |
| Merged model is too large or merge OOMs | Merge loads the base model in bfloat16 and applies adapter weights. | Merge on a machine with enough CPU/GPU memory, or keep the adapter unmerged and load it with PEFT. |
| Expected LoRA parameters are missing from saved output | `safe_save_model_for_hf_trainer()` saves LoRA tensors according to `--lora_bias`; full model weights are not saved in adapter mode. | Use `--lora_bias none/all/lora_only` deliberately; merge with the base model only after training is complete. |
| `--lora_weight_path` appears to do nothing | The parser declares the field, but the current trainer does not consume it. | Treat it as unused unless you have patched the trainer. Use Trainer checkpoints or PEFT loading logic instead. |

## Before rerunning

1. Re-run the validator on the exact manifest.
2. Re-render the command or inspect `entrypoints/xcomposer25/launch_full.sh` / `launch_lora.sh`, then compare mode, backend, GPU count, `hd_num`, `max_length`, LoRA flags, and output directory.
3. Delete or move only outputs you understand; do not overwrite a good LoRA adapter before merging or backing it up.
4. If switching between full and LoRA modes, explicitly reset `fix_vit`, `fix_sampler`, `use_lora`, learning rate, and output directory together.
