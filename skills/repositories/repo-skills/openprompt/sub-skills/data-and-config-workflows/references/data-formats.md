# OpenPrompt Dataset And Config Data Formats

OpenPrompt processors turn task-specific files into `InputExample` lists. This reference documents expected local layouts and remote/cache caveats so configs can be validated without starting training.

## General Dataset Path Rules

- `config.dataset.name` selects a processor; in `load_dataset`, the name is lowercased before lookup.
- `config.dataset.path` is passed to processor split methods as `data_dir` for local processors.
- Missing individual split files are logged as warnings, but if all splits are absent `load_dataset` logs a dataset-empty error and exits the process.
- HuggingFace processors may ignore `dataset.path` and call the `datasets` package; that can use network/cache and should not be triggered by static validation.
- Some repo examples use checkout-relative paths such as `datasets/...` or `scripts/...`; replace those with paths owned by the user's project or pass an explicit base directory to the inspector.

## Common `InputExample` Conventions

| Workflow | Required fields | Optional fields |
| --- | --- | --- |
| Classification | `guid`, `text_a`, `label` | `text_b`, `meta`, `idx` |
| Pair classification / NLI / QA | `guid`, `text_a`, `text_b`, `label` | `meta`, `idx` |
| Relation classification | `guid`, `text_a`, `label`, `meta.head`, `meta.tail` | entity positions, relation metadata |
| Typing | `guid`, `text_a`, `label`, `meta.entity` | span/type metadata |
| Conditional generation | `guid`, `text_a`, `tgt_text` | `meta.choices`, context lists |

## Text Classification Processors

| Name | Expected local files | Parsed fields | Notes |
| --- | --- | --- | --- |
| `agnews` | `<data_dir>/train.csv`, `<data_dir>/test.csv`; dev optional only if supplied | CSV rows: label, headline, body -> `text_a`, `text_b`, `label=int(label)-1` | Labels: World, Sports, Business, Tech. |
| `mnli` | `<data_dir>/<split>.csv` | CSV rows: label, headline, body | Source marks TODO; verify fixtures carefully. |
| `yahoo` | `<data_dir>/<split>.csv` | label, question title, question body, answer -> `text_a`, `text_b` | 10 topic labels. |
| `dbpedia` | `<data_dir>/<split>.txt` and `<data_dir>/<split>_labels.txt` | first sentence -> `text_a`; remaining text -> `text_b`; labels from sidecar file | Sidecar label line count must match text lines. |
| `imdb` | `<data_dir>/<split>.txt` and `<data_dir>/<split>_labels.txt` | line -> `text_a`; label from sidecar file | Binary labels. |
| `amazon` | `<data_dir>/<split>.txt` and `<data_dir>/<split>_labels.txt` | line -> `text_a`; label from sidecar file | Large dataset; avoid full native test unless explicitly available. |
| `sst-2` | `<data_dir>/train.tsv`, `<data_dir>/dev.tsv`, `<data_dir>/test.tsv` | TSV header then `sentence<TAB>label`; label mapped through `['0','1']` | Common few-shot subdirectories use path suffixes such as `16-shot/16-13`. |

## FewGLUE Local JSONL Processors

Base split mapping is not the normal train/dev/test convention:

| Helper | File name |
| --- | --- |
| `get_train_examples` | `train.jsonl` |
| `get_dev_examples` | `dev32.jsonl` |
| `get_test_examples` | `val.jsonl` |

| Name | Important JSON fields |
| --- | --- |
| `rte` | `idx`, `premise`, `hypothesis`, `label` (`entailment` or `not_entailment`). |
| `cb` | Same shape as RTE with labels `entailment`, `contradiction`, `neutral`. |
| `wic` | `idx`, `sentence1`, `sentence2`, `word`, boolean `label`. |
| `wsc` | `idx`, `text`, `target.span1_text`, `target.span2_text`, indices, boolean `label`; source code adjusts some spans. |
| `boolq` | `idx`, `passage`, `question`, boolean `label`. |
| `copa` | `idx`, `premise`, `choice1`, `choice2`, `question`, label `0`/`1`; train/unlabeled examples are mirrored. |
| `multirc` | `idx`, nested `passage.text`, `questions`, `answers`; creates one example per answer. |
| `record` | Intended ReCoRD format with passage entities and question answers; source implementation has a static-method/signature bug and should be verified before use. |

## HuggingFace Dataset Processors

Names:

- `super_glue.multirc`, `super_glue.boolq`, `super_glue.cb`, `super_glue.copa`, `super_glue.rte`, `super_glue.wic`, `super_glue.wsc`, `super_glue.record`.
- `yahoo_answers_topics`.

These processors wrap the `datasets` package. Static config inspection can recognize names and warn about blank `dataset.path`, but should not instantiate them because runtime may need network access or a prepared HuggingFace cache.

## NLI Processor

| Name | Expected files | Parsed fields |
| --- | --- | --- |
| `snli` | `<data_dir>/train.tsv`, `<data_dir>/dev.tsv`, `<data_dir>/test.tsv` | TSV fields include premise, hypothesis, label; labels are `entailment`, `neutral`, `contradiction`. |

Repo tests used a nested few-shot path such as `<DATA_ROOT>/SNLI/16-13`; adapt this to the actual user dataset layout.

## Relation Classification Processors

| Name | Expected files | Parsed fields |
| --- | --- | --- |
| `tacred` | `<data_dir>/train.json`, `<data_dir>/dev.json`, `<data_dir>/test.json` | tokenized sentence -> `text_a`; `subj`/`obj` fields become `meta.head`/`meta.tail`; relation label id. |
| `tacrev` | Same layout as TACRED | Revised TACRED labels. |
| `retacred` | Same layout as TACRED | Re-TACRED labels. |
| `semeval` | `<data_dir>/<split>.jsonl` | JSONL rows with sentence/head/tail/relation metadata. |

These datasets are large and often license-restricted. The skill should validate path presence and split-file names, not acquire data automatically.

## Typing Processor

| Name | Expected files | Parsed fields |
| --- | --- | --- |
| `fewnerd` | `<data_dir>/supervised/train.txt`, `dev.txt`, `test.txt` | Sentence tokens plus entity span/type metadata; labels are fine-grained FewNERD types. |

## Conditional Generation Processors

| Name | Expected files | Parsed fields | Notes |
| --- | --- | --- | --- |
| `webnlg_2017`, `webnlg` | `<data_dir>/train.json`, `<data_dir>/dev.json`, `<data_dir>/test.json` | Modified triple set -> `text_a`; lexicalisations -> `tgt_text` | Dev/test targets may join multiple lexicalisations with newlines. |
| `csqa` | `train_rand_split.jsonl`, `dev_rand_split.jsonl`, `test_rand_split_no_answers.jsonl` | Question stem -> `text_a`; answer key -> `tgt_text`; choices in `meta` | Test answer keys can be absent. |
| `ultrachat` | A JSONL file with `id` and `data` dialogue list | Assistant turns become `tgt_text`; context goes into `meta.context` | Source processor accepts a single data path, not `(data_dir, split)`, so `load_dataset` is not a clean fit. |

## LAMA Processor Quirk

The LAMA source map contains `"LAMA": LAMAProcessor`, but `load_dataset` calls `dataset.name.lower()`. A YAML with `dataset.name: LAMA` therefore resolves to `lama`, which is not present in the source map. In addition, `LAMAProcessor` requires constructor arguments (`base_path`, `model_name`, `tokenizer`, `vocab_strategy`, `relation_id`) and reads vocab files. Treat LAMA as a direct advanced processor workflow, not a normal YAML `load_dataset` workflow, unless the user's code patches aliases and constructor handling.

## Config File Patterns

A safe config usually contains:

```yaml
dataset:
  name: <known_processor_name>
  path: <local_dataset_dir_or_null_for_hf>
plm:
  model_name: <openprompt_plm_family>
  model_path: <hf_model_id_or_local_path>
template: <template_branch_name>
verbalizer: <verbalizer_branch_name_or_null_for_generation>
learning_setting: full | few_shot | zero_shot
```

Branch nodes that participate in selector merging should include `parent_config` when they are user-supplied branches:

```yaml
soft_template:
  parent_config: template
manual_verbalizer:
  parent_config: verbalizer
few_shot:
  parent_config: learning_setting
  few_shot_sampling: sampling_from_train
sampling_from_train:
  parent_config: few_shot_sampling
```

OpenPrompt defaults already define several branches, but repo examples often override or add branches explicitly. Static inspection should flag missing selected branches and incorrect `parent_config` values, while allowing unknown new branches if the user has a custom prompt component.
