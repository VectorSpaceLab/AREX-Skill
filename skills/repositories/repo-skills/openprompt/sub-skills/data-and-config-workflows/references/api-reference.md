# OpenPrompt Data And Config API Reference

This reference distills the repo evidence from `openprompt/data_utils/*.py`, `openprompt/config.py`, `openprompt/default_config.py`, and `experiments/cli.py`. It is safe to use without the source checkout.

## Data Payloads

### `InputExample`

OpenPrompt processors return lists of `InputExample` objects. Important fields:

| Field | Meaning |
| --- | --- |
| `guid` | String id for a record; many processors use `<split>-<idx>` or sequential integers. |
| `text_a` | Primary text span or generation source. |
| `text_b` | Optional second span, e.g. hypothesis/question/body. |
| `label` | Classification label id or token id after processor mapping; usually `None` for generation examples. |
| `tgt_text` | Target text for generation workflows such as WebNLG, CSQA, or UltraChat. |
| `meta` | Task-specific structured extras such as entities, choices, spans, candidates, or context turns. |

### `DataProcessor`

The base class supports:

- `labels`, `label_mapping`, and `id2label` properties.
- `get_label_id(label)`, `get_labels()`, and `get_num_labels()`.
- Split helpers: `get_train_examples(data_dir)`, `get_dev_examples(data_dir)`, `get_test_examples(data_dir)`, and `get_unlabeled_examples(data_dir)` delegate to `get_examples(data_dir, split)`.

A processor normally raises `FileNotFoundError` if the expected split file is absent. `openprompt.data_utils.load_dataset` catches missing train/dev/test splits individually but exits if all splits are empty.

## Known Processor Names

`load_dataset(config)` lowercases `config.dataset.name` and looks it up in the merged `PROCESSORS` dictionary. Use the lowercase names below unless a quirk is explicitly noted.

| Family | `dataset.name` values | Processor classes | Notes |
| --- | --- | --- | --- |
| Text classification | `agnews`, `dbpedia`, `amazon`, `imdb`, `sst-2`, `mnli`, `yahoo` | `AgnewsProcessor`, `DBpediaProcessor`, `AmazonProcessor`, `ImdbProcessor`, `SST2Processor`, `MnliProcessor`, `YahooProcessor` | Mostly local files under a dataset directory; labels are mapped to ints inside the processor. |
| FewGLUE local JSONL | `wic`, `rte`, `cb`, `wsc`, `boolq`, `copa`, `multirc`, `record` | `WicProcessor`, `RteProcessor`, `CbProcessor`, `WscProcessor`, `BoolQProcessor`, `CopaProcessor`, `MultiRcProcessor`, `RecordProcessor` | Local FewGLUE processors use `train.jsonl`, `dev32.jsonl`, and `val.jsonl` split names. |
| HuggingFace datasets | `super_glue.multirc`, `super_glue.boolq`, `super_glue.cb`, `super_glue.copa`, `super_glue.rte`, `super_glue.wic`, `super_glue.wsc`, `super_glue.record`, `yahoo_answers_topics` | `Superglue*Processor`, `YahooAnswersTopicsProcessor` | These wrap the `datasets` package and may access network/cache at runtime. Static config inspection must not trigger them. |
| NLI | `snli` | `SNLIProcessor` | Expects local `train.tsv`, `dev.tsv`, and `test.tsv`. |
| Relation classification | `tacred`, `tacrev`, `retacred`, `semeval` | `TACREDProcessor`, `TACREVProcessor`, `ReTACREDProcessor`, `SemEvalProcessor` | TACRED-style processors read JSON; SemEval reads JSONL. |
| Typing | `fewnerd` | `FewNERDProcessor` | Expects `supervised/<split>.txt`. |
| Conditional generation | `webnlg_2017`, `webnlg`, `csqa`, `ultrachat` | `WebNLGProcessor`, `CSQAProcessor`, `UltraChatProcessor` | WebNLG uses JSON split files; CSQA uses CommonsenseQA split file names; UltraChat is a direct JSONL-file processor and is awkward through `load_dataset`. |
| LAMA | source map key is `LAMA` | `LAMAProcessor` | The source `PROCESSORS` key is uppercase while `load_dataset` lowercases names; direct instantiation with tokenizer/base path is usually required unless the caller patches an alias. |

## `load_dataset(config, return_class=True, test=False)`

Runtime behavior:

1. Reads `config.dataset.name` and `config.dataset.path`.
2. Constructs `PROCESSORS[dataset.name.lower()]()`.
3. If `test=False`, tries `get_train_examples(path)` and `get_dev_examples(path)`, logging warnings for missing split files.
4. Always tries `get_test_examples(path)`.
5. If every split is missing or empty, logs a download/path error and exits the process.
6. Returns `(train_dataset, valid_dataset, test_dataset, processor)` when `return_class=True`.

Safety implication: use static validation first. Calling `load_dataset` can exit the process or cause HuggingFace dataset access depending on the processor.

## Few-Shot Sampling API

`FewShotSampler` supports two mutually exclusive train strategies:

- `num_examples_total=N`: sample N mixed examples.
- `num_examples_per_label=N`: sample up to N examples per label; requires `data[0].label`.

Dev sampling:

- `also_sample_dev=True` samples a dev subset as well.
- `num_examples_total_dev` and `num_examples_per_label_dev` are mutually exclusive.
- If `also_sample_dev=True` and no dev-specific number is set, it falls back to the train setting.
- `seed` is passed to the sampler call, not just the config object.

Config pattern from repo examples:

```yaml
learning_setting: few_shot
few_shot:
  parent_config: learning_setting
  few_shot_sampling: sampling_from_train
sampling_from_train:
  parent_config: few_shot_sampling
  num_examples_per_label: 10
  also_sample_dev: true
  num_examples_per_label_dev: 10
  seed: [123, 456, 789]
```

## Config API

### `get_default_config()`

Builds a permissive `yacs.config.CfgNode(new_allowed=True)` with defaults for:

- `environment`, `reproduce`, `plm`, `logging`, `checkpoint`.
- `train`, `dev`, `test`, `task`, `classification`, `generation`, `relation_classification`.
- `dataset`, `dataloader`, `learning_setting`, `zero_shot`, `few_shot`, `sampling_from_train`.
- `template`, `verbalizer`, and selected default prompt branches such as `manual_template`, `manual_verbalizer`, `one2one_verbalizer`, `automatic_verbalizer`, `prefix_tuning_template`, and `mixed_template`.

Because `new_allowed=True`, repo YAMLs can introduce branches such as `soft_template`, `ptuning_template`, `ptr_template`, `proto_verbalizer`, or `contextual_verbalizer` if the runtime prompt loaders know them.

### `get_user_config(config_path, default_config=None)`

- Loads user YAML into a `CfgNode(new_allowed=True)`.
- Merges it over the default config.
- Calls `get_conditional_config`.

### `get_conditional_config(config)`

OpenPrompt's conditional mechanism is selector-based:

1. Top-level nodes with a `parent_config` key are temporarily removed into a deeper-config map.
2. The config is breadth-first scanned.
3. If any scalar string value equals the name of a deeper-config branch, that branch is attached back to the config.

Practical examples:

- `task: generation` selects a `generation:` branch whose `parent_config: task`.
- `template: manual_template` selects `manual_template:`.
- `verbalizer: manual_verbalizer` selects `manual_verbalizer:`.
- `learning_setting: few_shot` selects `few_shot:`; `few_shot.few_shot_sampling: sampling_from_train` selects `sampling_from_train:`.

### CLI argument helpers

`add_cfg_to_argparser` recursively adds `--nested.key` flags for scalar and list config leaves. `update_cfg_with_argparser` writes changed CLI values back to the `CfgNode`. Safe inspection may run argparse/help-like logic, but the training CLI should not be invoked for actual runs unless the user wants model loading and dataset access.

## `experiments/cli.py` Safe Surface

The repo CLI performs, in order:

1. Parse `--config_yaml`, `--resume`, `--test`, and generated nested config flags.
2. Configure logging/checkpoint path.
3. Call `load_dataset`.
4. Load PLM, template, verbalizer, prompt model, dataloaders, and runner.
5. Run training, testing, resume, or zero-shot evaluation.

Only steps equivalent to config parsing and `--help` are safe for this sub-skill. Dataset loading, PLM loading, and runner construction belong to later workflows and may download models, require GPUs, or exit on missing data.
