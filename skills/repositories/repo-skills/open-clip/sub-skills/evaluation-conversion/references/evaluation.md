# Evaluation Flows

This reference covers contrastive zero-shot evaluation and where to route model families that do not fit the ImageNet text-classifier path.

## Zero-Shot Classifier Construction

Use `open_clip.build_zero_shot_classifier` for contrastive image/text models and compatible `TrainingTask` wrappers:

```python
classifier = open_clip.build_zero_shot_classifier(
    model,
    tokenizer=tokenizer,
    classnames=["tabby cat", "golden retriever"],
    templates=["a photo of a {}.", "a blurry photo of a {}."],
    num_classes_per_batch=10,
    device="cuda",
    use_tqdm=True,
)
```

Important contracts:

- `classnames` and `templates` must be non-empty sequences.
- Template entries may be format strings containing `{}` or callables that accept a class name.
- The tokenizer output is moved to `device` before the text forward pass.
- Model output may be a dict with `text_features`, a tuple/list whose second item is text features, or a tensor.
- Per-template text features are averaged per class and L2-normalized again; the return shape is `[embed_dim, num_classes]`.
- `num_classes_per_batch=None` processes all classes at once; otherwise classes are batched to reduce text-forward memory.

For a no-download sanity check, run `scripts/zero_shot_classifier_smoke.py` from this sub-skill.

## ImageNet Zero-Shot During Training/Eval

The training helper `open_clip_train.zero_shot.zero_shot_eval(model_or_task, data, epoch, args, tokenizer=None)` only runs when at least one of these data keys exists:

- `imagenet-val`
- `imagenet-v2`

It returns `{}` when:

- Neither ImageNet key is present.
- `args.zeroshot_frequency == 0`.
- The current epoch is not on the zero-shot schedule and is not the final epoch.
- The model has an image tower but no `encode_text` method, which is the contrastive text tower required for the classifier path.

It raises for audio-only/non-image models because ImageNet zero-shot is image-only and requires an image model with `visual` and `encode_image`.

## Wrapped, Compiled, Task, and FSDP Behavior

OpenCLIP uses `get_model_from_task` to check capabilities through wrappers:

- `.module` wrappers from DDP-like modules are unwrapped for capability checks.
- `._orig_mod` wrappers from `torch.compile` are unwrapped for capability checks.
- `TrainingTask.trainable_module` is unwrapped for raw model capability checks.

The actual classifier and evaluation calls still receive the original `model_or_task`, which is important for task-owned eval behavior, EMA preference, FSDP hooks, and custom batch preparation.

For FSDP zero-shot:

- All ranks must call `build_zero_shot_classifier` because text/image forwards can be collective.
- Rank 0 iterates real ImageNet batches and broadcasts a continue/stop signal.
- Non-rank-0 workers use `task.create_dummy_batch(batch_size=1, device=..., dtype=...)` when available.
- If `args.use_naflex` is true and there is no task dummy-batch interface, evaluation raises because NaFlex image dicts cannot be safely synthesized from a plain image size alone.

## NaFlex Image Batches

`run_zero_shot_classifier` supports standard image tensors and NaFlex image dicts. NaFlex image dicts should include at least:

- `patches`
- `patch_coord`
- `patch_valid`
- `seq_len` when required by the model/data path

The helper infers batch size from `images["patches"].shape[0]` for NaFlex dicts and from `images.size(0)` for ordinary image tensors.

## Routing by Model Family

- Contrastive image/text CLIP, SigLIP, CoCa-compatible contrastive eval: stay in this sub-skill.
- CLAP and NaFlexClap Hugging Face audio zero-shot: route dataset setup, audio transforms, and audio classifier behavior to `../audio-clap/SKILL.md`.
- GenLIP/GenLAP generative classification or caption-scoring alternatives: route to `../naflex-generative/SKILL.md`.
- Embedding generation before retrieval or custom classifier logits: route to `../model-inference/SKILL.md`.

## Minimal Manual Flow

1. Create/load the model and tokenizer using the model-inference sub-skill.
2. Put the model or task in eval mode when applicable.
3. Build class weights with `build_zero_shot_classifier` using task/model and tokenizer.
4. Encode images to normalized features or call `run_zero_shot_classifier` with a dataloader that yields `(images, target)`.
5. Compute logits as `100.0 * image_features @ classifier` for manual inference or let `run_zero_shot_classifier` produce top-1/top-5.

Do not use this ImageNet path for audio-only or generative-only requests; pick the sibling route before writing code.
