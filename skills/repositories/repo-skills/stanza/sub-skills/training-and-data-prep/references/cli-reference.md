# Training and Data CLI Reference

## When to read

Read this when constructing or reviewing a Stanza training/evaluation command. The commands below use installed Python modules (`python -m ...`) and do not require the original source checkout.

## Core model entry points

| Model family | Module | Primary modes | Required data flags to check first | Notes |
| --- | --- | --- | --- | --- |
| Tokenizer / sentence splitter | `stanza.models.tokenizer` | `--mode train`, `--mode predict` | `--txt_file`, `--label_file`, `--dev_txt_file`, `--dev_label_file`, optional `--mwt_json_file`, `--dev_conll_gold` | Supports `--skip_newline`, dictionary features, feature functions, charlm options, `--use_mwt`/`--no_use_mwt`. |
| MWT expander | `stanza.models.mwt_expander` | train/predict | CoNLL-U or MWT JSON inputs depending on workflow | Usually trained after tokenization data is prepared. |
| POS / morphology | `stanza.models.tagger` | `--mode train`, `--mode predict` | `--train_file`, `--eval_file`, optional `--wordvec_file` or `--wordvec_pretrain_file` | Supports charlm, transformer, PEFT, and device flags. |
| Lemmatizer | `stanza.models.lemmatizer` | train/predict | train/eval CoNLL-U files, optional charlm/pretrain | Can use identity or contextual/classifier behavior depending on model/package. |
| Dependency parser | `stanza.models.parser` | train/predict | `--train_file`, `--eval_file`, optional `--silver_file`, pretrain/charlm/transformer flags | CPU works for tiny tests; real training is often GPU-memory sensitive. |
| NER tagger | `stanza.models.ner_tagger` | train/predict | `--train_file`, `--eval_file`, scheme/pretrain flags | Use `--scheme`/`--train_scheme` carefully when converting BIO/BIOES data. |
| Sentiment/classifier | `stanza.models.classifier` | train/eval/predict family | classifier data files, model/save flags | The same code supports sentiment-like text classification workflows. |
| Constituency parser | `stanza.models.constituency_parser` | train/predict/eval | treebank files, retagging/model paths as needed | Some workflows use transformer or retagging pipelines. |
| Character LM | `stanza.models.charlm` | train/evaluate | raw text files or prepared charlm data | Used as a dependency for several models. |
| Language ID | `stanza.models.lang_identifier` | train/eval/predict | language-labeled data | Related to `MultilingualPipeline` routing. |
| Coref | `stanza.models.wl_coref` or coref modules | train/eval/predict | experiment/config/data split files | Optional transformer/PEFT dependencies may be required. |

## Higher-level training wrappers

Use wrapper modules when you want Stanza's standard per-treebank defaults, output naming, charlm/pretrain selection, or `all_ud` iteration:

- `python -m stanza.utils.training.run_tokenizer TREEBANK --train`
- `python -m stanza.utils.training.run_mwt TREEBANK --train`
- `python -m stanza.utils.training.run_pos TREEBANK --train`
- `python -m stanza.utils.training.run_lemma TREEBANK --train`
- `python -m stanza.utils.training.run_depparse TREEBANK --train`
- `python -m stanza.utils.training.run_ner DATASET --train`
- `python -m stanza.utils.training.run_constituency TREEBANK --train`
- `python -m stanza.utils.training.run_sentiment DATASET --train`
- `python -m stanza.utils.training.run_charlm CORPUS --train`

Common wrapper flags:

- Positional `treebanks`: one or more treebank names; `all_ud` or `ud_all` expands all UD treebanks visible under the configured UD data root.
- `--train`, `--score_dev`, `--score_test`, `--score_train`: choose the wrapper mode.
- `--save_dir`, `--save_name`: override output names; always use these in automation to avoid accidental writes under package defaults.
- `--force`: retrain even if an expected model file exists.
- `--charlm`, `--no_charlm`, `--charlm_only`: control character language model use where supported.
- `--transformer_only`: filter `all_ud` to languages with transformer settings.
- `--extra_args`: use this delimiter when the wrapper and underlying model both define similarly named flags.

## Device and optional dependency flags

Most neural model CLIs inherit device flags:

- `--cpu` forces CPU.
- `--cuda` requests CUDA.
- `--device DEVICE` is the most explicit option when the parser exposes it.

Optional features require extras or separately installed packages:

- Transformer features require `transformers` and sometimes `peft`.
- `--use_peft` implies transformer finetuning and needs the optional PEFT package.
- Visualization helpers need visualization extras; do not install them for training-only tasks.
- W&B logging is opt-in via `--wandb` or `--wandb_name`; avoid enabling it without credentials and an explicit logging requirement.

## Command builder helper

Use the bundled helper for dry command construction:

```bash
python scripts/build_training_command.py tokenizer en_ewt --mode train --save-dir /tmp/stanza-models --no-charlm
python scripts/build_training_command.py ner en_ontonotes --mode score-dev --extra --batch_size 16
```

The helper prints commands and never executes training.
