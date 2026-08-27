# GPT-2 NLG data formats

## Text records before tokenization

Each line is a JSON object with at least:

```json
{"context": "name : value", "completion": "a natural-language sentence"}
```

The repository's converters produce this shape for:

- E2E: a source line split at `||` into context and completion;
- WebNLG: the modified triple set joined with ` | ` and good lexicalisations;
- DART: triples joined as `subject : relation : object` with ` | ``, paired
  with each annotation text.

Keep the dataset ordering stable because decoding matches predictions to the
input record id.

## Tokenized training records

The GPT-2 encoder converts the two strings into integer lists:

```json
{"context": [50256, 123, 456], "completion": [789, 1011, 50256]}
```

The encoder prepends/appends token id `50256` when `--add_bos`/`--add_eos` is
passed. The training dataset expects `context` and `completion` to be lists of
integers and pads/truncates them to `--seq_len`.

## Beam predictions

The beam-search output is JSONL with at least `id` and `predict` keys, where
`predict` is a list of generated token ids:

```json
{"id": 0, "predict": [123, 456, 50256]}
```

The decoder joins the prediction to the input record by `id`, decodes through
the same vocabulary, and strips the end-of-text marker. Missing ids, duplicate
ordering, or a different vocabulary produces apparently valid but misaligned
text, so validate before metric calculation.

## Reference and hypothesis files

- E2E: one hypothesis per input and a blank-separated block containing all
  references.
- WebNLG/DART: a hypothesis file plus `reference0`, `reference1`, ... files;
  `--ref_num` must match the number expected by the evaluator.
- Optional `--tokenize` and `--lower` alter the text written for evaluation;
  use the same normalization assumptions as the metric script.

The bundled `validate_nlg_jsonl.py` checks the JSONL stages. It does not claim
that external metric files or scores are correct.
