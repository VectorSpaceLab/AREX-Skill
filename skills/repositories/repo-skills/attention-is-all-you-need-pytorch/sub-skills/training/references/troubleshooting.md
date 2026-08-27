# Training Troubleshooting

Use these symptoms to recover from common `train.py` setup failures without reopening the source repository.

## Missing `-output_dir`

Symptom:

```text
No experiment result will be saved.
RuntimeError: No active exception to reraise
```

Cause: `train.py` prints the message and executes a bare `raise` when `-output_dir` is missing.

Recovery:

- Add `-output_dir OUTPUT_DIR` to every command.
- Prefer `scripts/build_training_command.py`, which requires or supplies an output directory and never emits a command without one.
- If the parent directory may not be writable, create/check it before starting a long run.

## Stale README `-log` flag

Symptom:

```text
train.py: error: unrecognized arguments: -log ...
```

Cause: README examples include a historical `-log` flag, but the current parser has no such option.

Recovery: remove `-log` and rely on `OUTPUT_DIR/train.log` and `OUTPUT_DIR/valid.log`.

## Warmup warning with small batches

Symptom:

```text
[Warning] The warmup steps may be not enough.
(sz_b, warmup) = (2048, 4000) is the official setting.
Using smaller batch w/o longer warmup may cause the warmup stage ends with only little data trained.
```

Cause: `batch_size < 2048` and `n_warmup_steps <= 4000`.

Recovery:

- For real training with `-b 256`, consider a larger warmup such as the README's `128000`.
- For a short CPU sanity run, the warning can be accepted if no quality claim is being made.
- Record the chosen warmup in the run name/output directory so later checkpoint comparisons are interpretable.

## Embedding sharing assertion

Symptom in normal pickle mode:

```text
AssertionError: To sharing word embedding the src/trg word2idx table shall be the same.
```

Cause: `-embs_share_weight` was set, but `vocab['src'].vocab.stoi` differs from `vocab['trg'].vocab.stoi` in the all-in-one pickle.

Recovery:

- If source and target should share a vocabulary, regenerate the pickle through the shared-vocabulary preprocessing path.
- If vocabularies differ intentionally, remove `-embs_share_weight` for normal pickle training.
- Keep `-proj_share_weight` if you only need target embedding/output projection sharing; it does not require source and target vocabularies to match.
- For BPE-prefix mode, `-embs_share_weight` is mandatory; use a shared BPE vocabulary pickle.

## BPE branch data errors

Symptoms include `TypeError` from opening `None`, file-not-found errors for `.src`/`.trg`, or torchtext `TranslationDataset` failures.

Likely causes:

- `-train_path` and `-val_path` were supplied but `-data_pkl` was omitted.
- Prefixes point to full filenames instead of the stem before `.src`/`.trg`.
- One of `TRAIN_PREFIX.src`, `TRAIN_PREFIX.trg`, `VAL_PREFIX.src`, or `VAL_PREFIX.trg` is missing.
- The BPE vocabulary pickle lacks `settings.max_len` or a shared `vocab` field.

Recovery:

- Use `scripts/build_training_command.py --check-paths` before long training.
- Pass prefix stems, not individual `.src` or `.trg` files.
- Treat BPE as a WIP path and validate a tiny fixture before a production run.

## CUDA and `-no_cuda`

Symptoms include CUDA initialization errors, `Torch not compiled with CUDA enabled`, `CUDA error: invalid device ordinal`, or failures immediately after the model/data move to device.

Cause: by default `train.py` sets `opt.cuda = not opt.no_cuda` and chooses `torch.device('cuda')` whenever `-no_cuda` is absent. It does not first check that CUDA is usable.

Recovery:

- Add `-no_cuda` on CPU-only hosts or for safe dry runs.
- For GPU runs, check `torch.cuda.is_available()` and device visibility first.
- When adapting the shell launcher, set `CUDA_VISIBLE_DEVICES` deliberately. An empty or wrong value can hide GPUs or select an invalid device.

## Legacy torchtext dependency

Symptoms:

```text
ModuleNotFoundError: No module named 'torchtext'
AttributeError: module 'torchtext.data' has no attribute 'Field'
ImportError: cannot import name 'Field' from 'torchtext.data'
```

Cause: the repo uses the legacy torchtext API (`Field`, `Dataset`, `BucketIterator`, `TranslationDataset`). Modern torchtext releases removed or moved these APIs.

Recovery:

- Use a legacy-compatible environment with torchtext 0.6.x and compatible PyTorch.
- Keep pickles tied to the same torchtext/dill era that produced them when possible.
- If you only need architecture checks, use the model-architecture sub-skill instead of importing `train.py`.

## Optional TensorBoard import

Symptom:

```text
ModuleNotFoundError: No module named 'tensorboard'
```

Cause: `-use_tb` imports `torch.utils.tensorboard.SummaryWriter` at training start.

Recovery:

- Remove `-use_tb` if TensorBoard curves are not required.
- Or install a TensorBoard package compatible with the PyTorch runtime.
- TensorBoard files are written under `OUTPUT_DIR/tensorboard`.

## Checkpoint not where expected

Symptoms: `model.chkpt` is missing under the output directory, or multiple `model_accu_*.chkpt` files appear in the current working directory.

Causes and recovery:

- With `-save_mode best`, `OUTPUT_DIR/model.chkpt` is written only when validation loss improves. It should update during the first epoch if validation completes.
- With `-save_mode all`, checkpoints are written to the process working directory, not `OUTPUT_DIR`. Use this mode only from a controlled directory or prefer `best`.
- The training script has no resume flag. Continuing training from a checkpoint requires custom code outside this sub-skill.

## Empty or malformed target batches

Symptoms include divide-by-zero in epoch metrics or index errors during loss.

Likely causes:

- Target examples are empty or all padding after filtering.
- Vocabulary indices in examples exceed the model target vocabulary size.
- BPE filtering removed too much data because sequence lengths exceeded `settings.max_len`.

Recovery:

- Inspect the preprocessed pickle or BPE prefix files with the data-preparation sub-skill.
- Ensure every target sequence has at least one non-pad token after `patch_trg` shifts input and gold positions.
- Confirm padding token `'<blank>'` exists in the relevant vocabularies.
