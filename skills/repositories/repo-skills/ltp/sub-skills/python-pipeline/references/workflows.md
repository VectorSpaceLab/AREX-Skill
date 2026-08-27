# Python Pipeline Workflows

## 1. No-network environment and sentence-split check

Use this before model loading:

```bash
python scripts/ltp_pipeline_smoke.py --skip-model-load
```

It verifies `from ltp import LTP, StnSplit`, runs sentence splitting, and exits before any Hugging Face model resolution.

## 2. Basic neural inference

```python
from ltp import LTP

ltp = LTP("LTP/small")
output = ltp.pipeline(
    ["他叫汤姆去拿外衣。"],
    tasks=["cws", "pos", "ner", "srl", "dep", "sdp", "sdpg"],
)
print(output.cws)
print(output.pos)
print(output.ner)
print(output.dep)
```

Use `LTP/tiny` for faster checks, `LTP/small` for the default balance, and `LTP/base*` when quality matters more than speed.

## 3. Offline/local model loading

```python
from ltp import LTP

ltp = LTP("/path/to/local/ltp-model", local_files_only=True)
output = ltp.pipeline(["他叫汤姆去拿外衣。"], tasks=["cws", "pos", "ner"])
```

The local directory must contain `config.json` and the expected model/tokenizer files. For a cache-only check against a Hugging Face id, keep `local_files_only=True`.

## 4. Optional CUDA movement

```python
import torch
from ltp import LTP

ltp = LTP("LTP/small")
if torch.cuda.is_available():
    torch.empty((1,), device="cuda")
    ltp.to("cuda")
```

Do not move the model to CUDA just because a GPU exists. Verify the torch build, driver, and a tiny allocation first.

## 5. Custom words

```python
from ltp import LTP

ltp = LTP("LTP/small")
ltp.add_word("汤姆去", freq=2)
ltp.add_words(["外套", "外衣"], freq=2)
output = ltp.pipeline(["他叫汤姆去拿外衣。"], tasks=["cws", "pos", "ner"])
```

Custom words affect CWS and therefore downstream word-level tasks.

## 6. Pretokenized input

When the caller already has words, omit `cws` and pass word lists:

```python
result = ltp.pipeline(
    [["他", "叫", "汤姆", "去", "拿", "外衣", "。"]],
    tasks=["pos", "ner", "srl", "dep", "sdp"],
)
```

If raw strings are passed here, the tokenizer treats them as pre-split input and the task will be wrong.

## 7. Legacy through the high-level factory

```python
from ltp import LTP

ltp = LTP("LTP/legacy")
output = ltp.pipeline(
    ["他叫汤姆去拿外衣。"],
    tasks=["cws", "pos", "ner"],
)
```

Route direct `ltp_extension.perceptron` model/trainer work to the legacy-extension sub-skill.

## 8. Convert existing JSON output to CoNLL-U-like rows

Save a JSON object or list with `cws`, `pos`, `dep`, and optionally `sdpg`, then run:

```bash
python scripts/convert_ltp_output_to_conllu.py --input output.json --output output.conllu
```

The converter does not load an LTP model. It is useful when another step already produced JSON-like pipeline output.

## 9. Batch processing pattern

```python
sentences = ["他叫汤姆去拿外衣。", "汤姆生病了。他去了医院。"]
output = ltp.pipeline(sentences, tasks=["cws", "pos", "ner"])
for text, words, pos, ner in zip(sentences, output.cws, output.pos, output.ner):
    print(text, words, pos, ner)
```

Split long documents first with `StnSplit` and feed sentence batches to the model. Preserve original offsets if downstream systems need document-level spans.

## 10. Safety checklist before production use

- Confirm exact model id/path and whether network is allowed.
- Decide whether outputs should be raw tags or post-processed spans.
- Preserve task order and dependencies in tests (`cws` before POS/NER unless pretokenized).
- Record whether CUDA was actually used; do not infer it from GPU presence.
- Keep private model tokens and proxies outside scripts and logs.
