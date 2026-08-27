# Stanza Training Workflows

## When to read

Read this when planning a Stanza training or evaluation run. It describes safe phases and command shapes; it does not endorse running full training automatically.

## Safe phases

1. **Inspect the task**: identify model family, language/treebank/dataset, desired mode (`train`, `score_dev`, `score_test`, `predict`), and whether pretrained vectors, charlms, transformers, or PEFT are required.
2. **Validate data**: use the data preparation reference and tiny fixtures before full corpora.
3. **Generate commands**: use `scripts/build_training_command.py` to create an explicit command and review every path/flag.
4. **Run help/parser checks**: `python -m <module> --help` and wrapper `--help` are safe.
5. **Run a tiny smoke**: use a tiny corpus and explicit `--save_dir` before large training.
6. **Run full training only with approval**: full models may take hours, write large checkpoints, start W&B, and download resources.

## Direct model command pattern

Direct model modules expose model-specific flags. A direct training command generally looks like:

```bash
python -m stanza.models.tokenizer \
  --mode train \
  --lang en \
  --shorthand en_ewt \
  --txt_file /data/tokenize/en_ewt.train.txt \
  --label_file /data/tokenize/en_ewt.train.toklabels \
  --dev_txt_file /data/tokenize/en_ewt.dev.txt \
  --dev_label_file /data/tokenize/en_ewt.dev.toklabels \
  --save_dir /runs/stanza/tokenize \
  --cpu
```

Change the module and flags for each model family. Always keep output paths task-owned; avoid package default `saved_models/...` paths in automation.

## Wrapper command pattern

Wrapper modules add Stanza's standard treebank iteration and defaults:

```bash
python -m stanza.utils.training.run_tokenizer en_ewt --train --save_dir /runs/stanza/tokenize --no_charlm
python -m stanza.utils.training.run_pos en_ewt --score_dev --save_dir /runs/stanza/pos --extra_args --cpu
```

Use wrappers when:

- you want Stanza's per-language default charlm/pretrain selection;
- you are iterating over several UD treebanks;
- you need `all_ud` / `ud_all` expansion;
- you want model-name collision checks before retraining.

Prefer direct modules when:

- you need exact low-level flags;
- you are running a synthetic/tiny fixture;
- wrapper defaults would trigger downloads or unwanted charlms.

## Model-family notes

### Tokenizer and MWT

- Tokenizer training needs plain text and tokenization labels.
- `--mwt_json_file` carries MWT expansion supervision.
- Use `--skip_newline` for languages or corpora where newlines should not mark sentence structure.
- Some languages use dictionary features; confirm the external dictionary naming convention before training.

### POS, lemma, and dependency parsing

- Use CoNLL-U train/eval files.
- POS and depparse often need pretrains and optional charlms.
- Transformers and PEFT require optional packages and can change memory behavior.
- Dependency parsing may support silver data; keep silver weights and source provenance explicit.

### NER

- Confirm the tag scheme before training.
- `--scheme` controls decoding output; `--train_scheme` can override the training set scheme.
- Use explicit pretrain files when available to avoid surprise downloads.
- For multi-tag NER, validate column counts and tagset selection.

### Constituency and classifier/sentiment

- Constituency workflows often depend on tree converters and optional retagging.
- Classifier/sentiment workflows need text/class labels and may use constituency or pretrain features.
- Keep generated models and evaluation outputs in per-run directories.

### Coref and charlm

- Coref workflows are experiment/config driven; keep config, weights, and split paths explicit.
- Character language models are dependencies for several model families; treat them as separate training artifacts.

## Logging and reproducibility

- Record package version, command, data hashes/counts, seed, device, and output paths.
- Set seeds when exposed; do not rely on wrapper-generated random seeds for reproducibility unless intentionally using `--no_seed` behavior.
- Disable W&B unless credentials and logging scope are explicit.
- Keep dev/test evaluation separate from training output.

## Stop conditions

Stop and ask for a narrower plan when:

- required data roots are missing or ambiguous;
- a command would download large models/vectors;
- CUDA/transformer/PEFT dependencies are required but unavailable;
- a run would overwrite existing model checkpoints;
- full training cost is not approved.
