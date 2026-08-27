# Flair Model and Workflow Selection

Use this reference when a future task asks which Flair class, pretrained model, embedding family, or training route to start from.

## First decide the task shape

| User task | Primary Flair route | Where to continue |
| --- | --- | --- |
| Named entity recognition, POS, chunking, frame tagging, or other token/span prediction | `Classifier.load(model_id)` or `SequenceTagger.load(model_id)` | `tagging-and-annotations` for prediction and label extraction; `training-and-datasets` for fine-tuning. |
| Sentiment or document/text classification | `Classifier.load("sentiment")`, `TextClassifier.load(...)`, or `TextClassifier(...)` | `tagging-and-annotations` for inference; `training-and-datasets` for custom text classifier training. |
| Zero/few-shot text classification or tagging | `TARSClassifier` or `TARSTagger` | `training-and-datasets` for task switching and training. |
| Custom sequence labeling | `ColumnCorpus` / JSONL corpus + token embeddings + `SequenceTagger` + `ModelTrainer` | `training-and-datasets` and `embeddings-and-optimization`. |
| Span classification or entity-linker-style span labels | `SpanClassifier` over pre-existing spans | `training-and-datasets`; biomedical linking belongs in `biomedical-nlp`. |
| Relation extraction/classification | `RelationExtractor` or `RelationClassifier` | `training-and-datasets`; use annotation guidance to verify entity/relation layers. |
| Biomedical NER and entity normalization | `Classifier.load("hunflair2")` plus `EntityMentionLinker` | `biomedical-nlp`. |
| Embedding/vector export | `Transformer*Embeddings`, `WordEmbeddings`, `FlairEmbeddings`, `Document*Embeddings` | `embeddings-and-optimization`. |
| Language-model training and reuse as string embeddings | `LanguageModel`, `TextCorpus`, `LanguageModelTrainer`, then `FlairEmbeddings(path)` | `embeddings-and-optimization`. |

## Pretrained loading rules

Prefer the generic loader when using public model identifiers:

```python
from flair.nn import Classifier
model = Classifier.load("ner")        # dispatches to the right classifier type
model.predict(sentence)
```

Use concrete loaders only when the task needs the concrete type:

```python
from flair.models import SequenceTagger, TextClassifier
sequence_tagger = SequenceTagger.load("ner")
text_classifier = TextClassifier.load("sentiment")
```

Model-name loading can download public assets. Confirm download/cache policy before loading public names in constrained or offline environments.

Common public model IDs from Flair tutorials include:

| Area | Example IDs | Notes |
| --- | --- | --- |
| English NER | `ner`, `ner-fast`, `ner-large` | Span-style NER output on the `ner` layer by default. |
| POS / UPOS / chunking | `pos`, `pos-fast`, `upos`, `chunk` | Usually token-label workflows; check target layer. |
| Frame / relation models | `frame`, `relations` | Inspect output label layers and relation/span types after prediction. |
| Text sentiment | `sentiment`, `sentiment-fast` | Sentence-level labels. |
| Biomedical NER | `hunflair2`, legacy `hunflair`, entity-specific legacy models | Route to biomedical guidance; models may need biomedical tokenization/linking context. |

If a concrete class loader fails for a public ID, retry with `Classifier.load(model_id)` because the public ID may map to a subclass that is not the class you selected.

## Training method selection

| Situation | Use | Why |
| --- | --- | --- |
| Fine-tuning a transformer backbone | `ModelTrainer.fine_tune(...)` | Uses AdamW-style fine-tuning defaults, warmup, low learning rate, and `embeddings_storage_mode="none"` by default. |
| Training a classic Flair model over frozen/static embeddings or random decoder | `ModelTrainer.train(...)` | Uses classic SGD/annealing defaults. |
| Memory-constrained transformer fine-tuning | `fine_tune(..., mini_batch_chunk_size=..., embeddings_storage_mode="none")` | Chunks large batches and avoids retaining embeddings. |
| Multi-task learning | `MultitaskModel` or `flair.nn.multitask.make_multitask_model_and_corpus(...)` | Combines child models/corpora with optional task IDs and loss factors. |
| Biomedical multi-corpus NER | `PrefixedSequenceTagger` plus biomedical corpora | Keeps entity-type prompts and corpus-specific labels explicit. |
| Multi-GPU local fine-tuning | `launch_distributed(main, multi_gpu=True)` and `ModelTrainer.fine_tune(..., multi_gpu=True)` | Optional CUDA-only route; CPU smoke does not prove this. |

Always create a user-chosen output directory and test the saved model with one prediction before treating a training run as usable.

## Embedding family selection

| Need | Start with | Trade-offs |
| --- | --- | --- |
| Modern token/span tagging | `TransformerWordEmbeddings` or `TransformerEmbeddings(is_token_embedding=True)` | Strong defaults, but model downloads and GPU/CPU cost may be high. |
| Document classification | `TransformerDocumentEmbeddings` or `DocumentPoolEmbeddings` | Transformer document vectors are direct; pooling over token embeddings is more transparent. |
| No-download smoke/unit tests | `OneHotEmbeddings` + `DocumentPoolEmbeddings` | Safe and deterministic enough for API plumbing, not quality. |
| Classic high-quality stack | `StackedEmbeddings([WordEmbeddings(...), FlairEmbeddings(...)])` | Named static/LM resources may download and use large memory. |
| Domain-specific string context | Train/fine-tune `LanguageModel`; reuse with `FlairEmbeddings(path)` | Requires corpus layout and compute; preserve LM direction and dictionary. |
| Production latency work | PyTorch baseline first, then optional ONNX/JIT/export comparisons | Provider/runtime packages and numeric comparisons are required before claiming speedups. |

## Layer and output selection

- Sequence/span prediction usually writes to a layer such as `ner`, `pos`, or a model-specific default.
- Text classification writes sentence-level labels.
- Biomedical linkers read NER spans from `ner` or custom layers and write concept IDs to `link` or a custom linking layer.
- Pass `label_name="new_layer"` or `pred_label_type="new_link_layer"` when preserving gold/manual labels or separating multiple model outputs.
- Use `sentence.get_labels(layer)`, `sentence.get_spans(layer)`, and `sentence.get_relations(layer)` instead of unqualified `get_labels()` in production code.

## When not to use this Flair skill alone

- If the task is generic Hugging Face `transformers` fine-tuning without Flair data structures, use a Transformers-oriented workflow instead.
- If the task needs OCR generation, image preprocessing, or layout extraction, this skill only covers how Flair consumes token `bbox` and sentence `image` metadata; use an OCR/document processing workflow for the upstream extraction.
- If the task needs long benchmarks, hyperparameter sweeps, or production service packaging, use this skill for Flair APIs and combine it with an MLOps/tracking/deployment workflow.
