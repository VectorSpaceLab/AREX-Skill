# Neuron View Workflows

## Purpose

Use these recipes to compute BertViz neuron-view data, render it in notebooks or
HTML files, and validate a local install without downloading pretrained models.

## Offline toy validation first

Before debugging a large pretrained model, run the bundled validator:

```bash
python scripts/validate_toy_bert_attention.py
python scripts/validate_toy_bert_attention.py --include-query-key-schema
```

The helper generates a tiny BERT config and vocabulary in a temporary
directory, instantiates BertViz's modified BERT classes, and checks token
partitions, attention probabilities, and query/key schema without network
access.

## BERT neuron view

```python
from bertviz.transformers_neuron_view import BertModel, BertTokenizer
from bertviz.neuron_view import show

model_type = "bert"
model_version = "bert-base-uncased"  # or a local directory with compatible files
tokenizer = BertTokenizer.from_pretrained(model_version, do_lower_case=True)
model = BertModel.from_pretrained(model_version)

html = show(
    model,
    model_type,
    tokenizer,
    "The cat sat on the mat",
    "The cat lay on the rug",
    layer=2,
    head=0,
    html_action="return",
)
with open("bert_neuron_view.html", "w", encoding="utf-8") as f:
    f.write(html.data)
```

Use BERT when you need sentence-pair filtering and token type IDs are natural
for the model.

## GPT-2 neuron view

```python
from bertviz.transformers_neuron_view import GPT2Model, GPT2Tokenizer
from bertviz.neuron_view import show

model_type = "gpt2"
model_version = "gpt2"
tokenizer = GPT2Tokenizer.from_pretrained(model_version)
model = GPT2Model.from_pretrained(model_version)

show(model, model_type, tokenizer, "At the store, she bought apples, oranges, bananas,")
```

Do not pass `sentence_b` for GPT-2. BertViz treats GPT-2 as unidirectional and
sets `bidirectional=False` in the visualization parameters.

## RoBERTa neuron view

```python
from bertviz.transformers_neuron_view import RobertaModel, RobertaTokenizer
from bertviz.neuron_view import show

model_type = "roberta"
model_version = "roberta-base"
tokenizer = RobertaTokenizer.from_pretrained(model_version)
model = RobertaModel.from_pretrained(model_version)

show(
    model,
    model_type,
    tokenizer,
    "The cat sat on the mat",
    "The cat lay on the rug",
    display_mode="dark",
)
```

RoBERTa supports sentence pairs in BertViz, but uses RoBERTa separator handling
rather than BERT token type IDs.

## Direct `get_attention` workflow

Use `get_attention` when you want to inspect or test the data that the D3
renderer receives.

```python
from bertviz.neuron_view import get_attention

attn_data = get_attention(
    model,
    "bert",
    tokenizer,
    "The cat sat on the mat",
    "The cat lay on the rug",
    include_queries_and_keys=True,
)

assert set(attn_data) == {"all", "aa", "ab", "ba", "bb"}
assert "queries" in attn_data["all"]
assert "keys" in attn_data["all"]
```

The `attn` values are nested lists: layers, heads, source tokens, target tokens.
For sentence pairs, the four directional partitions should reassemble into the
`all` attention matrix for each layer/head.

## Avoiding unwanted downloads

`from_pretrained("bert-base-uncased")`, `from_pretrained("gpt2")`, and similar
calls can download weights/tokenizer files. For reproducible or offline runs:

1. Prefer a local model directory that already contains compatible files.
2. Use the toy validator to distinguish install/API problems from cache/network
   problems.
3. If only head/model attention visualization is needed, compute attention with
   any supported model stack and route to `attention-views`.

## Display and export modes

- Use `html_action="view"` in Jupyter/Colab when immediate display is desired.
- Use `html_action="return"` to save or post-process the generated HTML.
- `display_mode="dark"` is the default; pass `"light"` when a light theme is
  desired.
- `layer` and `head` preselect the initial layer/head in the rendered widget.
