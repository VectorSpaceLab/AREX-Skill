# Embedding Recipes

## Purpose

Use this reference to choose, compose, and validate Flair embeddings in a public, pip-installed `flair` workflow. It assumes CPU PyTorch as the verified baseline. Named pretrained resources, model downloads, CUDA, ONNX providers, `sentence-transformers`, OCR/image models, and other optional dependencies are available only when the current environment proves them.

Installed API evidence for Flair 0.15.1 includes these constructor shapes: `TransformerEmbeddings(model="bert-base-uncased", fine_tune=True, layers="-1", layer_mean=True, subtoken_pooling="first", cls_pooling="cls", is_token_embedding=True, is_document_embedding=True, allow_long_sentences=False, use_context=False, ...)`, `TransformerWordEmbeddings(model="bert-base-uncased", is_document_embedding=False, allow_long_sentences=True, **kwargs)`, `TransformerDocumentEmbeddings(model="bert-base-uncased", layers="-1", layer_mean=False, is_token_embedding=False, **kwargs)`, `WordEmbeddings(embeddings, field=None, fine_tune=False, force_cpu=True, ...)`, `FlairEmbeddings(model, fine_tune=False, chars_per_chunk=512, ...)`, `PooledFlairEmbeddings(contextual_embeddings, pooling="min", ...)`, `StackedEmbeddings(embeddings, overwrite_names=True)`, `OneHotEmbeddings(vocab_dictionary, field="text", embedding_length=300, stable=False)`, `BytePairEmbeddings(language=None, dim=50, syllables=100000, ...)`, `DocumentPoolEmbeddings(embeddings, fine_tune_mode="none", pooling="mean")`, `DocumentRNNEmbeddings(embeddings, hidden_size=128, rnn_layers=1, bidirectional=False, rnn_type="GRU", ...)`, and `DocumentCNNEmbeddings(embeddings, kernels=((100, 3), (100, 4), (100, 5)), ...)`.

## Embedding contract and shape checks

Flair embeddings are PyTorch modules that attach tensors to `Sentence` and `Token` data points.

- `TokenEmbeddings` produce one vector per token. Use them for `SequenceTagger`, `TokenClassifier`, `SpanClassifier`, `RelationExtractor`, token-level feature export, or any model expecting token features.
- `DocumentEmbeddings` produce one vector per `Sentence`. Use them for `TextClassifier`, `TextRegressor`, document-level relation classifiers, sentence similarity, dense retrieval features, or document vector export.
- `embedding.embed(sentence_or_sentences)` mutates the data points in place and returns a list of embedded points.
- `embedding.embedding_length` is the expected vector width for the embedding object.
- `embedding.get_names()` returns the embedding names stored on tokens or sentences. Use these names for precise checks.
- `get_embedding()` without names concatenates all stored embeddings in sorted-name order. This can include stale tensors from earlier experiments.
- `sentence.clear_embeddings()` removes sentence-level and token-level embeddings. Use it after standalone embedding or between baseline and optimized comparisons.

Minimal no-download shape assertions:

```python
from flair.data import Dictionary, Sentence
from flair.embeddings import DocumentPoolEmbeddings, OneHotEmbeddings

vocab = Dictionary(add_unk=True)
for item in ["Berlin", "loves", "Flair", "."]:
    vocab.add_item(item)

sentence = Sentence("Berlin loves Flair .")
token_embeddings = OneHotEmbeddings(vocab_dictionary=vocab, embedding_length=16)
token_embeddings.embed(sentence)

token_names = token_embeddings.get_names()
assert all(len(token.get_embedding(token_names)) == token_embeddings.embedding_length for token in sentence)

sentence.clear_embeddings()
document_embeddings = DocumentPoolEmbeddings([token_embeddings], pooling="mean", fine_tune_mode="none")
document_embeddings.embed(sentence)
assert len(sentence.get_embedding(document_embeddings.get_names())) == document_embeddings.embedding_length
sentence.clear_embeddings()
```

## Device and cache baseline

Set environment variables before importing `flair`:

```bash
export FLAIR_DEVICE=cpu
export FLAIR_CACHE_ROOT="./flair-cache"
python - <<'PY'
import flair
print(flair.device)
print(flair.cache_root)
PY
```

Operational facts:

- `flair.device` is selected at import time. With CUDA available, Flair selects `cuda:0` unless `FLAIR_DEVICE=cpu` or a specific device id is set.
- `FLAIR_CACHE_ROOT` controls Flair caches. Pretrained identifiers can populate subdirectories below it.
- Large static resources such as word vectors and BPEmb vectors default to CPU storage through `force_cpu=True` in their constructors.
- If a run changes `FLAIR_DEVICE` or `FLAIR_CACHE_ROOT`, start a new Python process or import Flair only after the variables are set.

## Choose token embeddings

### `TransformerWordEmbeddings`

Best modern default for sequence labeling or token feature extraction when transformer dependencies, cache/downloads, and runtime cost are acceptable.

```python
from flair.data import Sentence
from flair.embeddings import TransformerWordEmbeddings

sent = Sentence("The grass is green .")
embeddings = TransformerWordEmbeddings(
    model="distilbert-base-uncased",
    layers="-1",
    layer_mean=True,
    subtoken_pooling="first",
    allow_long_sentences=False,
    fine_tune=False,
)
embeddings.embed(sent)
print(embeddings.embedding_length, [tuple(tok.get_embedding(embeddings.get_names()).shape) for tok in sent])
sent.clear_embeddings()
```

Important knobs:

| Knob | Values | Use when |
| --- | --- | --- |
| `layers` | `"-1"`, `"-1,-2,-3,-4"`, `"all"` | More layers may improve frozen features but increase width when `layer_mean=False`. Use `"-1"` for most fine-tuning. |
| `layer_mean` | `True` or `False` | `True` averages selected layers and keeps one hidden-size width. `False` concatenates selected layers. |
| `subtoken_pooling` | `first`, `last`, `first_last`, `mean` | Converts subword pieces into one token vector. `first_last` doubles token width. |
| `fine_tune` | `True` or `False` | `True` enables gradients through the transformer during training and increases memory/time cost. |
| `allow_long_sentences` | `True` or `False` | Token embeddings can stride/patch over tokenizer length when true; include long examples in validation. |
| `use_context` | `False`, `True`, or integer token count | Adds neighboring sentences for FLERT-style context. This changes sequence length and boundary behavior. |
| `force_max_length` | `True` or `False` | Pads to tokenizer max length; useful for some tracing/provider workflows but slower. |
| `transformers_*_kwargs` | dictionaries | Forward tokenizer/config/model options. Use deliberately and record them with the model. |

### `TransformerEmbeddings`

Use the combined class when one object should produce token embeddings, document embeddings, or both:

```python
from flair.embeddings import TransformerEmbeddings

embeddings = TransformerEmbeddings(
    model="distilbert-base-uncased",
    is_token_embedding=True,
    is_document_embedding=True,
    cls_pooling="mean",
    layers="-1",
)
```

Prefer `TransformerWordEmbeddings` or `TransformerDocumentEmbeddings` when a downstream Flair model expects only one embedding type. The combined object can return both `token_embeddings` and `document_embeddings` internally, which complicates export/tracing validation.

### `WordEmbeddings`

Use static word vectors for classic Flair stacks, frozen features, or local custom vectors.

```python
from flair.embeddings import WordEmbeddings

# May download unless the resource is already cached.
embeddings = WordEmbeddings("glove", fine_tune=False, force_cpu=True)
```

Public identifiers include `glove`/`en-glove`, `extvec`, `turian`, `crawl`/`en-crawl`, `news`/`en-news`, `twitter`, and two-letter language codes or `-wiki`/`-crawl` variants. A local gensim or word2vec file path may also be used.

Rules:

- Named or remote resources require cache/download access and usually `gensim` support.
- Keep `force_cpu=True` for large frozen vectors unless there is a deliberate need for GPU-resident trainable vectors.
- If `fine_tune=True` while Flair is using CUDA, set `force_cpu=False`; Flair raises an error for trainable word embeddings forced to CPU during GPU training.
- Static vectors can benefit from `embeddings_storage_mode="cpu"` in repeated-epoch training when RAM is sufficient.
- Use `field="some_label"` only when tokens carry that metadata/label field and the task intentionally embeds that field rather than token text.

### `FlairEmbeddings`

Use contextual string embeddings backed by character language models.

```python
from flair.embeddings import FlairEmbeddings, StackedEmbeddings

embeddings = StackedEmbeddings([
    FlairEmbeddings("news-forward-fast", fine_tune=False),
    FlairEmbeddings("news-backward-fast", fine_tune=False),
])
```

Guidance:

- Combine forward and backward LM embeddings for most token-level tasks.
- Named models such as `news-forward`, `news-backward`, `news-forward-fast`, `multi-forward`, or language-specific `*-forward`/`*-backward` may download.
- `fine_tune=True` sends gradients into the LM. Use only for deliberate training experiments.
- `chars_per_chunk` trades speed against memory for long LM inference; reduce it when long sentences hit memory limits.
- A custom saved LM path such as `lm-output/best-lm.pt` can be passed directly.

### `PooledFlairEmbeddings`

Use only when the global word-memory behavior is desired.

```python
from flair.embeddings import PooledFlairEmbeddings

embeddings = PooledFlairEmbeddings("news-forward-fast", pooling="min")
```

The pooled variant maintains a representation for each observed word and can change over time during prediction. This can improve representations but grows memory usage and can make service behavior less deterministic. Avoid it for low-memory or reproducibility-sensitive production unless this statefulness is intentional.

### `StackedEmbeddings`

Use to concatenate several token embeddings into one token representation.

```python
from flair.data import Dictionary
from flair.embeddings import OneHotEmbeddings, StackedEmbeddings

vocab = Dictionary(add_unk=True)
for item in ["I", "love", "Berlin"]:
    vocab.add_item(item)

stack = StackedEmbeddings([
    OneHotEmbeddings(vocab, embedding_length=8, stable=True),
    OneHotEmbeddings(vocab, embedding_length=4),
])
assert stack.embedding_length == 12
```

`StackedEmbeddings` prefixes component names by default. Always call `stack.get_names()` when retrieving vectors. The final width is the sum of component widths.

### `OneHotEmbeddings`

Use for no-download baselines, fixtures, trainable lexical/task features, or embedding a token field such as a POS label.

```python
from flair.data import Dictionary
from flair.embeddings import OneHotEmbeddings

vocab = Dictionary(add_unk=True)
for word in ["The", "grass", "is", "green"]:
    vocab.add_item(word)
embeddings = OneHotEmbeddings(vocab_dictionary=vocab, field="text", embedding_length=32, stable=False)
```

`OneHotEmbeddings.from_corpus(corpus, field="text", min_freq=3, embedding_length=300)` can build a vocabulary from a corpus. One-hot embeddings are randomly initialized and only become semantically meaningful after task training.

### `BytePairEmbeddings`

Use for small subword static embeddings when BPEmb resources are available from cache/download or local files.

```python
from flair.embeddings import BytePairEmbeddings

# May download BPEmb files unless they already exist in cache.
embeddings = BytePairEmbeddings(language="en", dim=50, syllables=100000, force_cpu=True)
```

Rules:

- Flair's default vector width is `2 * dim` because it concatenates first and last subword vectors per token.
- If no `language` is supplied, provide `model_file_path`; if only a SentencePiece model is supplied, also provide `name`.
- Keep `force_cpu=True` for large static resources unless deliberately moving them.
- `field` lets the embedding read a token field instead of text; verify that field exists.

### Optional/legacy token families

- `CharacterEmbeddings` and `HashEmbeddings` are trainable no-download token embeddings useful for controlled baselines, but they were not the main requested scope.
- `FastTextEmbeddings`, `MuseCrosslingualEmbeddings`, and language-specific legacy classes require extra packages/resources and should be treated as optional unless the environment proves them.
- Image embeddings live outside this text-embedding sub-skill. For layout/OCR transformer metadata, see [Troubleshooting](troubleshooting.md#ocr-layout-and-image-model-gaps).

## Choose document embeddings

### `TransformerDocumentEmbeddings`

Best direct default for document/sentence classification when transformer runtime and resources are allowed.

```python
from flair.data import Sentence
from flair.embeddings import TransformerDocumentEmbeddings

sent = Sentence("The grass is green .")
embeddings = TransformerDocumentEmbeddings(
    model="distilbert-base-uncased",
    layers="-1",
    layer_mean=False,
    cls_pooling="cls",  # also: "mean" or "max"
    fine_tune=False,
)
embeddings.embed(sent)
assert len(sent.get_embedding(embeddings.get_names())) == embeddings.embedding_length
sent.clear_embeddings()
```

Use `cls_pooling="mean"` or `"max"` when `allow_long_sentences=True` must stride long documents. CLS pooling over strided long input is usually not beneficial.

### `DocumentPoolEmbeddings`

Use when token embeddings already exist and a simple document vector is enough. Pooling options are `mean`, `max`, and `min`.

```python
from flair.data import Dictionary, Sentence
from flair.embeddings import DocumentPoolEmbeddings, OneHotEmbeddings

vocab = Dictionary(add_unk=True)
for word in ["short", "document"]:
    vocab.add_item(word)
tok = OneHotEmbeddings(vocab, embedding_length=8)
doc = DocumentPoolEmbeddings([tok], pooling="mean", fine_tune_mode="none")
sentence = Sentence("short document")
doc.embed(sentence)
```

`fine_tune_mode` can be `none`, `linear`, or `nonlinear`. Use `none` for already trained token features or smoke checks; use `linear`/`nonlinear` when downstream training should learn a transformation before pooling.

### `DocumentRNNEmbeddings`

Use for trainable document encoders over token embeddings. They are generally meaningful only after downstream task training.

```python
from flair.embeddings import DocumentRNNEmbeddings

doc = DocumentRNNEmbeddings([tok], hidden_size=16, rnn_layers=1, bidirectional=True, rnn_type="GRU")
```

Shape rule: with `bidirectional=False`, width is `hidden_size`; with `bidirectional=True`, Flair's implementation reports `hidden_size * 4`.

### `DocumentCNNEmbeddings`

Use for a trainable CNN document encoder over token embeddings.

```python
from flair.embeddings import DocumentCNNEmbeddings

doc = DocumentCNNEmbeddings([tok], kernels=((8, 2), (8, 3)), reproject_words=True, fine_tune=True)
```

Shape rule: width is the sum of kernel counts, so `((8, 2), (8, 3))` gives width `16`. Flair pads short sentences to the largest kernel size.

### Other document options

- `DocumentLMEmbeddings` converts one or more `FlairEmbeddings` into document-level vectors by taking final forward/backward LM token states.
- `SentenceTransformerDocumentEmbeddings` requires optional `sentence-transformers` and may download the selected model.
- `DocumentTFIDFEmbeddings` requires scikit-learn and either a train dataset or a prebuilt vectorizer.

## Language-model training and reuse

Use this for planning or bounded experiments. Full LM training can require large corpora, long runtimes, and GPUs.

Expected plain-text corpus layout:

```text
corpus/
  train/
    split_1.txt
    split_2.txt
  valid.txt
  test.txt
```

Minimal CPU-sized API pattern:

```python
from flair.data import Dictionary
from flair.models import LanguageModel
from flair.trainers.language_model_trainer import LanguageModelTrainer, TextCorpus

is_forward_lm = True
dictionary = Dictionary.load("chars")
corpus = TextCorpus("corpus", dictionary, forward=is_forward_lm, character_level=True)
language_model = LanguageModel(dictionary, is_forward_lm=is_forward_lm, hidden_size=128, nlayers=1)
trainer = LanguageModelTrainer(language_model, corpus)
trainer.train("lm-output", sequence_length=10, mini_batch_size=10, max_epochs=2, checkpoint=True)
```

Installed signatures show `LanguageModelTrainer.train(base_path, sequence_length, learning_rate=20, mini_batch_size=100, anneal_factor=0.25, patience=10, clip=0.25, max_epochs=1000, checkpoint=False, grow_to_sequence_length=0, num_workers=2, use_amp=False, **kwargs)`.

Production-scale LM training commonly uses much larger corpora, `hidden_size`, `sequence_length`, and training time. For a custom language or non-Latin alphabet, build and save a matching `Dictionary` first. Keep the same dictionary when fine-tuning or reusing the LM.

Reuse after training:

```python
from flair.data import Sentence
from flair.embeddings import FlairEmbeddings

embeddings = FlairEmbeddings("lm-output/best-lm.pt")
sentence = Sentence("I love Berlin")
embeddings.embed(sentence)
sentence.clear_embeddings()
```

Fine-tune an existing LM:

```python
from flair.embeddings import FlairEmbeddings

language_model = FlairEmbeddings("news-forward", has_decoder=True).lm
is_forward_lm = language_model.is_forward_lm
dictionary = language_model.dictionary
```

Then create `TextCorpus(..., dictionary, forward=is_forward_lm)` and train with `LanguageModelTrainer`. Direction and dictionary must match the loaded LM.

## Storage modes during training and inference

When a downstream model calls `ModelTrainer.train`, `ModelTrainer.fine_tune`, or a model `.predict`, embedding storage controls memory and speed:

| Mode | Best use | Caution |
| --- | --- | --- |
| `embeddings_storage_mode="none"` | Fine-tuning transformers; large datasets; low-memory prediction | Recomputes embeddings each batch but avoids retaining tensors. |
| `"cpu"` | Static/frozen embeddings when RAM can cache tensors across epochs | Can slow GPU prediction because tensors move back to CPU. |
| `"gpu"` | Small datasets that fit in CUDA memory | Optional/unverified and can exhaust GPU memory. |

For standalone prediction, many `.predict(..., embedding_storage_mode="none")` paths clear embeddings after use. Set `"cpu"` or `"gpu"` only when the caller needs embeddings retained.

## A no-download environment smoke

The bundled helper runs API contracts and prints JSON:

```bash
python scripts/embedding_smoke.py --json
```

Optional transformer checks require explicit opt-in and may download if allowed:

```bash
python scripts/embedding_smoke.py --include-transformer --transformer-model distilbert-base-uncased --allow-downloads --json
```

Do not treat the optional transformer check as proof of CUDA, ONNX, TorchScript, or provider acceleration. It proves only that the selected transformer model can instantiate and produce expected token/document tensors in the current environment.
