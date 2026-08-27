---
name: data-preparation
description: "Routes OpenNMT-py corpus YAML, vocabulary building, transforms,
  tokenizers, source features, and data preparation failure recovery."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Data preparation

Use this sub-skill when an OpenNMT-py task is about shaping corpora before training or inference: corpus YAML, `onmt_build_vocab`, transform lists, tokenizer models, source features, alignment-aware data, and data/config validation failures.

## Use this route when

- The user asks to create, validate, or repair a YAML config with `data`, `path_src`, `path_tgt`, `path_txt`, `path_align`, `src_vocab`, `tgt_vocab`, `save_data`, `n_sample`, or `share_vocab`.
- The user needs to build vocabularies with `onmt_build_vocab` or understand the plain-text vocab files that training later consumes.
- The request mentions transforms such as `filtertoolong`, `prefix`, `suffix`, `clean`, `normalize`, `inferfeats`, `onmt_tokenize`, `sentencepiece`, `bpe`, `bart`, `switchout`, `tokendrop`, `tokenmask`, or `insert_mask_before_placeholder`.
- The user is debugging source features, feature defaults, subword regularization, tokenizer model paths, missing target files, corpus weights, or alignment file compatibility.

## Do not use this route when

- The primary task is model architecture, optimizer schedules, checkpoint resume, LoRA, embeddings, or GPU training orchestration; route that to `../training/`.
- The primary task is translation output, scoring, REST serving, dynamic inference, or CTranslate2 runtime selection; route that to `../inference/`.
- The primary task is checkpoint conversion, checkpoint release, model averaging, or external model import; route that to `../conversion/`.

## Start here

1. Read `references/data-formats.md` for the self-contained corpus YAML schema, vocabulary fields, transform ownership, tokenizer options, source-feature rules, and examples.
2. Run the bundled validator before launching an expensive build or training job:

   ```bash
   python scripts/validate_data_config.py --config CONFIG.yaml --root DATA_ROOT --mode build-vocab
   ```

   Use `--mode train` when checking that already-built vocab files exist for `onmt_train`; use `--mode generic` for a partial data-only YAML.
3. Build vocabularies only after the config is clean enough for the intended mode:

   ```bash
   onmt_build_vocab -config CONFIG.yaml -n_sample 5000
   ```

4. If `n_src_feats` is greater than zero, confirm every corpus has `inferfeats` in `transforms` and that `src_feats_defaults` has exactly one `￨`-separated value per source feature.
5. If alignment learning is involved, validate every `path_align` and avoid on-the-fly tokenization or token-deleting transforms in the aligned training config.

## What this sub-skill owns

- Corpus YAML structure: top-level `data` mapping, train corpus ids, `valid`, file path fields, weights, source-only language-model layouts, and blockwise `path_txt` data.
- Vocabulary preparation: `src_vocab`, `tgt_vocab`, `share_vocab`, `save_data`, `overwrite`, `n_sample`, `dump_samples`, `learn_subwords`, and feature vocab side outputs.
- Transform and tokenizer preparation: per-corpus transform lists, global default transforms, subword model paths, pyonmttok kwargs, regularization knobs, transform order, and transforms that require existing vocabularies.
- Source feature preparation: feature delimiter, `n_src_feats`, `src_feats_defaults`, `inferfeats`, and common mixed-feature-line failures.
- Data-preparation troubleshooting: YAML shape errors, relative path confusion, missing optional tokenizer dependencies, incompatible alignments, invalid vocab modes, and config-vs-command option placement.

## Bundled helper

`scripts/validate_data_config.py` is a self-contained validator. It parses YAML with PyYAML, checks OpenNMT-py data mappings and paths, validates vocab fields for build or train modes, checks feature defaults and sampled feature annotations, warns about transform/tokenizer pitfalls, and never imports the source checkout.

Useful invocations:

```bash
python scripts/validate_data_config.py --config CONFIG.yaml --root . --mode generic
python scripts/validate_data_config.py --config CONFIG.yaml --root . --mode build-vocab --strict
python scripts/validate_data_config.py --config CONFIG.yaml --root . --mode train --sample-lines 50
```

## Troubleshooting entry point

If `onmt_build_vocab` or `onmt_train` fails before model computation starts, read `references/troubleshooting.md` first. Most failures are config shape, relative paths, missing vocab fields, source-feature count mismatches, tokenizer model paths, or transforms that are incompatible with alignments or build-vocab mode.
