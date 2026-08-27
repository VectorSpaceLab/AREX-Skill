# NaFlex and Generative Troubleshooting

## NaFlex Is Unavailable

Symptom:

```text
NaFlex requires a timm version with NaFlex data support, including eval patchify transforms.
Install timm>=1.0.16 or a recent timm main checkout.
```

Likely cause: installed timm lacks `timm.data.naflex_dataset`, `timm.data.naflex_transforms`, or `timm.models.naflexvit`.

Recovery:

- Upgrade timm to a version with NaFlex support.
- If the user is only validating CLI/config values, use `scripts/naflex_config_report.py`, which does not import timm.
- Do not suggest running NaFlex eval transforms until the timm support check passes.

## Eval Transform Rejected

Symptom:

```text
NaFlex eval requires `--aug-cfg use_timm=True naflex=True`.
```

Likely cause: a dense transform callable was passed to `create_naflex_eval_transform`.

Recovery:

- CLI route: use `--use-naflex` so parser injects `aug_cfg` flags.
- Python route: call `create_model_and_transforms(..., aug_cfg={"use_timm": True, "naflex": True})`.
- Verify the returned factory has `is_naflex_eval_transform_factory` before building eval loaders.

## Non-Positive or Mismatched Config Values

Symptoms:

- `NaFlex patch sizes must be positive`.
- `NaFlex sequence lengths must be positive`.
- `NaFlex seq-len probabilities must match seq-lens length`.
- `NaFlex patch size probabilities must sum to a positive value`.
- `NaFlex max image tokens per batch must be positive`.
- `NaFlex batch divisor must be positive`.

Recovery:

- Require at least one positive `--naflex-patch-sizes` entry.
- Require at least one positive `--naflex-seq-lens` entry.
- Ensure probability lists have the same count and order as their target list.
- Use non-negative probabilities with a positive sum; they are normalized internally.
- Run `python scripts/naflex_config_report.py ...` before launching training.

## Max Token Schedule Surprises

Symptoms:

- Actual rows per local batch differ from `--batch-size`.
- Smaller sequence lengths appear more frequently per sample than expected.
- Training epoch sample count changes under distributed mode.

Likely causes:

- NaFlex schedules by `--naflex-max-tokens-per-batch`, not fixed rows.
- `--naflex-seq-len-probs` samples sequence lengths per batch; shorter buckets fit more rows, so per-sample skew toward short sequences is stronger.
- Distributed and worker scheduling may pad batches/samples to rank or worker counts.
- `--naflex-batch-divisor` can round scheduled row counts down to a divisible value.

Recovery:

- Explain row estimate as `floor(max_tokens_per_batch / row_cost)`, then adjusted by `batch_divisor` and implementation details.
- For GenLIP, row cost is roughly `image_seq_len + caption_cap`, where caption cap comes from `--naflex-max-text-tokens` or model context length.
- Use loss scaling (`--naflex-loss-scale linear` or `sqrt`) only when the user intentionally wants loss magnitude to track row-count changes.

## Dense Tensor vs Patch Dict Mismatch

Symptoms:

- Code indexes `batch[0]` or expects `(images, texts)` tuples but receives dicts.
- Model/task code fails with missing `patches`, `patch_coord`, or `patch_valid`.
- Custom callbacks report dense shape assumptions like `[B, C, H, W]` under NaFlex.

Recovery:

- Use dict keys: `batch["image"]["patches"]`, `batch["image"]["patch_coord"]`, `batch["image"]["patch_valid"]`.
- For audio, use `batch["audio"]` with the same patch keys.
- Keep `patch_valid` masks attached through model/probe code.
- Route ordinary dense model inference to the dense model-inference sub-skill when NaFlex is not actually needed.

## Variable Text or `text_valid` Missing

Symptoms:

- GenLIP/GenLAP loss includes padded caption tail or becomes unstable.
- Variable-text collation fails because tokenizer has no reserved pad token.
- Caption lengths produce many compile graphs.

Recovery:

- For GenLIP/GenLAP batches, include `text_valid` from collation or derive `text != pad_id` only when pad id is reliable.
- Use a tokenizer/config with a reserved `pad_token_id`.
- Keep valid caption tokens front-contiguous; packed-prefix loss assumes front-contiguous valid prefix/text tokens.
- Use `--text-pad-multiple` to bound distinct caption lengths for compile-heavy jobs.
- Use `--naflex-max-text-tokens` to cap captions and account for text tokens in GenLIP row cost.

## GenLIP Does Not Support CLIP Cosine Zero-Shot

Symptom: user asks to compute `image_features @ text_features.T` or call `encode_text` for GenLIP classification.

Likely cause: treating GenLIP as a contrastive dual-tower CLIP.

Recovery:

- Explain GenLIP is a caption LM over `[image_patches ; text]`, not a contrastive dual tower.
- For a research zero-shot probe, score `log P(template(class) | image)` with length-normalized teacher-forced likelihood.
- For paper-style frozen-backbone classification, use an attentive probe over image patch features.
- Warn that generative scoring is expensive and use `scripts/genlip_scoring_args.py` for a no-data cost report.

## GenLIP/GenLAP Scoring Cost Explosion

Symptoms:

- `genlip_zeroshot` run is unexpectedly slow.
- GPU memory spikes with large `score_batch`.
- Full ImageNet with many templates is infeasible.

Cost driver:

```text
forwards_per_image = ceil(num_classes * templates_per_class / score_batch)
total_forwards = num_images * forwards_per_image
```

Recovery:

- Lower `--num-images` for smoke tests.
- Use `--templates single` or `simple` before `openai`.
- Tune `--score-batch` to fit memory.
- Consider PMI only after basic scoring works; it adds an unconditional baseline pass.
- Use `scripts/genlip_scoring_args.py` to report estimated forwards before running.

## Checkpoint Architecture Mismatch

Symptoms:

- Many missing/unexpected keys when loading a checkpoint.
- Dense CLIP checkpoint fails under GenLIP or GenLAP.
- NaFlex conversion fails for ResNet or custom ViT towers.

Recovery:

- Match checkpoint family to config family: contrastive CLIP/CLAP vs GenLIP/GenLAP vs NaFlexCLAP.
- Use `force_naflex_vision` conversion only for compatible native/timm image ViT towers.
- Do not use dense CLIP conversion paths for GenLIP/GenLAP checkpoints.
- For native ViT conversion, confirm positional embeddings form a square patch grid.
- For timm NaFlex conversion, confirm installed timm provides `NaFlexVit` and checkpoint filter support.

## Audio NaFlex Geometry Errors

Symptoms:

- `n_mels` not divisible by `patch_freq`.
- `max_audio_tokens` smaller than `freq_tokens`.
- Audio position ids or masks look wrong.

Recovery:

- Choose `patch_freq` that divides `n_mels`.
- Ensure every sequence-length bucket can fit at least one full frequency column: `--naflex-seq-lens >= n_mels / patch_freq`.
- For full-height strips, expect 1-D time RoPE. For multi-row patches, expect 2-D `(freq, time)` coordinates.
- Preserve `patch_valid`; do not flatten/truncate audio patches in a way that drops frequency rows.

## Attentive Probe Is Not a Safe Default

Symptoms: user wants to run the attentive probe as a quick eval.

Caveats:

- It loads a checkpoint and ImageNet train/val data.
- It extracts and caches backbone features.
- It trains a probe head for multiple epochs.
- It needs timm `AttentionPoolLatent` and enough cache memory.

Recovery:

- Treat it as a reference workflow unless the user explicitly authorizes data access, checkpoint loading, and training.
- For planning only, summarize the protocol from `references/generative-workflows.md`.
