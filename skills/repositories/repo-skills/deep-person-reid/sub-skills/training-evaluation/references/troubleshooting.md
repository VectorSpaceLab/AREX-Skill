# Training/evaluation troubleshooting

Use this matrix for Torchreid training, evaluation, dataset, and config failures.

## Missing dataset files or failed downloads

**Symptoms**

- Dataset constructor prints download attempts or fails before DataLoader creation.
- `FileNotFoundError`, `RuntimeError`, or messages about missing `bounding_box_train`, `query`, `gallery`, `.mat`, or split files.
- Long hangs while the code tries to download a dataset from an old public link.

**Actions**

1. Do not rely on automatic downloads for production runs; many dataset links are old, gated, or institution-restricted.
2. Verify `data.root` is the parent folder, not the dataset folder itself.
3. Compare the local layout with [data-formats.md](data-formats.md).
4. For `compute_mean_std`, run `../scripts/compute_mean_std.py ROOT KEY --check-only` before `--compute`.
5. For CUHK03, confirm both `cuhk03_release/` and the new-protocol `.mat` files when using the default split.
6. If a previously working CUHK03 tree moved, delete generated CUHK03 split/cache JSON files so paths can be regenerated.

## Invalid dataset key

**Symptoms**

```text
Invalid dataset name. Received "...", but expected to be one of [...]
```

**Actions**

- Check image keys versus video keys. `mars` is video; `market1501` is image.
- Use lowercase Torchreid keys exactly: `dukemtmcreid`, not `duke` or `dukemtmc`.
- Register custom datasets with `register_image_dataset` or `register_video_dataset` before data-manager construction.
- Do not reuse a built-in key for custom registration; the registry rejects duplicates.

## Config opts spelling and list values

**Symptoms**

- YACS merge error for non-existent key.
- A boolean/list override is treated as a string or splits into multiple shell tokens.
- `train.stepsize` type error in scheduler construction.

**Actions**

- Use exact dotted keys from [configuration.md](configuration.md).
- Keep key/value pairs complete: `test.evaluate True`, not just `test.evaluate`.
- Quote list literals in a shell: `train.stepsize '[60]'`, `train.open_layers "['fc', 'classifier']"`.
- `single_step` accepts one integer; if a list is passed in config, Torchreid uses the last element. `multi_step` requires a list.
- Use `../scripts/torchreid_train_eval.py --dry-run --extra-opts ...` to catch common misspellings before runtime.

## Triplet loss and sampler constraints

**Symptoms**

- Assertion from `RandomIdentitySampler`: not enough pids for `batch_size // num_instances`.
- Model forward unpacking errors or missing features in triplet engine.
- Unified config assertion: classifier output not included in graph when `loss.triplet.weight_x == 0` and `train.fixbase_epoch > 0`.

**Actions**

- Build the model with `loss='triplet'` when using triplet engines.
- Use `sampler.train_sampler RandomIdentitySampler` and set `sampler.num_instances` to a feasible value.
- Ensure `train.batch_size` is at least `num_instances` and preferably divisible by `num_instances`.
- If using pure triplet (`loss.triplet.weight_x 0`), keep `train.fixbase_epoch 0`; otherwise include a cross-entropy component with `weight_x > 0`.
- For video triplet training, remember the batch unit is tracklets, not individual frames.

## `visrank` only works in test-only mode

**Symptoms**

```text
ValueError: visrank can be set to True only if test_only=True
```

**Actions**

- In config/CLI mode, set both `test.evaluate True` and `test.visrank True`.
- In API mode, call `engine.run(test_only=True, visrank=True, ...)`.
- Provide a local checkpoint through `model.load_weights` or `load_pretrained_weights` before test-only visualization.
- Visrank outputs go under `data.save_dir` / `save_dir` as `visrank_<dataset>`.

## CUHK03 classic/new split and metric confusion

**Symptoms**

- Results do not match papers using old CUHK03 protocol.
- mAP is reported where old classic protocol expects only CMC.
- Split index errors or missing `.mat` split files.

**Actions**

- Default Torchreid CUHK03 uses the new 767/700 split and detected images.
- Use `cuhk03.classic_split True` for the original 20 splits (`split_id` 0-19).
- Use `cuhk03.labeled_images True` only when evaluating labeled images.
- Use `cuhk03.use_metric_cuhk03 True` for old single-gallery-shot metric comparisons.
- Keep the reporting protocol explicit in experiment notes.

## CPU versus CUDA expectations

**Symptoms**

- Training is extremely slow on CPU.
- `CUDA out of memory`, `torch.cuda.is_available()` false, or device mismatch errors.
- A command silently runs CPU even though GPUs were expected.

**Actions**

- CPU is sufficient for parser, config, import, and tiny API semantics checks. It is not evidence of practical training throughput.
- For runtime training/evaluation, explicitly check CUDA availability and visible devices before promising GPU performance.
- Reduce `train.batch_size`, `test.batch_size`, input size, or `video.seq_len` for memory errors.
- If code uses `nn.DataParallel`, verify the model is moved to CUDA only when CUDA is available.
- Treat CUDA as optional/unverified unless a current hardware smoke check passed.

## Missing weights or resume path

**Symptoms**

- Evaluation runs from random or ImageNet weights instead of the intended checkpoint.
- Resume starts from epoch 0.
- Logs show a skipped or failed file check for `model.load_weights` / `model.resume`.

**Actions**

- Check `model.load_weights` for fine-tuning/evaluation weights and `model.resume` for full training checkpoints with optimizer/scheduler state.
- Confirm the file exists before launching; the unified source flow checks files before loading.
- In test-only evaluation, set `model.pretrained False` if you want to avoid automatic pretrained downloads and rely only on a supplied local checkpoint.
- If the checkpoint architecture differs from `model.name`, route model/key/weight compatibility questions to the feature-extraction sub-skill.

## DataLoader worker issues

**Symptoms**

- Hanging at dataset iteration.
- Worker subprocess errors obscure the original exception.
- Shared-memory or file-descriptor errors.

**Actions**

- Set `data.workers 0` or `--workers 0` for debugging.
- Verify dataset image paths before DataLoader construction in custom datasets.
- Avoid network filesystems for large image reads when possible.
- Reduce `test.batch_size` or `train.batch_size` if memory pressure appears.
- On Windows or notebook contexts, protect executable training code with `if __name__ == '__main__':`.

## Transform and normalization surprises

**Symptoms**

- Invalid transform name has no visible effect.
- Mean/std computation gives unexpected values.

**Actions**

- Valid transform tokens in this workflow: `random_flip`, `random_crop`, `random_patch`, `color_jitter`, `random_erase`.
- Unknown transform tokens are effectively ignored by the transform builder; inspect generated plans carefully.
- Mean/std should be computed with normalization mean `[0,0,0]` and std `[1,1,1]`, as the bundled helper does under `--compute`.
- `random_erase` occurs after normalization; for cross-domain generalization, official examples often use `color_jitter` rather than `random_erase`.

## Log parser reports missing or incomplete logs

**Symptoms**

- `parse_test_results.py` reports split directories with no `test.log*`.
- A split is present but mAP/rank fields are missing.

**Actions**

- Confirm each split directory contains at least one `test.log*` file.
- Use `--log-glob` if logs have a different prefix.
- Use `--strict` to make missing/incomplete splits fail CI-like checks.
- Check that evaluation logs use lines like `mAP: 76.5%` and `Rank-1  : 88.8%`.

## Custom dataset registration issues

**Symptoms**

- Registration works in one script but not another.
- Pids/camids mismatch during evaluation.
- Multi-source training produces surprising person/camera counts.

**Actions**

- Registration is process-local; register custom classes in the same Python process before data-manager construction.
- Keep pids and camids zero-based within each custom dataset.
- Query and gallery must share person-ID scope; train/query/gallery should share camera-ID scope.
- When combining datasets, Torchreid offsets train pids/camids/dataset IDs internally, so do not pre-offset by global dataset order.
- Validate each file path in the custom dataset constructor and fail early with a clear message.
