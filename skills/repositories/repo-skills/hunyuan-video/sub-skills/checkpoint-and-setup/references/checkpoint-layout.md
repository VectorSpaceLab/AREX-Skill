# Checkpoint Layout Reference

Read this when a task involves `--model-base`, `MODEL_BASE`, missing model files, text encoder preprocessing, or FP8 weight placement.

## Default layout

HunyuanVideo expects all model artifacts under a model root, normally `ckpts/`:

```text
ckpts/
  hunyuan-video-t2v-720p/
    transformers/
      mp_rank_00_model_states.pt
      mp_rank_00_model_states_fp8.pt        # optional FP8
      mp_rank_00_model_states_fp8_map.pt    # required with FP8
    vae/
      config.json
      pytorch_model.pt
  text_encoder/
    config/tokenizer/model files for the extracted LLaVA language model
  text_encoder_2/
    config/tokenizer/model files for CLIP-L
```

The canonical default `--dit-weight` is:

```text
ckpts/hunyuan-video-t2v-720p/transformers/mp_rank_00_model_states.pt
```

If `--dit-weight` is a directory, the loader searches for `pytorch_model_*.pt` or `*_model_states.pt`. If it is a file, that exact file must exist.

## Download and preprocessing recipe

Use the Hugging Face CLI to download the main HunyuanVideo model:

```bash
python -m pip install "huggingface_hub[cli]"
huggingface-cli download tencent/HunyuanVideo --local-dir ./ckpts
```

For slow or interrupted downloads, a mirror endpoint can be used when appropriate, and rerunning the same command resumes downloads. If a transient `.huggingface/.gitignore.lock` missing-file error appears, rerun the command.

The primary MLLM text encoder is prepared from a local LLaVA Transformers directory. After downloading that model into `ckpts/llava-llama-3-8b-v1_1-transformers`, use the bundled skill helper:

```bash
python sub-skills/checkpoint-and-setup/scripts/extract_llava_text_encoder.py \
  --input-dir ckpts/llava-llama-3-8b-v1_1-transformers \
  --output-dir ckpts/text_encoder
```

The secondary CLIP text encoder is downloaded separately into the model root:

```bash
cd ckpts
huggingface-cli download openai/clip-vit-large-patch14 --local-dir ./text_encoder_2
```

## Validation helper

The bundled validator is read-only and does not load multi-GB weights:

```bash
python sub-skills/checkpoint-and-setup/scripts/validate_checkpoint_layout.py --model-base ckpts
```

Use `--json` for automation and `--require-fp8 --dit-weight <fp8.pt>` for FP8 preflight.
