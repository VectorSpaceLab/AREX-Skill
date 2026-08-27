# Troubleshooting: Training and Generation

Use this guide after a dry-run report or native run points to a specific runner/backend/checkpoint/generation failure.

## CUDA or device placement failures

Symptoms:

- `AssertionError: Torch not compiled with CUDA enabled`
- `RuntimeError: CUDA error: invalid device ordinal`
- `RuntimeError: module must have its parameters and buffers on device cuda:0`
- Hang or OOM after DataParallel/model-parallel setup

Checks:

```bash
python scripts/inspect_training_config.py \
  --config-yaml path/to/config.yaml --probe-torch
```

Fixes:

- Set `environment.num_gpus: 0` for CPU-only inspection/debug runs.
- If using CUDA, install a CUDA-compatible PyTorch build and verify `torch.cuda.is_available()`.
- Keep `environment.local_rank` within the visible device range.
- Avoid setting both `model_parallel: True` and `num_gpus > 1`; `model_to_device` handles model parallel first and does not combine it with DataParallel.
- Remember that `CUDA_VISIBLE_DEVICES` already set in the shell overrides the config's attempt to set `cuda_visible_devices`.

## Missing model cache or network downloads

Symptoms:

- Hugging Face `OSError` about missing `config.json`, tokenizer, or model weights.
- Long download attempts when running tutorials or `experiments/cli.py`.
- LM-BFF loads more than one large model.

Fixes:

- Pre-download or point `plm.model_path` to a local model directory.
- For LM-BFF, also check `template_generator.plm.model_path`.
- For tiny logic debugging, create a separate small config rather than editing benchmark configs in place.
- Do not treat the dry-run helper as a model-cache verifier; it intentionally does not load PLMs.

## Dataset or prompt asset path failures

Symptoms:

- Dataset processor cannot find train/dev/test files.
- `FileNotFoundError` for `manual_template.file_path`, `manual_verbalizer.file_path`, `template_generator.template.file_path`, or prompt assets used by tutorials.
- Few-shot sampling fails because labels/splits are absent.

Fixes:

- Inspect active paths in the dry-run report.
- Resolve relative paths from the project root or the config's chosen base directory when using copied repository configs.
- Route dataset layout and config-merge questions to `../data-and-config-workflows/`.
- Route template/verbalizer grammar and asset format questions to `../template-verbalizer-design/`.

## Checkpoint load/save surprises

Symptoms:

- `Checkpoint .../last.ckpt not found` during resume.
- Test exits or fails because `best.ckpt` is missing.
- No TensorBoard or checkpoints were written.
- `checkpoint.save_latest: False` did not stop `last.ckpt` writes.

Facts from `BaseRunner`:

- Checkpoints live at `{config.logging.path}/checkpoints/{last,best}.ckpt`.
- `--resume RUN_DIR` loads `last.ckpt`; absent `last` falls back to training from scratch.
- `--test RUN_DIR` loads `best.ckpt`; absent `best` is fatal for test mode.
- `train.clean: True` disables TensorBoard scalar writes and checkpoint saving.
- `checkpoint.save_latest` and `checkpoint.save_best` are config fields but are not enforced by `BaseRunner.save_checkpoint()`.

Fixes:

- Re-run without `train.clean: True` if you need resume/test artifacts.
- Supply the exact logging run directory, not the `checkpoints/` subdirectory.
- If loading a checkpoint from another config, ensure class count, template/verbalizer, PLM architecture, and prompt parameters match.

## Generation length, EOS, and teacher-forcing mistakes

Symptoms:

- Generated text never stops or is truncated.
- Generation output is empty or only repeats the prompt.
- Training loss does not decrease for generation.
- `AssertionError: The generation start from different position in a batch.`

Fixes:

- For training generation, make sure examples contain `tgt_text` and the train dataloader uses `teacher_forcing=True`.
- Use `predict_eos_token=True` when the template or tokenizer wrapper needs an explicit end token to stop generation.
- Distinguish `dataloader.decoder_max_length` from `generation.max_length`: decoder length truncates target/decoder inputs; generation max length controls inference and includes input tokens in native transformers behavior.
- Prefer `generation.max_new_tokens` when the prompt length varies and the installed transformers version supports it.
- For encoder-decoder generation, batches must have aligned generation start positions because `PromptForGeneration.generate()` asserts a common start index.
- For decoder-only PLMs, OpenPrompt generates one instance at a time; expect slower evaluation.

## Classification metric or label mapping issues

Symptoms:

- Metric errors for hierarchical labels.
- Mismatched predictions/labels length.
- Unexpected first metric drives checkpoint choice.

Fixes:

- The first metric in `classification.metric` is the validation score returned by `inference_epoch()` and used for best-checkpoint comparison.
- Pass `id2label=Processor.id2label` when constructing `ClassificationRunner` manually if metrics need label names.
- Set `dataset.label_path_sep` for hierarchical labels.
- Confirm the dataset processor's labels align with the verbalizer classes.

## Few-shot sampling failures

Symptoms:

- `ValueError: use few_shot setting but config.few_shot.few_shot_sampling is not specified`.
- Some labels disappear in sampled train/dev splits.
- Per-seed directories are missing or uneven.

Fixes:

- Set `few_shot.few_shot_sampling: sampling_from_train`.
- Ensure `sampling_from_train.num_examples_per_label` and `num_examples_per_label_dev` are feasible for every label.
- Keep `sampling_from_train.seed` as a list even for one seed.
- Inspect each `seed-*` directory separately; `experiments/cli.py` averages seed results after individual runs.

## Zero-shot branch does not run

Symptoms:

- Config appears zero-shot, but the CLI does nothing after dataset loading or falls through unexpectedly.

Fix:

- Use `learning_setting: zero_shot` with an underscore. The default config comment mentions `zero-shot`, but `experiments/cli.py` checks `zero_shot`.

## LM-BFF failures

Symptoms:

- `ValueError: no verbalizer for template generation provided!`
- `ValueError: no template for verbalizer generation provided...`
- OOM or slow candidate search.
- Missing `t5-large` or `roberta-large` caches.

Fixes:

- For `classification.auto_t: True`, provide a manual verbalizer; any provided template is ignored.
- For `classification.auto_v: True`, provide a template; any provided verbalizer is ignored.
- Reduce `template_generator.beam_width`, candidate counts, model size, and dataset size for debugging.
- Confirm both classifier PLM and template-generator PLM caches exist.

## ProtoVerb failures

Symptoms:

- Attribute errors inside `train_proto`.
- Prototypes do not update at the expected time.
- The runner ignores `train_verbalizer`.

Fixes:

- Use the repository spelling `train.train_verblizer`.
- Choose one of the native timings: non-`post` pretraining, `alternate`, or `post`.
- Verify the active `proto_verbalizer` config and prompt asset file before fitting.
- Avoid substituting a standard manual verbalizer while keeping `verbalizer: proto_verbalizer`.

## Dependency/version drift

Symptoms:

- Import errors for `transformers.AdamW` or generation APIs.
- `datasets`, `rouge`, `sklearn`, or `scipy` import failures during root import or metrics.
- `experiments/cli.py --help` fails before training.

Fixes:

- Prefer a Python 3.8-era environment with a transformers version compatible with this OpenPrompt source.
- Run `python experiments/cli.py --help` as a no-training import gate.
- For root import, ensure torch, transformers, yacs, dill, tensorboardX, nltk, rouge, scipy, and scikit-learn are installed as required by the prepared environment plan.
