# Training Workflows

This reference gives concrete launch patterns and handoff rules for the repo's paired Pix2Pix-Turbo and unpaired CycleGAN-Turbo training workflows. Commands that launch training are intentionally explicit because they are long-running CUDA jobs that write checkpoints, metric samples, and tracker logs.

Always validate the dataset first with [validate_training_dataset.py](../scripts/validate_training_dataset.py), and ask before running network downloads or full training.

## Common launch preparation

1. Verify a CUDA-capable environment with the repo's training dependencies: PyTorch with CUDA, `accelerate`, `diffusers`, `transformers`, `peft`, `xformers` if requested, `wandb`, `lpips`, `clean-fid`, OpenAI `clip`, and `vision_aided_loss`.
2. Configure Accelerate once, or pass explicit launch settings:

   ```bash
   accelerate config
   ```

3. Prefer explicit `accelerate launch` settings for reproducibility and to avoid stale defaults:

   ```bash
   accelerate launch --num_processes 1 --main_process_port 29500 <training-entrypoint> ...
   ```

4. For multi-GPU runs, set `--num_processes` deliberately, choose a free `--main_process_port`, and keep `train_batch_size` as the per-device batch size. Use `gradient_accumulation_steps` to raise effective batch size without raising per-device memory.
5. If W&B network login is unavailable but W&B logging is desired, set `WANDB_MODE=offline` before launch and sync later.

## Paired Pix2Pix-Turbo training

### Minimal validated command pattern

The documented paired example trains on a Fill50K-style dataset. It uses SD-Turbo as the base model, xformers attention, W&B logging, validation visualization, and optional clean-FID tracking.

```bash
WANDB_MODE=offline \
accelerate launch --num_processes 1 --main_process_port 29500 src/train_pix2pix_turbo.py \
  --pretrained_model_name_or_path="stabilityai/sd-turbo" \
  --output_dir="output/pix2pix_turbo/fill50k" \
  --dataset_folder="data/my_fill50k" \
  --resolution=512 \
  --train_batch_size=2 \
  --enable_xformers_memory_efficient_attention \
  --viz_freq 25 \
  --track_val_fid \
  --report_to "wandb" \
  --tracker_project_name "pix2pix_turbo_fill50k"
```

Remove `WANDB_MODE=offline` when online W&B logging is configured. Remove `--track_val_fid` to skip paired clean-FID evaluation; the rest of paired validation still computes L2, LPIPS, and CLIP-SIM during eval steps.

### Important paired flags and defaults

| Flag | Source behavior |
| --- | --- |
| `--dataset_folder` | Required. Must contain paired `train_A`/`train_B`/`test_A`/`test_B` and prompt JSON files. |
| `--output_dir` | Required. The script creates `<output_dir>/checkpoints` and `<output_dir>/eval`. |
| `--pretrained_model_name_or_path` | The training code initializes the Pix2Pix-Turbo model when this value is `stabilityai/sd-turbo`; use that value for the documented workflow. |
| `--train_image_prep`, `--test_image_prep` | Default `resized_crop_512`; other transforms are listed in [data formats](data-formats.md#image-preparation-strings). |
| `--resolution` | Default `512`; used by the paired FID path to resize reference images when `--track_val_fid` is enabled. |
| `--train_batch_size` | Default `4` per device; reduce for memory pressure. |
| `--max_train_steps` | Default `10000`. |
| `--checkpointing_steps` | Default `500`; checkpoints are written when `global_step % checkpointing_steps == 1`, producing names such as `model_1.pkl`, `model_501.pkl`, and `model_1001.pkl`. |
| `--eval_freq` | Default `100`; validation metrics/images are produced when `global_step % eval_freq == 1`. |
| `--num_samples_eval` | Default `100`; caps paired validation samples. |
| `--viz_freq` | Default `100`; logs train/source, train/target, and train/model_output images. |
| `--report_to` | Default `wandb`; parser also accepts Accelerate tracker names such as `tensorboard`, `comet_ml`, or `all`. |
| `--mixed_precision` | Paired parser accepts `no`, `fp16`, or `bf16`; default is unset. |
| `--enable_xformers_memory_efficient_attention` | Optional. The paired script checks availability and raises a clear error if xformers is not installed. |
| `--gradient_checkpointing`, `--allow_tf32` | Optional memory/speed controls. |
| `--gan_disc_type` | Default and implemented value is `vagan_clip`; other values raise `NotImplementedError`. |

### Paired losses, metrics, and outputs

Training logs include:

- `lossG`, `lossD`, `loss_l2`, `loss_lpips`, and `loss_clipsim` when CLIP-sim loss is enabled.
- Validation `val/l2`, `val/lpips`, `val/clipsim`.
- Optional `val/clean_fid` only when `--track_val_fid` is set.
- W&B image groups for training source, target, and model output at `viz_freq` steps.

Output layout:

```text
<output_dir>/
├── checkpoints/
│   ├── model_1.pkl
│   ├── model_501.pkl
│   └── ...
└── eval/
    └── fid_<step>/        # only when FID tracking is enabled
```

### Handoff to paired inference

After paired training, route inference to [paired-inference](../../paired-inference/SKILL.md). The checkpoint is the `model_<step>.pkl` file under `<output_dir>/checkpoints`.

Command pattern for a trained paired checkpoint:

```bash
python src/inference_paired.py \
  --model_path "output/pix2pix_turbo/fill50k/checkpoints/model_6001.pkl" \
  --input_image "data/my_fill50k/test_A/40000.png" \
  --prompt "violet circle with orange background" \
  --output_dir "outputs"
```

Use a prompt that matches the conditioning task. Do not use a pretrained `--model_name` path when the intent is to evaluate a custom trained checkpoint.

## Unpaired CycleGAN-Turbo training

### Minimal validated command pattern

The documented unpaired example trains on a horse2zebra-style dataset. It sets `NCCL_P2P_DISABLE=1`, uses a non-default `main_process_port`, enables xformers, and logs through W&B.

```bash
export NCCL_P2P_DISABLE=1
WANDB_MODE=offline \
accelerate launch --num_processes 1 --main_process_port 29501 src/train_cyclegan_turbo.py \
  --pretrained_model_name_or_path="stabilityai/sd-turbo" \
  --output_dir="output/cyclegan_turbo/my_horse2zebra" \
  --dataset_folder "data/my_horse2zebra" \
  --train_img_prep "resize_286_randomcrop_256x256_hflip" \
  --val_img_prep "no_resize" \
  --learning_rate="1e-5" \
  --max_train_steps=25000 \
  --train_batch_size=1 \
  --gradient_accumulation_steps=1 \
  --report_to "wandb" \
  --tracker_project_name "gparmar_unpaired_h2z_cycle_debug_v2" \
  --enable_xformers_memory_efficient_attention \
  --validation_steps 250 \
  --lambda_gan 0.5 \
  --lambda_idt 1 \
  --lambda_cycle 1
```

Set `WANDB_MODE=offline` only when offline W&B logging is desired. The unpaired script performs clean-FID reference preparation from `test_A` and `test_B` at startup, then runs FID and DINO-structure validation at `validation_steps` intervals.

### Important unpaired flags and defaults

| Flag | Source behavior |
| --- | --- |
| `--dataset_folder` | Required. Must contain unpaired domain directories and `fixed_prompt_a.txt`/`fixed_prompt_b.txt`. |
| `--train_img_prep`, `--val_img_prep` | Required. The documented run uses `resize_286_randomcrop_256x256_hflip` for training and `no_resize` for validation. |
| `--output_dir` | Required. The script creates `<output_dir>/checkpoints`; it also creates FID reference/sample directories. |
| `--tracker_project_name` | Required. |
| `--pretrained_model_name_or_path` | Parser default is `stabilityai/sd-turbo`; the tokenizer and text encoder path in the training code use SD-Turbo. |
| `--seed` | Default `42`. |
| `--train_batch_size` | Default `4` per device; documented run uses `1`. |
| `--max_train_steps` | Parser default is `None`, but the training loop uses it in a `range(...)`; set it explicitly for real runs. |
| `--max_train_epochs` | Default `100`. |
| `--checkpointing_steps` | Default `500`; checkpoints are written when `global_step % checkpointing_steps == 1`. |
| `--validation_steps` | Default `500`; validation runs when `global_step % validation_steps == 1`. |
| `--validation_num_images` | Default `-1` for all validation images; use a positive value to bound validation cost. |
| `--viz_freq` | Default `20`; W&B image visualization runs when `global_step % viz_freq == 1` and the active tracker is W&B. |
| `--lora_rank_unet`, `--lora_rank_vae` | Defaults `128` and `4`. |
| `--enable_xformers_memory_efficient_attention` | Optional. Unlike the paired script, the unpaired script calls the enable method directly, so installation/CUDA mismatches may surface as lower-level errors. |
| `--gradient_checkpointing`, `--allow_tf32` | Optional memory/speed controls. |
| `--gan_disc_type` | Default implemented discriminator is `vagan_clip`. |

Supported image prep strings are defined in the data reference: `resized_crop_512`, `resize_286_randomcrop_256x256_hflip`, `resize_256`, `resize_256x256`, `resize_512`, `resize_512x512`, and `no_resize`.

### Unpaired losses, metrics, and outputs

Training logs include:

- Cycle losses: `cycle_a`, `cycle_b`.
- GAN losses: `gan_a`, `gan_b`, `disc_a`, `disc_b`.
- Identity losses: `idt_a`, `idt_b`.
- Validation metrics: `val/fid_a2b`, `val/fid_b2a`, `val/dino_struct_a2b`, `val/dino_struct_b2a`.

Output layout:

```text
<output_dir>/
├── checkpoints/
│   ├── model_1.pkl
│   ├── model_501.pkl
│   └── ...
├── fid_reference_a2b/
├── fid_reference_b2a/
└── fid-<step>/
    ├── samples_a2b/
    └── samples_b2a/
```

The DINO-structure metric constructs a DINO ViT-B/8 extractor through `torch.hub` on CUDA. Expect a model/cache requirement and possible network access unless the model is already cached.

### Handoff to unpaired inference

After unpaired training, route inference to [unpaired-inference](../../unpaired-inference/SKILL.md). The checkpoint is the `model_<step>.pkl` file under `<output_dir>/checkpoints`.

Command pattern for a trained A→B checkpoint:

```bash
python src/inference_unpaired.py \
  --model_path "output/cyclegan_turbo/my_horse2zebra/checkpoints/model_1001.pkl" \
  --input_image "data/my_horse2zebra/test_A/n02381460_20.jpg" \
  --prompt "picture of a zebra" \
  --direction "a2b" \
  --output_dir "outputs" \
  --image_prep "no_resize"
```

For custom unpaired checkpoints, provide both `--prompt` and `--direction`. Use `a2b` for domain A→domain B and `b2a` for domain B→domain A. Do not route custom checkpoint inference through a pretrained `--model_name` branch.

## Example dataset downloads

Use [download_example_dataset.sh](../scripts/download_example_dataset.sh) instead of the original direct download scripts. The bundled helper refuses network actions unless all required arguments and `--yes` are present.

```bash
bash sub-skills/training/scripts/download_example_dataset.sh --dataset fill50k --output-dir data --yes
bash sub-skills/training/scripts/download_example_dataset.sh --dataset horse2zebra --output-dir data --yes
```

Expected extraction folders:

- Fill50K paired example: `data/my_fill50k`.
- Horse2zebra unpaired example: `data/my_horse2zebra`.
