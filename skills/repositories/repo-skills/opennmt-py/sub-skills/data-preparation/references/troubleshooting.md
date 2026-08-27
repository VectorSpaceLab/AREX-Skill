# Data preparation troubleshooting

## Purpose

Use this when OpenNMT-py fails during YAML parsing, corpus loading, vocabulary building, transform warm-up, tokenizer loading, source-feature parsing, or alignment-aware data preparation.

## Fast triage

1. Run the bundled validator in the intended mode:

   ```bash
   python scripts/validate_data_config.py --config CONFIG.yaml --root . --mode build-vocab
   ```

2. If the validator reports only warnings, decide whether they matter for the current mode. Re-run with `--strict` before long jobs.
3. If OpenNMT-py still fails, compare the error fragment below with the likely cause and recovery steps.

## Common failures

| Symptom or error fragment | Likely cause | Recovery |
| --- | --- | --- |
| YAML parser error, or `expected a mapping` | Indentation, tabs, a missing colon, or a top-level `data` value that is not a corpus mapping. | Reformat `data` as a mapping of corpus ids to mappings. Validate with `--mode generic`. |
| `Corpus NAME src/txt path is required` | A corpus entry lacks both `path_src` and `path_txt`. | Add `path_src` for parallel/source-only corpora or `path_txt` for blockwise text. |
| `Please check path of your NAME/path_src file` | Relative path is not valid from the CLI working directory, or the file was not staged where expected. | Run from the intended data root, adjust `--root` in the validator to mirror that root, or rewrite paths consistently. |
| `path_tgt is None` debug message, source-only behavior, or unexpected LM-style training | `path_tgt` was omitted. OpenNMT-py treats that corpus as language-model style by using source as target. | For seq2seq, add `path_tgt` to every training and `valid` corpus. For LM, keep all corpora source-only and route model-task details to training. |
| `-tgt_vocab is required if not -share_vocab` | `tgt_vocab` is missing and `share_vocab` is false or absent. | Add `tgt_vocab` or set `share_vocab: true` when a shared vocabulary is intended. |
| Build vocab refuses to overwrite an output file | `src_vocab`, `tgt_vocab`, feature vocab, or sample outputs already exist and `overwrite` is false. | Choose a new output prefix or set `overwrite: true` deliberately. Keep old vocab files if the current checkpoint depends on them. |
| `Illegal argument n_sample=0` or `n_sample should > 0 or == -1` | `onmt_build_vocab` needs `n_sample` greater than `1` or `-1`; `0` is a training-time skip value. | Use `onmt_build_vocab -config CONFIG.yaml -n_sample 5000` or `-n_sample -1` for full corpus. |
| `-save_data should be set if want save samples` | Training config uses nonzero `n_sample`, `dump_transforms`, embeddings, or build-vocab mode without `save_data`. | Add `save_data` as an output prefix or set training `n_sample: 0` when you do not want sample dumping. |
| `inferfeats transform is required when setting source features` | `n_src_feats` is greater than zero but at least one corpus lacks `inferfeats`. | Add `inferfeats` to every corpus transform list or remove source-feature options. |
| `The number source features defaults does not match -n_src_feats` | `src_feats_defaults` has a different number of `￨`-separated values than `n_src_feats`. | Set exactly one default per feature channel, for example `src_feats_defaults: "0￨UNK"` for `n_src_feats: 2`. |
| `The number of fetures does not match` | A token has fewer or more inline feature columns than `n_src_feats`. | Fix source lines to use `token￨feat1￨feat2`; run the validator with `--sample-lines` to locate early mismatches. |
| `Some tokens are missing features` | A source line mixes annotated and unannotated tokens without compatible defaults. | Annotate every token consistently or provide `src_feats_defaults`. |
| `transform not supported` | A transform name is misspelled or unavailable in the installed package. | Use one of the built-in transform names or run the validator with `--allow-custom-transforms` only when a custom installed transform is intentional. |
| Prefix or suffix transform fails for a corpus | `prefix` or `suffix` was applied but the corpus-specific prefix/suffix values were omitted or the transform is used without a corpus name. | Add `src_prefix`/`tgt_prefix` or `src_suffix`/`tgt_suffix` to each corpus using the transform. |
| SentencePiece/BPE model load fails | `src_subword_model` or `tgt_subword_model` is missing, points at the wrong file, or the optional tokenizer dependency is absent. | Validate model paths; install the corresponding tokenizer dependency only for that workflow; for shared vocab/model, use the source model deliberately. |
| `src_subword_alpha should be in the range [0, 1]` | Subword sampling or BPE dropout alpha is outside the valid range. | Set `src_subword_alpha` and `tgt_subword_alpha` between `0` and `1`. |
| pyonmttok kwargs validation fails | `src_onmttok_kwargs` or `tgt_onmttok_kwargs` is not a dictionary string. | Use a quoted dictionary string such as `"{'mode': 'none', 'spacer_annotate': True}"`. |
| Alignment learning complains about missing alignments | `lambda_align` is greater than zero but at least one corpus has no `path_align`. | Add a valid `path_align` for every training corpus or disable alignment training. |
| Alignment learning rejects tokenization or token-changing transforms | `lambda_align` is incompatible with `sentencepiece`, `bpe`, `onmt_tokenize`, `tokendrop`, `prefix`, or `bart` in the validated path. | Prepare aligned text before OpenNMT-py sees it, remove incompatible transforms, or train without supervised alignment. |
| Vocabulary counts look too small or unstable | `n_sample` is too low, stochastic transforms are active, or build-vocab transforms differ from training transforms. | Increase `n_sample`, use deterministic tokenizer settings for vocab construction, and keep build/training transform lists aligned. |

## Feature-specific checks

Use these checks when `n_src_feats` is present:

- Count separators in source data: every token should have exactly `n_src_feats` feature values after the token text.
- If defaults are configured, the default string must split into exactly `n_src_feats` values on `￨`.
- If a line has some annotated tokens and some unannotated tokens, fix the line even if defaults are present; mixed lines are the easiest way to produce surprising feature vocabularies.
- Remember that feature vocab files are derived from `src_vocab`, with suffixes `_feat0`, `_feat1`, and so on.

## Tokenizer-specific checks

- For `sentencepiece` and `bpe`, check both source and target model paths unless the source model is intentionally shared.
- For `onmt_tokenize`, validate that `src_subword_type` and `tgt_subword_type` match the model files: `sentencepiece` for SentencePiece models, `bpe` for BPE codes, or `none` for tokenizer-only behavior.
- Use deterministic settings when debugging: `src_subword_nbest: 1`, `tgt_subword_nbest: 1`, and alpha values of `0`.
- If a tokenizer should preserve placeholders, make that explicit in the pyonmttok kwargs; otherwise mask and placeholder tokens may be split.

## When to stop and reroute

- If the YAML validates but training fails on optimizer, devices, checkpoint state, LoRA, embeddings, or architecture options, route to `../training/`.
- If the issue appears only during `onmt_translate`, scoring, server startup, or dynamic inference configs, route to `../inference/`.
- If the data preparation question is actually about converting external checkpoints or updating checkpoint vocabularies, route checkpoint-specific steps to `../conversion/` or `../training/` while keeping corpus/vocab validation here.
