# Triple-extraction data and configuration reference

Use this reference when a DeepKE triple-extraction task fails because filenames, labels, model paths, or generated output formats do not match the selected workflow.

## Workflow data layouts

### PRGC

Common files under the selected data directory:

| File | Purpose | Checks |
| --- | --- | --- |
| `rel2id.json` | Relation-label inventory and integer ids | Every relation in train/dev/test triples should exist here. Preserve id stability when comparing runs. |
| `train_triples.json` | Training split | Each record should contain text/sentence plus gold triples in the schema expected by the PRGC loader. |
| `val_triples.json` | Validation split | Avoid accidentally naming it `valid_triples.json` unless the config is changed accordingly. |
| `test_triples.json` | Test split | Use only for evaluation/prediction, not prompt examples or training leakage. |

Important config fields include data directory, pretrained BERT path, relation vocabulary path, batch size, learning rate, maximum sequence length, training epochs, output model directory, log directory, and random seed.

### PURE

Common files under a dataset JSON directory:

| File | Purpose | Checks |
| --- | --- | --- |
| `train.json` | Training examples | Entity spans and relations must use the PURE loader's expected JSON schema. |
| `dev.json` | Validation examples | The source docs use `dev`, not always `valid`. |
| `test.json` | Test examples | Relation prediction output path is configured separately. |

PURE has two families of configuration knobs:

- Entity model knobs: train/eval flags, BERT model name/path, context window, output directory, entity prediction filenames, batch size, learning rates, and epochs.
- Relation model knobs: train file, prediction file, output directory, max sequence length, eval batch size, learning rate, no-cuda/single-card flags, and relation model path.

Keep entity and relation base model paths consistent unless the user explicitly designed a heterogeneous experiment.

### ASP

Common files under a dataset-specific ASP data directory:

| File | Purpose | Checks |
| --- | --- | --- |
| `train.json` | Training data | Must match the configured dataset name. |
| `dev.json` | Development data | Used for selecting/validating saved suffixes. |
| `test.json` | Test data | Evaluation expects a saved suffix from a training run. |

ASP native commands often accept a `config_name` and `gpu_id`. The config selects the dataset folder, PLM, output directory, and decoding settings. The saved suffix used by evaluation should be copied exactly from the training output directory; do not invent it from timestamps in docs.

### MT5 / CCKS

Common files:

| File | Purpose | Checks |
| --- | --- | --- |
| `train.json` | Training data for generative fine-tuning | The native script may internally split this if no validation file is provided. |
| `valid.json` | Competition-style prediction input in the source docs | Despite the name, this may be the test/input file for submission. |
| `test_preds.json` | Model-generated predictions, one JSON object per line | Each line should contain the configured prediction field, usually `output`. |
| `valid_result.json` or `.jsonl` | Converted result with `kg` triples | Should have the same number of rows as the source input unless explicitly using a subset. |

The bundled `convert_mt5_predictions.py` reads source records and prediction records line by line, copies/cleans the generated output string, and writes `kg` as a list of `[head, relation, tail]` triples.

## Triple text parsing expectations

The source MT5/LLMICL helpers parse triple-like substrings such as:

```text
输入中包含的关系三元组是：(Alice, works_for, Acme),(Bob, lives_in, Paris)
```

into:

```json
[["Alice", "works_for", "Acme"], ["Bob", "lives_in", "Paris"]]
```

This format is simple and intentionally limited:

- It treats commas as field delimiters, so unescaped commas inside entity names or relation labels are ambiguous.
- It expects parentheses around each triple.
- It skips incomplete triples rather than fabricating missing fields.
- It does not canonicalize aliases, normalize relation labels, or validate against `rel2id.json`.

If the model emits JSON, XML, semicolons, Chinese punctuation, or natural-language explanations instead, first decide whether to change the prompt/training format or write a task-specific parser.

## Path and config discipline

- Prefer absolute or clearly resolved local model/checkpoint paths in native DeepKE config files, but do not publish private paths in reusable skill docs.
- Keep data, log, and output directories separate for each experiment.
- Do not reuse MT5 `output_dir`/`logging_dir` across runs unless overwriting is deliberate.
- For Hydra configs, record each override and verify the active resolved config before a long run.
- For DeepSpeed configs, verify GPU count, bf16/fp16 support, batch size, gradient accumulation, ZeRO stage, and checkpointing settings before launch.

## Minimal validation before evaluation

1. Count rows in all split/prediction files.
2. Check every gold or predicted relation label against the intended inventory.
3. Check whether expected keys exist in JSON/JSONL records before passing them to DeepKE loaders.
4. For staged workflows, evaluate entity spans separately from relation predictions.
5. For generative workflows, inspect raw `output` strings, parsed `kg`, and empty-`kg` examples.
6. Save the exact model/checkpoint path and config values used to produce each prediction file.
