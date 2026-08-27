# Language-model API reference

## ModelLanguage

ASRT exposes a `ModelLanguage` class for the statistical language model.

```python
ml = ModelLanguage(model_path)
ml.load_model()
text = ml.pinyin_to_text(list_pinyin, beam_size=100)
```

The bundled `scripts/decode_pinyin.py` keeps the same core methods and adds an optional `dict_path` constructor argument so the decoder can load the self-contained bundled dictionary without relying on the caller's current working directory.

### Constructor

```python
ModelLanguage(model_path: str)
```

- `model_path`: directory containing `language_model1.txt` and `language_model2.txt`.
- State initialized by the constructor: `dict_pinyin`, `model1`, and `model2`, all empty dictionaries until `load_model()` runs.

Bundled helper extension:

```python
ModelLanguage(model_path: str, dict_path: str = "dict.txt")
```

- `dict_path`: pinyin dictionary file. The original ASRT source effectively expects `dict.txt` in the current working directory.

### load_model

```python
load_model()
```

Loads:

- pinyin candidates from `dict.txt`;
- unigram counts from `language_model1.txt`;
- bigram counts from `language_model2.txt`.

Return value: `(dict_pinyin, model1, model2)`.

Important file-format details:

- `dict.txt` has one pinyin row per line: `pinyin<TAB>candidate_characters`.
- `language_model1.txt` and `language_model2.txt` start with a total-count line such as `3941753`; the decoder does not use that first line for scoring.
- Later count lines are tab separated and should be UTF-8 encoded.

### pinyin_to_text

Verified signature:

```python
pinyin_to_text(self, list_pinyin: list, beam_size: int = 100) -> str
```

- `list_pinyin`: list of tone-number pinyin tokens, for example `['ni3', 'hao3', 'ya5']`.
- `beam_size`: maximum number of candidate paths retained after each non-initial extension; ASRT servers use `100`.
- Returns a Chinese text string.

Example:

```python
ml = ModelLanguage("language_model", dict_path="dict.txt")
ml.load_model()
assert ml.pinyin_to_text(['ni3', 'hao3', 'ya5']) == '你好呀'
```

Batch fallback behavior: if extending a previous candidate state with the current pinyin produces no candidate, the method commits the best previous candidate, restarts from the current pinyin, commits that single-token candidate if any, then clears the intermediate state.

### pinyin_stream_decode

```python
pinyin_stream_decode(self, temple_result: list, item_pinyin: str, beam_size: int = 100) -> list
```

Parameter notes:

- `temple_result`: previous candidate state list. The name is spelled this way in ASRT source.
- `item_pinyin`: one tone-number pinyin token.
- `beam_size`: maximum number of states returned after sorting by score.

Return value: a list of `[candidate_text, score]` pairs. Examples:

```python
state = ml.pinyin_stream_decode([], 'ni3')
# [['拟', 1.0], ['你', 1.0], ...]
state = ml.pinyin_stream_decode(state, 'hao3')
# best state begins with ['你好', ...]
```

If `item_pinyin` is absent from `dict.txt`, the method returns `[]` and performs no decode.

## Server integration evidence

The ASRT HTTP service's language branch reads JSON field `sequence_pinyin` and returns `ml.pinyin_to_text(seq_pinyin)`. The ASRT gRPC `Language` method converts `request.pinyins` to a list and returns `ml.pinyin_to_text(...)`. The gRPC `Stream` method keeps `tmp_result_last` across incoming audio chunks and calls `pinyin_stream_decode` for each recognized pinyin token.

Endpoint wiring, request/response schemas, and client behavior belong to the `serving-clients` sub-skill. This sub-skill owns only the local language-model API and decoding behavior.
