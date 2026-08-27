# GenLIP and GenLAP Generative Workflows

## Mental Model

GenLIP and GenLAP are not contrastive CLIP/CLAP models. They use one transformer over a packed media-prefix plus caption sequence and train a next-token language-modeling objective over caption tokens.

- GenLIP prefix: NaFlex image patches.
- GenLAP prefix: NaFlex log-mel spectrogram patches.
- Sequence layout: `[media_patches ; caption_tokens]` padded per row.
- Attention: media patches attend bidirectionally within media; text attends causally to text and can attend to media; media never attends to text.
- Loss: cross entropy over text tokens only; image/audio patches and padding are ignored.
- Default training path: model computes a memory-efficient fused caption loss inside `forward(compute_loss=True)`.

Do not suggest CLIP-style cosine zero-shot with `encode_text` for GenLIP/GenLAP. The generative models do not expose paired contrastive text/image embeddings for classification in that way.

## GenLIP Image Model

`NaFlexGenLip` combines:

- `NaFlexGenLipVisionCfg`: image patch geometry, input/pre-trunk normalization, and image-only pooling behavior.
- `NaFlexGenLipTextCfg`: default `tiktoken` text config with reserved pad/BOS/EOS ids and context length.
- `NaFlexGenLipTrunkCfg`: shared transformer width/depth/heads, MRoPE section, gated attention, SwiGLU, LayerScale, qk-norm, norm flavor, and optional `pack_prefix`.

Key APIs and outputs:

- `model(image=patch_dict, text=text_ids, text_valid=mask, compute_loss=False)` returns `{"logits": logits, "image_seq_len": ni}`.
- `model(..., compute_loss=True)` returns `{"loss": scalar}` and does not materialize full-vocabulary logits in the fused path.
- `model.encode_image(image_patch_dict, normalize=False)` returns pooled image features for frozen-feature probes, not a contrastive CLIP text-matching path.

Patch dict keys are `patches`, `patch_coord`, and `patch_valid`. `text_valid` may be omitted only when `text != pad_id` correctly identifies valid caption tokens.

## GenLAP Audio Model

`NaFlexGenLap` is the audio sibling of GenLIP:

- Prefix is a NaFlex spectrogram patch dict under `audio`.
- It reuses GenLIP trunk, prefix-LM mask, rotary stack, fused caption loss, and task logic.
- The forward signature is `model(audio=patch_dict, text=text_ids, text_valid=mask, compute_loss=...)`.
- `model.encode_audio(audio_patch_dict, normalize=False)` returns pooled audio features for encoder/probe use.

Position modes:

- Full-height strips (`patch_freq == n_mels`) set `rope_1d=True`; time is broadcast to all three MRoPE axes.
- Multi-row patches (`patch_freq < n_mels`) set `rope_1d=False`; positions use `t=0`, `h=freq`, `w=time`, and text starts after the max spatial index.

`GenLapTask` inherits GenLIP loss behavior but uses `batch["audio"]` as the prefix modality and forwards it as `audio=...`.

## Task Differences

| Model family | Data prefix | Objective | Task | Batch keys | Evaluation route |
| --- | --- | --- | --- | --- | --- |
| NaFlex CLIP | image patches | contrastive image/text | image-text task | `image`, `text` | encode image/text, cosine/logits |
| NaFlexCLAP | audio patches | contrastive audio/text | CLAP task | `audio`, `text` | audio-text zero-shot route |
| GenLIP | image patches | caption LM | `GenLipTask` | `image`, `text`, `text_valid` | generative scoring or frozen-feature probe |
| GenLAP | audio patches | caption LM | `GenLapTask` | `audio`, `text`, `text_valid` | generative scoring/probe-style research workflows |

GenLIP and GenLAP reject gradient accumulation via feature caching (`--accum-freq > 1`) because the contrastive cached-feature path does not apply to a caption LM objective.

## Generative Zero-Shot Scoring

The research `genlip_zeroshot` workflow classifies by conditional caption likelihood:

```text
score(class | image) = mean_templates log P(template(classname) | image)
```

Important behavior:

- Tokenize each class/template caption once.
- For each image, expand the same image patch row across candidate-caption batches.
- Run the model teacher-forced with `compute_loss=False`.
- Read logits at positions `ni - 1 : ni - 1 + Lt`; position `ni - 1 + j` predicts caption token `j`.
- Compute token log-probs, mask padded caption positions with `text_valid`, and length-normalize the caption score.
- Optional PMI subtracts an unconditional/null-image caption likelihood to reduce class-name surface-form bias.

This is a research probe of the LM head, not the paper's primary classification protocol. It is expensive because the current workflow recomputes the image prefix for each candidate-caption batch.

Approximate forward count:

```text
forwards_per_image = ceil(num_classes * templates_per_class / score_batch)
total_forwards = num_images * forwards_per_image
```

Use the bundled safe planner before running a real dataset job:

```bash
python scripts/genlip_scoring_args.py \
  --num-classes 1000 \
  --templates simple \
  --num-images 2000 \
  --score-batch 1024 \
  --seq-len 256 \
  --pmi
```

The helper reports estimated forwards and flags risky settings without importing open_clip, loading ImageNet, or opening checkpoints.

## Attentive Probe Workflow

The attentive-probe workflow is reference-only because it trains a probe and caches features. Use it to explain the expected protocol, not as a safe default command.

Protocol summary:

1. Build a GenLIP model and load a checkpoint.
2. Freeze the backbone.
3. Create a NaFlex eval transform with `aug_cfg={"use_timm": True, "naflex": True}` and a fixed `seq_len`/`patch_size`.
4. Extract last-layer image patch hidden states with `visual.patch_embed`, MRoPE positions, `build_image_attn_mask`, and the trunk.
5. Cache features and `patch_valid` masks for train/val images.
6. Train an `AttentionPoolLatent` head plus classifier on cached features.
7. Evaluate top-1/top-5 from the probe logits.

Caveats:

- Requires checkpoint loading, ImageNet train/val data, timm `AttentionPoolLatent`, and potentially large CPU/GPU cache memory.
- No train-time image augmentation is used after caching because cached features are deterministic.
- Patch padding must be passed to the head so attention ignores invalid patches.

## Caption Stats Workflow

The caption-stats workflow is reference-only because it reads WebDataset shards and uses `tiktoken`. It is useful for planning GenLIP text caps and token budgets.

It reports:

- Caption token percentiles per text field, including BOS/EOS special-token overhead.
- Candidate `--naflex-max-text-tokens` caps such as p90/p95/p99.
- Estimated text and total sequence utilization for target rows/GPU.
- Suggested `--naflex-max-tokens-per-batch = rows * (image_seq_len + text_cap)`.
- Suggested `--length-bucketing` and `--bucket-chunk` values.

For safety, do not run it by default on unknown shard globs. Ask the user for a bounded shard/sample limit first.

## Tiktoken and Variable Text Caveats

GenLIP/GenLAP test configs use `TikTokenTokenizer` with reserved control ids:

- Body token ids come from the tiktoken encoding vocabulary.
- BOS/EOS are added around captions.
- Pad ids are reserved and must not collide with ordinary BPE ids.
- Default tiktoken cleaning is verbatim; optional cleaning modes can canonicalize case/punctuation or replace underscores.

When explaining training failures:

- Missing reserved pad id breaks variable-text padding.
- `text_valid` must match `text != pad_id` for padded batches.
- If captions are truncated/capped, ensure EOS behavior and masking still match tokenizer expectations.
- For compile-heavy runs, `--text-pad-multiple` reduces distinct caption lengths.

## Safe Prompt Responses

If a user asks: "Can I run CLIP cosine zero-shot with a GenLIP checkpoint?"

Answer:

- No for GenLIP as a generative model: it lacks the contrastive dual-tower `encode_text` semantics expected by CLIP cosine zero-shot.
- Use conditional caption scoring for a research probe, or use a frozen-feature attentive probe if the task is classification accuracy.
- Warn about cost: `num_images * ceil(num_classes * templates / score_batch)` forward passes for generative scoring.

If a user asks: "Why does my GenLIP batch have `text_valid`?"

Answer:

- GenLIP trains on variable padded captions and applies LM loss only to valid text tokens.
- `text_valid` masks padded caption tails and is used by prefix-LM attention/loss code.
- Keep valid tokens front-contiguous; the packed-prefix helper assumes valid prefix/text tokens are front-contiguous.
