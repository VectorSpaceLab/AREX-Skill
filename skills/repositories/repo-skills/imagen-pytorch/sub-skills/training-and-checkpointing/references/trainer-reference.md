# ImagenTrainer Reference

This reference distills the trainer behavior a future agent needs without reopening the source checkout. It covers `imagen-pytorch` 2.1.0 public trainer surfaces and the tiny repo test intent.

## Constructor Contract

Use `ImagenTrainer` around an `Imagen` or `ElucidatedImagen` model.

| Argument / property | Operating detail |
| --- | --- |
| `imagen` | Primary supported input. Must be an `Imagen` or `ElucidatedImagen` instance. Prefer instances created by `ImagenConfig` or `ElucidatedImagenConfig` when the checkpoint must later be commandable. |
| `imagen_checkpoint_path` | Present in the signature and participates in the “either image instance or checkpoint path” assertion. In 2.1.0, the implementation still expects `imagen` to be an actual model immediately afterward, so use `load_imagen_from_checkpoint(path)` plus `ImagenTrainer(imagen=...)`, or reconstruct the model and call `trainer.load(path)`. |
| `use_ema` | Defaults to `True`; EMA modules are used only on the main process. `update()` refreshes EMA; `sample()` uses EMA unless `use_non_ema=True`. |
| `lr`, `eps`, `warmup_steps`, `cosine_decay_max_steps` | Accept scalars or per-unet tuples. One optimizer, scaler, scheduler, and warmup scheduler is stored per unet. |
| `max_grad_norm` | If set, `update()` clips the currently trained unet before optimizer step. |
| `only_train_unet_number` | Pins the trainer to one one-based unet number. This is the safest pattern for cascade training scripts and distributed launch jobs. |
| `fp16`, `precision` | Mutually exclusive. `fp16=True` maps Accelerate mixed precision to `fp16`; `precision` can be `"fp16"`, `"bf16"`, or `"no"`. |
| `split_batches` and `accelerate_*` kwargs | Forwarded into `Accelerator`. The trainer installs distributed DDP kwargs with `find_unused_parameters=True`. |
| `dl_tuple_output_keywords_names` | Default tuple mapping is `('images', 'text_embeds', 'text_masks', 'cond_images')`. A dataloader item is cast to a tuple and zipped to these names before `forward()`. |
| `split_valid_from_train`, `split_valid_fraction`, `split_random_seed` | If enabled, `add_train_dataset` randomly splits the dataset and automatically registers a validation dataset. |
| `checkpoint_path`, `checkpoint_every` | Must be set together or both omitted. When set, the constructor loads the newest checkpoint from the folder if present, and `update()` saves every `checkpoint_every` total steps. |
| `checkpoint_fs`, `fs_kwargs`, `max_checkpoints_keep` | Configure fsspec storage and checkpoint retention. Local paths are safest; test cloud filesystems before relying on them. |

`ImagenTrainer.locked` prevents multiple distributed trainers in the same process. Do not bypass it in real multi-process training. Resetting it is acceptable only in local smoke scripts that construct multiple trainers sequentially outside distributed launch.

## Lifecycle Ordering

1. **Create or load model**: build architecture through sibling model/config guidance. For CLI-compatible checkpoints, create the model through config classes so the model carries `_config`.
2. **Instantiate trainer**: pass the model and trainer options. Use one process/script per cascade unet when training a multi-unet model.
3. **Register data before preparation**: call `add_train_dataset`, `add_train_dataloader`, `add_valid_dataset`, or `add_valid_dataloader` before the first `train_step`, `valid_step`, manual `prepare()`, or manual `forward()` that triggers wrapping.
4. **Train**:
   - Dataloader-owned path: `loss = trainer.train_step(unet_number=n, max_batch_size=m)`. This lazily prepares, creates the train iterator, runs forward/backward over chunks, then calls `update()`.
   - Manual tensor path: `loss = trainer(images, text_embeds=..., text_masks=..., unet_number=n, max_batch_size=m)` followed by `trainer.update(unet_number=n)`. For unconditional models, omit text inputs.
5. **Validate**: `valid_step(unet_number=n, max_batch_size=m, use_ema_unets=False)` uses `torch.no_grad()` and eval mode. It requires a validation dataloader.
6. **Sample**: `trainer.sample(...)` swaps in EMA unets by default, warns about untrained non-null unets, and delegates image/video arguments to the model. Use `use_non_ema=True` to sample training weights.
7. **Save/resume**: use `trainer.save(path)` and `trainer.load(path)` or managed checkpoint folders. See [checkpointing](checkpointing.md).

## Dataset and Dataloader Inputs

`add_train_dataset(ds, batch_size=..., **dl_kwargs)` wraps `ds` in `torch.utils.data.DataLoader` and accepts standard dataloader kwargs such as `shuffle`, `num_workers`, `pin_memory`, and `collate_fn`.

`add_train_dataloader(dl)` uses a prepared dataloader directly. In both cases, there can be only one train dataloader and only one validation dataloader per trainer.

Default dataloader item mappings:

| Returned item | Model inputs produced |
| --- | --- |
| `images` tensor | `images=...` for unconditional training. |
| `(images, text_embeds)` | `images=...`, `text_embeds=...` for text-conditioned training without T5 calls. |
| `(images, text_embeds, text_masks)` | Adds explicit padding mask. |
| `(images, text_embeds, text_masks, cond_images)` | Adds conditioning images for models configured to accept them. |

For text strings, folder schemas, Hugging Face collators, URL images, and T5 cache behavior, route to [data-and-text-conditioning](../../data-and-text-conditioning/SKILL.md).

## Gradient Accumulation with `max_batch_size`

`max_batch_size` controls memory use, not dataloader batch size. The trainer splits tensors and iterable batch items along the first dimension, weights each chunk loss by chunk fraction, calls backward on each chunk, and performs one optimizer/EMA/scheduler update at the end.

Practical rules:

- Set dataloader `batch_size` to the desired effective batch and `max_batch_size` to the largest microbatch that fits memory.
- At least one positional or keyword argument to `forward()` must be a tensor so the trainer can infer batch size.
- Keep tuple/list text inputs batch-aligned with image tensors; chunking splits iterables by batch index.
- `trainer.sample(..., max_batch_size=m)` also chunks sampling requests; unconditional sampling needs a `batch_size` keyword.

## One Unet at a Time

Unet numbers are one-based. Single-unet trainers can omit `unet_number`; multi-unet trainers must pass it.

The trainer intentionally restricts a process to one cascade stage once training begins. If `only_train_unet_number=1` was used, trying to train unet 2 in the same trainer will assert. Save a checkpoint, start a fresh process/trainer for the next unet, load the checkpoint, and continue with `only_train_unet_number=2` or `train_step(unet_number=2)`.

## EMA and Sampling

- EMA modules are created per unet when `use_ema=True` and the trainer is on the main process.
- `update()` updates only the EMA module for the currently trained unet.
- `sample()` uses the EMA unets by default, moving EMA modules as needed and restoring training unets afterward.
- Use `sample(use_non_ema=True, ...)` when intentionally testing raw training weights.
- For untrained cascade stages, sampling will print warnings; pass model-level `stop_at_unet_number` when previewing only trained early stages.

## Accelerate / Multi-GPU Pattern

1. Put trainer construction, dataloader registration, loop, validation, sampling, and saving in a training script that accepts a unet number argument.
2. Run `accelerate config` once for the working launch environment.
3. Launch with `accelerate launch train.py --unet 1` rather than plain `python` when distributed training is desired.
4. Use `trainer.is_main` for global logging, samples, and non-local filesystem writes. For local checkpoint folders the trainer uses local-main checkpointing.
5. Do not create multiple `ImagenTrainer` instances in the same distributed process. Start a fresh launch for another unet.

## Minimal Dataloader Loop Skeleton

```python
trainer.add_train_dataset(dataset, batch_size=effective_batch_size, shuffle=True)
for step in range(total_steps):
    loss = trainer.train_step(unet_number=unet_number, max_batch_size=microbatch_size)
    if should_validate:
        valid_loss = trainer.valid_step(unet_number=unet_number, max_batch_size=microbatch_size)
    if trainer.is_main and should_sample:
        sample = trainer.sample(batch_size=1, stop_at_unet_number=unet_number)
    if trainer.is_main and should_save:
        trainer.save(checkpoint_file)
```

Use [scripts/tiny_trainer_smoke.py](../scripts/tiny_trainer_smoke.py) to test the smallest safe control flow without network downloads or long loops.
