# Python Pipeline API Reference

## Verified public entry points

```python
from ltp import LTP, StnSplit
```

`LTP` is a factory function with this inspected signature:

```python
LTP(
    pretrained_model_name_or_path="LTP/small",
    force_download=False,
    proxies=None,
    token=None,
    cache_dir=None,
    local_files_only=False,
    **model_kwargs,
)
```

It resolves `config.json` from a local directory or Hugging Face Hub/cache. The config determines whether the returned object is the neural implementation or the legacy implementation.

## Model identifiers and revisions

- Built-in model ids include `LTP/tiny`, `LTP/small`, `LTP/base`, `LTP/base1`, `LTP/base2`, and `LTP/legacy`.
- Add a revision with `@`, for example `LTP/small@main`.
- Pass a local directory path for offline/private models. The directory must contain `config.json` and the weights/model files required by that config.
- Use `cache_dir=...`, `force_download=True`, `token=...`, `proxies=...`, and `local_files_only=True` the same way you would for Hugging Face downloads. Keep secrets outside code.

## Neural pipeline

Source signature:

```python
pipeline(inputs, tasks=None, raw_format=False, return_dict=True)
```

- Default neural tasks: `cws`, `pos`, `ner`, `srl`, `dep`, `sdp`, `sdpg`.
- If `cws` is requested, `inputs` should be a string or list of raw strings.
- If `cws` is not requested, `inputs` should be pretokenized words: `List[str]` for one sentence or `List[List[str]]` for a batch.
- `raw_format=False` converts NER and SRL tags into entity/argument spans. Set `raw_format=True` to keep lower-level tag sequences.
- `return_dict=True` returns `LTPOutput`; `return_dict=False` returns a tuple via `LTPOutput.to_tuple()`.

The neural implementation is a torch module. Use `.to("cuda")`, `.cuda()`, or `.cpu()` only after verifying the backend.

## Legacy high-level pipeline

Inspected signature:

```python
pipeline(*args, tasks=None, raw_format=False, parallelism=True, return_dict=True)
```

- Default legacy tasks: `cws`, `pos`, `ner`.
- `LTP("LTP/legacy")` does not support `srl`, `dep`, `sdp`, or `sdpg`.
- Legacy NER depends on POS. Ask for `['cws', 'pos', 'ner']`, or pass words and POS results explicitly to a follow-up call.
- `parallelism=True` uses the extension's parallel path when available.

## Output container

`LTPOutput` fields are:

```text
cws, pos, ner, srl, dep, sdp, sdpg
```

Access examples:

```python
output = ltp.pipeline(["他叫汤姆去拿外衣。"], tasks=["cws", "pos"])
words = output.cws
pos = output["pos"]
first_non_none = output[0]
words, pos = output.to_tuple()
```

The container is mapping/tuple-like but cannot be mutated with `pop`, `update`, or `setdefault`.

## Sentence splitting

`StnSplit` comes from `ltp_extension.algorithms` and is re-exported by `ltp`.

```python
from ltp import StnSplit
splitter = StnSplit()
splitter.use_en = False
sentences = splitter.split("汤姆生病了。他去了医院。")
batch = splitter.batch_split(["他叫汤姆去拿外衣。", "汤姆生病了。他去了医院。"], threads=8)
```

Live inspection confirmed `split` returns a list of sentences and `batch_split` returns a flattened list for the input batch.

## Custom words

Both neural and legacy high-level LTP objects expose:

```python
ltp.add_word("长江大桥", freq=2)
ltp.add_words(["外套", "外衣"], freq=2)
```

Use custom words before calling `pipeline`; the hook adjusts CWS output and downstream tasks then consume the adjusted words.

## Task output reminders

- `dep` and `sdp` return dictionaries with `head` and `label`; dependency indices use root at 0 and token positions starting from 1.
- `sdpg` returns graph arcs as tuples/lists shaped like `(source, target, label)`.
- `ner` entities are tuples such as `(tag, text, start, end)` in neural post-processed output and `(tag, text)` in the legacy wrapper unless raw format is requested.
- `srl` output is a list of predicate dictionaries with `index`, `predicate`, and `arguments`.
