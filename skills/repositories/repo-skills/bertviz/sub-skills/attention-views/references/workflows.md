# Workflows

## 1) Self-attention from a pretrained model

Use this flow for BERT, DistilBERT, GPT-2, RoBERTa-style self-attention views.

```python
from transformers import AutoTokenizer, AutoModel, utils
from bertviz import head_view, model_view

utils.logging.set_verbosity_error()

model_name = "distilbert-base-uncased"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModel.from_pretrained(model_name, output_attentions=True)

inputs = tokenizer.encode("The cat sat on the mat", return_tensors="pt")
outputs = model(inputs)
attention = outputs.attentions if hasattr(outputs, "attentions") else outputs[-1]
tokens = tokenizer.convert_ids_to_tokens(inputs[0])

head_view(attention, tokens)
model_view(attention, tokens)
```

Notes:
- Distilled from the DistilBERT head-view and model-view notebooks.
- Keep `output_attentions=True`; otherwise BertViz cannot format the tensors.
- Use `model_view(..., display_mode="light")` when the dark theme is hard to read.

## 2) Sentence-pair visualization

Use this flow when the input contains two sentences and you want the A/B dropdown.

```python
from transformers import AutoTokenizer, AutoModel, utils
from bertviz import head_view, model_view

utils.logging.set_verbosity_error()

model_name = "bert-base-uncased"
sentence_a = "the rabbit quickly hopped"
sentence_b = "The turtle slowly crawled"

tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModel.from_pretrained(model_name, output_attentions=True)
inputs = tokenizer.encode_plus(sentence_a, sentence_b, return_tensors="pt")
input_ids = inputs["input_ids"]
token_type_ids = inputs["token_type_ids"]
attention = model(input_ids, token_type_ids=token_type_ids)[-1]
sentence_b_start = token_type_ids[0].tolist().index(1)
tokens = tokenizer.convert_ids_to_tokens(input_ids[0])

head_view(attention, tokens, sentence_b_start=sentence_b_start, layer=2, heads=[3, 5])
model_view(attention, tokens, sentence_b_start=sentence_b_start)
```

Notes:
- Distilled from the BERT sentence-pair notebook.
- `sentence_b_start` must point to the first token in sentence B after tokenization.
- `layer` and `heads` in `head_view` set the initial selection; they do not remove heads from the data.

## 3) Encoder-decoder and cross attention

Use this flow for BART, MarianMT, T5-style encoder-decoder models.

```python
from transformers import AutoTokenizer, AutoModel, utils
from bertviz import model_view

utils.logging.set_verbosity_error()

tokenizer = AutoTokenizer.from_pretrained("Helsinki-NLP/opus-mt-en-de")
model = AutoModel.from_pretrained("Helsinki-NLP/opus-mt-en-de", output_attentions=True)

encoder_input_ids = tokenizer(
    "She sees the small elephant.",
    return_tensors="pt",
    add_special_tokens=True,
).input_ids

with tokenizer.as_target_tokenizer():
    decoder_input_ids = tokenizer(
        "Sie sieht den kleinen Elefanten.",
        return_tensors="pt",
        add_special_tokens=True,
    ).input_ids

outputs = model(input_ids=encoder_input_ids, decoder_input_ids=decoder_input_ids)

encoder_tokens = tokenizer.convert_ids_to_tokens(encoder_input_ids[0])
decoder_tokens = tokenizer.convert_ids_to_tokens(decoder_input_ids[0])

model_view(
    encoder_attention=outputs.encoder_attentions,
    decoder_attention=outputs.decoder_attentions,
    cross_attention=outputs.cross_attentions,
    encoder_tokens=encoder_tokens,
    decoder_tokens=decoder_tokens,
    display_mode="light",
)
```

Notes:
- Distilled from the encoder-decoder and BART notebooks.
- `head_view` accepts the same encoder/decoder/cross blocks when you want a head-focused rendering.
- `cross_attention` uses decoder tokens on the left and encoder tokens on the right.

## 4) Saved HTML and non-notebook workflows

Use `html_action='return'` whenever you want a saved file or custom renderer.

```python
from pathlib import Path
from bertviz import head_view, model_view

html_obj = model_view(attention, tokens, html_action="return")
Path("model_view.html").write_text(html_obj.data, encoding="utf-8")
```

Notes:
- The returned object is an `IPython.display.HTML` wrapper; write `.data` to disk.
- In notebooks and Colab, the default `html_action='view'` is the fastest path.
- If you need to inspect raw wordpiece markers, set `prettify_tokens=False`.

## 5) Offline synthetic validation

Use the bundled helper to smoke-test the API without downloading models.

```bash
python scripts/render_synthetic_attention.py --view both --action validate
python scripts/render_synthetic_attention.py --view model --encoder-decoder --action write-html --output-dir ./artifacts
```

Notes:
- The helper builds synthetic tensors with the documented attention shapes.
- It uses `html_action='return'` internally and fails fast on invalid BertViz outputs.
- This is the safest path for scripts, CI-style checks, and CWD-independent smoke tests.
