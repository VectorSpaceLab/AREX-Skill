# Data-Preparation Workflows

## Purpose

Read this when you need to turn raw videos into the latent cache that LoRA training consumes.

## 1) Configure the extraction run

The checkout’s `hyvideo/hyvae_extract/vae.yaml` defines the extraction inputs:

- `vae_path`
- `video_url_files`
- `output_base_dir`
- `sample_n_frames`
- `target_size`
- `enable_multi_aspect_ratio`
- `use_stride`

The checked-in YAML uses a real checkout-relative metadata-list/output example but still requires a downloaded VAE at `ckpts/hunyuan-video-i2v-720p/vae`; it does not provide or fake that checkpoint. Copy the YAML for your run if your metadata or output location differs.

The bundled skill script can print the launcher for that YAML or execute it across multiple GPUs.

## 2) Validate the raw metadata first

Before extraction:

- confirm the `meta_file.list` file exists
- confirm every listed JSON file exists
- confirm each JSON has a `video_path` and `raw_caption.long caption`

From the real checkout root, use the generated-skill helper:

```bash
cd "$CHECKOUT_ROOT"
python "$SKILL_ROOT/sub-skills/data-preparation/scripts/check_dataset_layout.py" --mode raw --meta-file-list "$CHECKOUT_ROOT/assets/demo/i2v_lora/train_dataset/meta_file.list"
```

## 3) Run the latent extraction

The source launcher assigns one local rank per GPU and runs `hyvideo/hyvae_extract/run.py` with the same config file on each rank.

Important behavior:

- the script splits the JSON list across ranks
- already processed videos are skipped if the `.npy` file exists
- the VAE is loaded from the checkpoint tree before any encoding starts

Typical dry-run pattern (run from the checkout root):

```bash
cd "$CHECKOUT_ROOT"
python "$SKILL_ROOT/sub-skills/data-preparation/scripts/run_hyvae_extract.py" \
  --repo-root "$CHECKOUT_ROOT" \
  --config "$CHECKOUT_ROOT/hyvideo/hyvae_extract/vae.yaml" \
  --host-gpu-num 8 \
  --dry-run
```

## 4) Validate the processed output

After the run, verify that each latent has:

- a matching `.npy` file
- a sibling JSON entry under `json_path/`
- a valid `latent_shape` and `npy_save_path`

Use the generated-skill checker from the checkout root before handing the directory to training:

```bash
python "$SKILL_ROOT/sub-skills/data-preparation/scripts/check_dataset_layout.py" --mode processed --json-dir "$CHECKOUT_ROOT/assets/demo/i2v_lora/train_dataset/processed_data/json_path"
```

## 5) Optional text-encoder asset preparation

If you need to preprocess the LLaVA text encoder/tokenizer assets referenced by the README, do that only after the VAE/checkpoint layout is already correct. The helper is optional and external-model-bound, so it is documented in checkpoints/troubleshooting instead of being a default run step.
