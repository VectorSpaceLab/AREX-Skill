# Checkpoints and Asset Layout

## Purpose

Read this before inference, LoRA training, or latent extraction. The repo expects a local `ckpts/` tree with model weights; the source checkout does not ship them.

## Expected Layout

The inspected code and README expect a structure like:

```text
ckpts/
  hunyuan-video-i2v-720p/
    transformers/mp_rank_00_model_states.pt
    vae/pytorch_model.pt
    lora/*.safetensors
  text_encoder_i2v/
  text_encoder_2/
  text_encoder/            # legacy/t2v path used by some configs
```

Key paths used by the code:

- `--model-base` defaults to `ckpts`
- `--i2v-dit-weight` defaults to `ckpts/hunyuan-video-i2v-720p/transformers/mp_rank_00_model_states.pt`
- `--dit-weight` defaults to `ckpts/hunyuan-video-t2v-720p/transformers/mp_rank_00_model_states.pt`
- `load_vae()` expects `vae/pytorch_model.pt`
- `TEXT_ENCODER_PATH` and `TOKENIZER_PATH` point to `text_encoder_i2v`, `text_encoder_2`, and `text_encoder`

## Download Commands

Run downloads from the real checkout root (`cd "$CHECKOUT_ROOT"`). These commands fetch public assets into that checkout; they are examples, not claims that weights are already present:

```bash
cd "$CHECKOUT_ROOT"
huggingface-cli download tencent/HunyuanVideo-I2V --local-dir ./ckpts
huggingface-cli download xtuner/llava-llama-3-8b-v1_1-transformers --local-dir ./ckpts/text_encoder_i2v
huggingface-cli download openai/clip-vit-large-patch14 --local-dir ./ckpts/text_encoder_2
```

If downloads are unavailable, stop at layout validation. Do not create placeholder checkpoint files.

## When to Check This File

- Before any real call to `sample_image2video.py` or the inference wrapper.
- Before LoRA training, because the training script loads the base transformer, VAE, and text encoders.
- Before latent extraction, because the extraction pipeline loads the VAE checkpoint.

## Missing-Asset Symptoms

- `ValueError: \`models_root\` not exists` from inference if `--model-base` points to a missing tree.
- `AssertionError: VAE checkpoint not found` from `hyvideo.vae.load_vae()` when the VAE file is absent.
- `No model weights found` or `model_path not exists` when the transformer weights are missing.
- `FileNotFoundError` for `meta_file.list` or `video_path` files during data preparation.

## Practical Checks

From the checkout root, use the generated-skill checker (not a script under the source checkout) before a run:

```bash
cd "$CHECKOUT_ROOT"
python "$SKILL_ROOT/scripts/check_checkpoint_layout.py" --ckpts-root "$CHECKOUT_ROOT/ckpts" --mode inference
python "$SKILL_ROOT/scripts/check_checkpoint_layout.py" --ckpts-root "$CHECKOUT_ROOT/ckpts" --mode train
python "$SKILL_ROOT/scripts/check_checkpoint_layout.py" --ckpts-root "$CHECKOUT_ROOT/ckpts" --mode extraction
```

The checker should report every missing required file explicitly instead of letting a later workflow fail deep inside the model loader.
