# SFT Workflow

## Launch variants

- **Full finetuning**: update the whole model, usually with ZeRO-2 or ZeRO-3.
- **Language LoRA**: set `lora_enable=True` and keep the vision tower frozen.
- **Vision LoRA**: set `lora_enable=True`, `vision_lora=True`, and keep the base vision tower and merger frozen so PEFT trains LoRA adapters for the selected vision modules.
- **Video SFT**: use the video media keys and tune the pixel/frame controls carefully.

## Useful launch choices

- The executable helper runs the bundled `src/train/train_sft.py` from the skill root with `PYTHONPATH=src`; it does not require the original checkout.
- ZeRO-2 is often easier to debug.
- ZeRO-3 or offload variants help when memory is tight.
- `--disable_flash_attn2 True` is the stable path for Qwen3.5.
- Generation-based evaluation can be added with `eval_path` and `compute_metrics`.

## Typical command ingredients

- `--model_id`
- `--data_path`
- `--image_folder`
- `--output_dir`
- `--deepspeed`
- `--per_device_train_batch_size`
- `--gradient_accumulation_steps`
- `--learning_rate`
- `--num_train_epochs`
- `--bf16` or `--fp16`
- `--disable_flash_attn2`
- `--lora_enable` / `--vision_lora`

## Video-specific notes

- Use one media sampling scheme, not both `fps` and `nframes`.
- The model accepts multi-image/video layouts, but the pixel budget should be matched to the available VRAM.
- Qwen3-VL uses the repo’s 32×32 token-budget guidance in the README.

## Executable helper

```bash
python scripts/sft_command.py --help
python scripts/sft_command.py --variant lora --model-id Qwen/Qwen2.5-VL-3B-Instruct --data-path data/train.json --image-folder data/images --output-dir outputs/sft
# add --run only when the printed command should be executed
```

## Evaluation during training

If the user wants generation-based validation:

- add `eval_path`
- add `eval_image_folder` when the eval media lives elsewhere
- wire in a custom `compute_metrics` function
- keep the evaluation dataset in the same JSON family as the training dataset
