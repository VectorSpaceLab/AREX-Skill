# Troubleshooting Evaluation and Conversion

## ImageNet Zero-Shot on the Wrong Model Family

Symptoms:

- `ValueError` mentioning ImageNet zero-shot requiring an image model.
- Empty zero-shot results for a generative model.
- User asks for ImageNet top-1 on `CLAP-*`, `naflexclap_*`, `naflexgenlip_*`, or `naflexgenlap_*`.

Resolution:

- For CLAP/NaFlexClap, route to `../audio-clap/SKILL.md` and use Hugging Face audio classification zero-shot instead of ImageNet.
- For GenLIP/GenLAP, route to `../naflex-generative/SKILL.md` and use generative/caption-scoring alternatives rather than `build_zero_shot_classifier`.
- For contrastive image/text models, confirm the raw model has `visual`, `encode_image`, and `encode_text`.

## Wrapped vs Bare Models

Symptoms:

- Capability checks fail on DDP/compiled/task-wrapped objects.
- Code strips too many wrapper layers and loses task-specific eval behavior.
- Direct `encode_text` or `encode_image` calls fail under FSDP.

Resolution:

- Use OpenCLIP's task-aware helpers (`zero_shot_eval`, `run_zero_shot_classifier`) when possible.
- For capability checks, unwrap `.module`, `._orig_mod`, and `TrainingTask.trainable_module` only as needed.
- For evaluation calls, pass the original task/model wrapper unless there is a clear reason to use the raw model.
- Under FSDP, all ranks must participate in classifier construction and eval forwards. Use task dummy batches for non-rank workers, especially for NaFlex.

## FSDP Non-Rank Dummy Batch Failures

Symptoms:

- NaFlex zero-shot eval raises because a dummy image cannot be synthesized.
- Non-rank workers hang or fail during FSDP eval.
- Direct `encode_text` calls produce DTensor/all-gather errors.

Resolution:

- Prefer a `TrainingTask` with `create_dummy_batch` for FSDP eval.
- Ensure the task registered FSDP forward methods for `encode_text` and `encode_image` during `prepare_fsdp`.
- Do not attempt NaFlex FSDP zero-shot with only a bare model and image size; the patch dict contract matters.

## Retrieval OOM or Slow Metrics

Symptoms:

- Validation OOMs after feature extraction, during retrieval metric calculation.
- Full-matrix retrieval is too slow or too memory-heavy.
- Half precision produces unstable tie-heavy rankings.

Resolution:

- Lower `--val-retrieval-chunk-size` from the default `4096`.
- Keep `--val-retrieval-precision fp32` unless memory pressure requires `--val-retrieval-precision model`.
- Use GPU retrieval for speed when chunking fits; use CPU retrieval if GPU memory is the bottleneck.
- Confirm feature lists have matching total item counts and feature dimensions before metric calculation.
- For generative-only tasks, skip retrieval metrics and report generative/caption loss instead.

## State-Dict Missing or Unexpected Keys

Symptoms:

- `load_state_dict` reports many missing/unexpected keys.
- Keys start with `module.`, `_orig_mod.`, or `trainable_module.`.
- A task checkpoint is loaded as if it were a flat inference state dict.

Resolution:

1. Run `scripts/checkpoint_key_report.py /path/to/checkpoint.pt --prefer-ema`.
2. Identify whether `state_dict` or `state_dict_ema` is the intended payload.
3. Strip only mechanical wrapper prefixes that match the load target.
4. Use OpenCLIP factory load paths before writing custom key conversion.
5. Use `strict=False` only after documenting remaining missing/unexpected keys.

If the checkpoint came from task training, remember that the full checkpoint may include optimizer, scaler, epoch, and counters. Those are training-resume data, not inference/export weights.

## EMA Selection Confusion

Symptoms:

- Two payloads exist: `state_dict` and `state_dict_ema`.
- User wants the best eval/export checkpoint but code loads the non-EMA weights.
- Checkpoint produced by a task with `ModelEmaV3` behaves differently from the current trainable module.

Resolution:

- Prefer EMA for inference/evaluation/export when the user wants smoothed eval weights and `state_dict_ema` exists.
- Use main `state_dict` when resuming training or when the user explicitly wants raw trainable weights.
- If the live task object exists, `state_dict_for_inference()` already prefers EMA.

## FSDP Scalar Shape Mismatch

Symptoms:

- Only `logit_scale` or `logit_bias` shape differs: 0-D scalar vs `[1]` tensor.
- Loading between FSDP and non-FSDP models fails strict shape checks.

Resolution:

- Use task/factory load helpers; they reconcile 0-D and 1-D scalar parameters.
- Do not write broad reshape logic for every parameter; this special case is for scalar logit parameters.
- Confirm the rest of the state dict matches before suppressing strict errors.

## Unsafe Pickle Risk

Symptoms:

- `torch.load(..., weights_only=True)` fails with a weights-only payload error.
- A checkpoint includes custom Python objects in optimizer or metadata payloads.

Resolution:

- Keep `weights_only=True` for default inspection and generated scripts.
- Ask for explicit user approval before `weights_only=False` and only for trusted checkpoints.
- If only inference weights are needed, request a clean state dict or safetensors export instead of loading arbitrary training metadata.

## Conversion Format Mismatch

Symptoms:

- A SigLIP `.npz` is loaded through a generic PyTorch state-dict path.
- MobileCLIP keys remain under `image_encoder.model...` or `text_encoder...` after conversion.
- NaFlex conversion leaves native ViT keys like `visual.conv1.weight` for a NaFlexVit destination.

Resolution:

- Use `.npz`/`.npy` big_vision path for SigLIP big_vision weights.
- Use `convert_state_dict` for supported MobileCLIP signatures.
- Use `force_naflex_vision=True` plus `convert_naflex_state_dict` only for compatible native ViT or timm EVA/ViT towers.
- Route HF CLAP state-dict conversion to `../audio-clap/SKILL.md`.

## Hugging Face Push Auth or Network Failure

Symptoms:

- `push_to_hf_hub` cannot create repo or upload files.
- Missing `huggingface_hub` or `safetensors` dependency.
- Tokenizer fallback produces an unexpected tokenizer config.

Resolution:

- Treat push as a separate side-effecting step after local export/eval checks.
- Confirm HF auth token, `repo_id`, private/public setting, revision, and `create_pr` choice.
- Install `huggingface_hub` and `safetensors` when needed.
- For custom tokenizers, verify whether fallback to the default CLIP HF tokenizer is acceptable or whether config/tokenizer handling needs a custom export step.
