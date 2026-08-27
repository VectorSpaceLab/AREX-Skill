# DreamBooth LoRA, Sol-RL, and post-training boundaries

Use this reference when the user asks for personalization, reward-based post-training, SFT/RL integration, wandb/HF hub behavior, or a plan that is not ordinary supervised image/video training.

## DreamBooth LoRA for Sana

The repo provides `train_scripts/train_dreambooth_lora_sana.py` plus `train_scripts/train_lora.sh`. This path uses the diffusers Sana model family and PEFT LoRA layers.

### Data assumptions

DreamBooth LoRA typically starts from a few subject images, for example 3-5 dog images. The trainer accepts either:

- `--instance_data_dir`: local folder containing instance images, or
- `--dataset_name`: a Hugging Face dataset.

Do not pass both. If using prior preservation, also provide class image settings:

- `--with_prior_preservation`
- `--class_data_dir`
- `--class_prompt`
- optionally `--num_class_images` and `--prior_loss_weight`

Safe local check:

```bash
python skills/disco/sana/sub-skills/training-data-configs/scripts/validate_dataset_layout.py \
  --path data/dreambooth/my_subject \
  --mode lora \
  --max-samples 20
```

### Command template

```bash
export MODEL_NAME="Efficient-Large-Model/Sana_1600M_1024px_BF16_diffusers"
export INSTANCE_DIR="data/dreambooth/my_subject"
export OUTPUT_DIR="trained-sana-lora-my-subject"

accelerate launch --num_processes 4 --main_process_port 29500 --gpu_ids 0,1,2,3 \
  train_scripts/train_dreambooth_lora_sana.py \
  --pretrained_model_name_or_path="$MODEL_NAME" \
  --instance_data_dir="$INSTANCE_DIR" \
  --output_dir="$OUTPUT_DIR" \
  --mixed_precision=bf16 \
  --instance_prompt="a photo of sks subject" \
  --resolution=1024 \
  --train_batch_size=1 \
  --gradient_accumulation_steps=4 \
  --use_8bit_adam \
  --learning_rate=1e-4 \
  --report_to=wandb \
  --lr_scheduler=constant \
  --lr_warmup_steps=0 \
  --max_train_steps=500 \
  --validation_prompt="A photo of sks subject in a cinematic scene" \
  --validation_epochs=25 \
  --seed=0
```

Optional knobs from the trainer and docs:

- `--lora_layers "to_k,to_q,to_v"` to restrict LoRA target modules. If omitted, default target selection is used.
- `--max_sequence_length` to change text embedding length.
- `--complex_human_instruction` for the complex-human-instruction prompt used by Sana app configs.
- `--offload` to offload text encoder and VAE to CPU when not used.
- `--cache_latents` to precompute latents and drop the VAE from memory during training.
- `--push_to_hub` after `huggingface-cli login`; avoid mixing `--report_to=wandb` with `--hub_token` because the trainer rejects that for token-safety reasons.

### Accelerate and dependency notes

The docs recommend installing a current diffusers checkout and initializing accelerate:

```bash
accelerate config
# or non-interactive default:
accelerate config default
```

PEFT is required for LoRA; the docs call out `peft>=0.14.0`. W&B logging requires `wandb` and `wandb login` unless using offline/disabled logging.

## Sol-RL in-repo post-training

Sol-RL uses shell launchers under `train_scripts/sol_rl/` and config functions under `configs/sol_rl/`. It is reward-based RL-style post-training for Sana, FLUX.1, and SD3.5-L, with the signature "FP4 explore, BF16 train" for quantized families.

### Launchers

Default single-node launchers:

```bash
bash train_scripts/sol_rl/run_sana_single_node_8gpu.sh
bash train_scripts/sol_rl/run_sd3_single_node_8gpu.sh
bash train_scripts/sol_rl/run_flux1_single_node_8gpu.sh
```

Select a config function with `CONFIG_SPEC`:

```bash
CONFIG_SPEC=configs/sol_rl/sana.py:sana_diffusionnft_pickscore \
bash train_scripts/sol_rl/run_sana_single_node_8gpu.sh
```

```bash
CONFIG_SPEC=configs/sol_rl/sd3.py:sd3_compile_hpsv2 \
bash train_scripts/sol_rl/run_sd3_single_node_8gpu.sh
```

```bash
CONFIG_SPEC=configs/sol_rl/flux1.py:flux1_sol_rl_imagereward \
bash train_scripts/sol_rl/run_flux1_single_node_8gpu.sh
```

The Sana launcher resolves a native Sana checkpoint at `output/pretrained_models/SANA_LinearFFN.pth` by default, downloading/symlinking from its configured `hf://` source if absent.

### Config family map

Names follow:

```text
<model>_<family>_<reward>
```

Families:

| Family | Meaning | Rollout shape | Transformer Engine / NVFP4 |
|---|---|---|---|
| `diffusionnft` | PEFT-only baseline | 24-in-24 | not needed |
| `naive_scaling` | PEFT brute-force scaling | 24-in-96 | not needed |
| `compile` | BF16 compiled brute-force scaling | 24-in-96 | not needed |
| `naive_quant` | direct NVFP4 compiled rollout | 24-in-96 | needed |
| `sol_rl` | two-stage decoupled rollout | 24-in-96 | needed |

Recommended first runs are the `diffusionnft_pickscore` variants for each model.

### Rewards and checkpoints

Supported online reward suffixes:

- `pickscore`
- `clipscore`
- `hpsv2`
- `imagereward`

HPSv2 needs manual local reward checkpoints under `reward_ckpts/`:

```bash
mkdir -p reward_ckpts
cd reward_ckpts
wget https://huggingface.co/laion/CLIP-ViT-H-14-laion2B-s32B-b79K/resolve/main/open_clip_pytorch_model.bin
wget https://huggingface.co/xswu/HPSv2/resolve/main/HPS_v2.1_compressed.pt
cd -
```

Other reward models are auto-downloaded on first use:

- `clipscore`: `openai/clip-vit-large-patch14`
- `pickscore`: `laion/CLIP-ViT-H-14-laion2B-s32B-b79K` and `yuvalkirstain/PickScore_v1`
- `imagereward`: `ImageReward-v1.0`

### Tiny debug run shape

The native smoke test uses a tiny rollout to exercise real launcher paths. Use this as a planning pattern, not a quality recipe:

```bash
WANDB_MODE=offline \
NPROC_PER_NODE=1 \
CUDA_VISIBLE_DEVICES=0 \
CONFIG_SPEC=configs/sol_rl/sana.py:sana_diffusionnft_pickscore \
bash train_scripts/sol_rl/run_sana_single_node_8gpu.sh \
  --config.num_epochs=1 \
  --config.debug=True \
  --config.resume=False \
  --config.rollout_sample_num_steps=2 \
  --config.sample.num_image_per_prompt=2 \
  --config.sample.best_of_n=2 \
  --config.sample.full_rollout_num=2 \
  --config.sample.rollout_batch_size=2 \
  --config.sample.per_prompt_iter_num=1 \
  --config.sample.per_gpu_to_process_prompts=1 \
  --config.sample.per_gpu_total_samples_to_train=2 \
  --config.sample.test_batch_size=1 \
  --config.train.batch_size=1 \
  --config.train.gradient_accumulation_steps=1 \
  --config.train.n_batch_per_epoch=1 \
  --config.train.num_inner_epochs=1 \
  --config.enable_debug_image_save=False \
  --config.logdir=output/sol_rl_logs \
  --config.run_name=sana_diffusionnft_pickscore_debug \
  --config.save_dir=output/sol_rl_debug \
  --config.resume_from=output/sol_rl_debug
```

Sol-RL resume behavior is config-driven. `resume_from` points at a directory containing `checkpoints/`; `resume` must be true to resume.

## Cosmos-RL boundary

`docs/sana_cosmos_rl.md` describes an external integration, not a native Sana repo training script. Use this when the user specifically asks for Cosmos-RL SFT/RL infrastructure or async reward services.

Supported external preset families in Cosmos-RL include:

- SFT image: `sana-image-sft`, `sana-image-sft-lora`
- SFT video: `sana-video-sft`, `sana-video-sft-lora`
- RL image: `sana-image-nft`
- RL video: `sana-video-nft`

Example external command shapes:

```bash
cosmos-rl --config ./configs/sana/sana-image-sft-lora.toml cosmos_rl.tools.dataset.diffusers_dataset
```

```bash
cosmos-rl --config ./configs/sana/sana-image-nft.toml cosmos_rl.tools.dataset.diffusion_nft
```

Data notes from the integration doc:

- Cosmos-RL SFT uses local dirs with `*.json` plus `*.jpg` or `*.mp4`.
- Cosmos-RL RL supports image datasets such as pickscore, OCR, and GenEval, and video datasets such as filtered VidProM.
- Reward service is separate and asynchronous; trainers need variables such as `REMOTE_REWARD_TOKEN`, `REMOTE_REWARD_ENQUEUE_URL`, and `REMOTE_REWARD_FETCH_URL`.

Boundary rule: for Cosmos-RL, provide a compatibility plan and call out that verification requires a Cosmos-RL installation and config tree. Do not pretend the native Sana repo launchers cover the external Cosmos-RL commands.

## Logging, checkpoints, and publication

### W&B

- Native image/video wrappers default to tensorboard through their shell scripts.
- Direct pyrallis runs can use `--report_to=wandb`; if so, confirm `wandb login` or set `WANDB_MODE=offline`.
- LoRA docs use `--report_to=wandb` and qualitative validation prompts.
- LongSANA/WM recipes provide `--disable-wandb`.

### Checkpoints

- Image/video/Sprint trainers save under `<work_dir>/checkpoints` and write a resolved `config.yaml` in `work_dir`.
- `--resume_from=latest` searches under the current `work_dir`. Avoid reused `work_dir` names unless intentional.
- FSDP resume can have stricter format/state requirements than non-FSDP resume.
- DreamBooth LoRA uses accelerate checkpoint directories named `checkpoint-<step>` and supports `--resume_from_checkpoint latest`.
- Sol-RL saves under `config.save_dir/checkpoints/checkpoint-<global_step>`.

### Hub push

- DreamBooth LoRA can push adapters with `--push_to_hub` after HF authentication.
- For data with third-party subjects, copyrighted images, or noncommercial WM dataset derivatives, verify license and consent before upload.
