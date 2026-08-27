# Troubleshooting

## Quick recovery checklist

1. Re-run `scripts/validate_server_config.py` on the server JSON.
2. Confirm the launch working directory matches the relative model/tokenizer paths.
3. Check whether the request belongs to PyTorch inference, CT2 inference, or the REST server.
4. If LM scoring is needed, stay on `InferenceEnginePY`.
5. If the model was released to CT2, verify `src_subword_vocab` and the exported model directory.

## Common failures and fixes

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `FileNotFoundError` for a model path | `models_root` / `model_root` is wrong, or a checkpoint file is missing | Re-check the relative root and the checkpoint list in the config. |
| `FileNotFoundError` for tokenizer data | SentencePiece model or a `params.*path` file is missing | Put the tokenizer files under the configured model root or update the path. |
| `Missing mandatory tokenizer option 'type'` | Tokenizer JSON shape is incomplete | Add `type`, and then `model` or `params` as required by the tokenizer family. |
| `Missing mandatory tokenizer option 'model'` | SentencePiece tokenizer block is incomplete | Add the SentencePiece model path. |
| `Missing mandatory tokenizer option 'params'` | `pyonmttok` tokenizer block is incomplete | Add a `params` object and keep the `mode` key too. |
| `Invalid value for tokenizer type` | Tokenizer type is not `sentencepiece` or `pyonmttok` | Use one of the supported tokenizer families. |
| `To get decoded alignment, joiner/spacer should be used in both side's tokenizer.` | Alignment output was requested with incompatible tokenization | Use reversible tokenization consistently on both source and target. |
| `gold_align` validation error | `report_align` or `tgt` was omitted, or `replace_unk` was enabled | Add `report_align` and `tgt`, and disable `replace_unk`. |
| `replace_unk requires an attentional decoder.` | The model does not expose attentional decoding | Remove `replace_unk` or use an attentional seq2seq model. |
| `World size must be less than 1.` | CT2 engine is being used with multi-process inference settings | Use `InferenceEngineCT2` only in single-process mode. |
| `The scoring with InferenceEngineCT2 is not implemented.` | CT2 path was used for scoring or perplexity | Switch the scoring script to `InferenceEnginePY`. |
| CT2 mismatch error for `beam_size`, `batch_size`, `n_best`, or length fields | `ct2_translate_batch_args` conflicts with the OpenNMT translate options | Make both sides agree or remove the conflicting CT2 override. |
| CT2 device mismatch | `ct2_translator_args.device` or `device_index` does not match the OpenNMT `gpu` choice | Align the CT2 args with the model’s actual device. |
| Hook import failure | `preprocess` or `postprocess` dotted path is not importable | Make the hook module importable in the runtime environment. |
| `ServerModelError` during `/translate` | A runtime exception occurred inside the translator or a hook | Check the server logs, then validate paths and tokenizer settings again. |

## Path semantics to remember

- `models_root` and `model_root` are not rewritten against the config file location.
- Keep relative paths relative to the process launch directory.
- `tokenizer.params` keys ending in `path` are also resolved relative to the same root.
- CT2 export directories and `vocabulary.json` files must exist before startup.

## Shape reminders

- `models` is the top-level list of server entries.
- `id` is optional but recommended for stable server endpoints.
- `load` must be boolean if present.
- `timeout` must be an integer, with negative values disabling the timer.
- `on_timeout` must be `to_cpu` or `unload`.
- `features.src_feats_defaults` must match `n_src_feats`.
- `preprocess` and `postprocess` are lists of dotted function paths.

## If you need a deeper next step

- For CLI semantics, re-open `references/translation-and-serving.md`.
- For model release and CT2 export problems, switch to the conversion sub-skill.
- For tokenizer or feature shape issues outside inference, route back to data preparation.
