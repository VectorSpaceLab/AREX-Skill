# Flair API Overview

This reference summarizes the public package surface verified for Flair 0.15.1. Use it to orient a workflow before reading a narrower sub-skill.

## Package facts

| Fact | Value |
| --- | --- |
| Distribution name | `flair` |
| Import name | `flair` |
| Version snapshot | `0.15.1` |
| Python requirement | `>=3.9` |
| Verified baseline | CPU PyTorch package workflows |
| Optional/unverified here | CUDA/multi-GPU, ONNX/provider runtimes, SciSpaCy model, pyab3p, large model/data downloads |

Global runtime variables are selected when `flair` is imported:

```python
import flair
print(flair.__version__)
print(flair.device)
print(flair.cache_root)
```

Set `FLAIR_DEVICE` and `FLAIR_CACHE_ROOT` before importing `flair` if the workflow needs a deliberate device or cache location.

## Core data and annotations

Key constructors/signatures verified in the installed package:

```python
from flair.data import Corpus, DataPair, Dictionary, MultiCorpus, Relation, Sentence

Sentence(text, use_tokenizer=True, language_code=None, start_position=0)
Relation(first_span, second_span)
Dictionary(add_unk=True)
Corpus(train=None, dev=None, test=None, name="corpus", sample_missing_splits=True, random_seed=None)
MultiCorpus(corpora, task_ids=None, name="multicorpus", **corpusargs)
```

Important methods:

```python
sentence.get_labels(label_type=None)
sentence.get_spans(label_type=None)
sentence.to_dict()
Sentence.from_dict(payload)
corpus.make_label_dictionary(label_type, min_count=1, add_unk=True, add_dev_test=False)
corpus.downsample(percentage=0.1, downsample_train=True, downsample_dev=True, downsample_test=True, random_seed=None)
Dictionary.load(name)
```

Use [`../sub-skills/tagging-and-annotations/SKILL.md`](../sub-skills/tagging-and-annotations/SKILL.md) for label-layer discipline, tokenization, prediction output extraction, and serialization.

## Tokenization and splitting

Verified public constructors include:

```python
from flair.tokenization import NoTokenizer, SciSpacyTokenizer, SegtokTokenizer, SpaceTokenizer, SpacyTokenizer, StaccatoTokenizer, JapaneseTokenizer
from flair.splitter import NewlineSentenceSplitter, NoSentenceSplitter, SciSpacySentenceSplitter, SegtokSentenceSplitter, SpacySentenceSplitter, TagSentenceSplitter
```

CPU-baseline tokenizers/splitters include SegTok, space/no tokenizers, Staccato, newline/no/tag splitters, and SegTok sentence splitting. spaCy, SciSpaCy, Japanese/Konoha backends, and their models are optional dependencies.

## Corpus and dataset loaders

Common public loaders:

```python
from flair.data import MultiCorpus
from flair.datasets import ColumnCorpus, ClassificationCorpus, CSVClassificationCorpus
from flair.datasets.sequence_labeling import JsonlCorpus, MultiFileJsonlCorpus
```

In the evidenced version, `JsonlCorpus` and `MultiFileJsonlCorpus` are implemented in `flair.datasets.sequence_labeling`. If `from flair.datasets import JsonlCorpus` fails, import them from `flair.datasets.sequence_labeling`.

Use [`../sub-skills/training-and-datasets/SKILL.md`](../sub-skills/training-and-datasets/SKILL.md) for concrete schemas, split behavior, label dictionaries, and training.

## Embeddings

Verified embedding constructors include:

```python
from flair.embeddings import (
    BytePairEmbeddings,
    DocumentCNNEmbeddings,
    DocumentPoolEmbeddings,
    DocumentRNNEmbeddings,
    FlairEmbeddings,
    OneHotEmbeddings,
    PooledFlairEmbeddings,
    StackedEmbeddings,
    TransformerDocumentEmbeddings,
    TransformerEmbeddings,
    TransformerWordEmbeddings,
    WordEmbeddings,
)
```

Representative signatures:

```python
TransformerEmbeddings(model="bert-base-uncased", fine_tune=True, layers="-1", layer_mean=True, subtoken_pooling="first", cls_pooling="cls", is_token_embedding=True, is_document_embedding=True, allow_long_sentences=False, use_context=False, respect_document_boundaries=True, ...)
TransformerWordEmbeddings(model="bert-base-uncased", is_document_embedding=False, allow_long_sentences=True, **kwargs)
TransformerDocumentEmbeddings(model="bert-base-uncased", layers="-1", layer_mean=False, is_token_embedding=False, **kwargs)
WordEmbeddings(embeddings, field=None, fine_tune=False, force_cpu=True, stable=False, ...)
FlairEmbeddings(model, fine_tune=False, chars_per_chunk=512, ...)
StackedEmbeddings(embeddings, overwrite_names=True)
DocumentPoolEmbeddings(embeddings, fine_tune_mode="none", pooling="mean")
```

Use [`../sub-skills/embeddings-and-optimization/SKILL.md`](../sub-skills/embeddings-and-optimization/SKILL.md) for family selection, vector shapes, storage modes, language model reuse, and optional transformer optimization.

## Models and prediction

Public model routes include:

```python
from flair.nn import Classifier
from flair.models import (
    EntityMentionLinker,
    LanguageModel,
    Lemmatizer,
    MultitaskModel,
    PrefixedSequenceTagger,
    RegexpTagger,
    RelationClassifier,
    RelationExtractor,
    SequenceTagger,
    SpanClassifier,
    TARSClassifier,
    TARSTagger,
    TextClassifier,
    TextRegressor,
    TokenClassifier,
)
```

Common loaders/predictors:

```python
Classifier.load(model_path_or_id)
SequenceTagger.load(model_path_or_id)
TextClassifier.load(model_path_or_id)
SequenceTagger.predict(sentences, mini_batch_size=32, label_name=None, force_token_predictions=False, embedding_storage_mode="none")
TARSClassifier.predict_zero_shot(sentences, candidate_label_set, multi_label=True)
EntityMentionLinker.load(model_path_or_id)
EntityMentionLinker.predict(sentences, top_k=1, pred_label_type=None, entity_label_types=None, batch_size=None)
```

`Classifier.load(...)` is the preferred general route for public pretrained model IDs because it dispatches to the right classifier type. Concrete class loaders are useful when the task specifically needs class-specific methods.

## Training

Training APIs:

```python
from flair.trainers import ModelTrainer, LanguageModelTrainer, TextCorpus

ModelTrainer(model, corpus)
ModelTrainer.train(base_path, learning_rate=0.1, mini_batch_size=32, max_epochs=100, embeddings_storage_mode="cpu", ...)
ModelTrainer.fine_tune(base_path, learning_rate=5e-5, mini_batch_size=4, max_epochs=10, embeddings_storage_mode="none", multi_gpu=False, ...)
LanguageModelTrainer(model, corpus)
LanguageModelTrainer.train(base_path, sequence_length, learning_rate=20, mini_batch_size=100, max_epochs=1000, ...)
```

Use `fine_tune` for transformer fine-tuning and low learning rates. Use `train` for classic/randomly initialized decoders over frozen/static features. Store outputs only in a user-selected directory.

## Biomedical APIs

Biomedical routes:

```python
from flair.nn import Classifier
from flair.models import EntityMentionLinker
from flair.models.entity_mention_linking import BioSynEntityPreprocessor, Ab3PEntityPreprocessor, load_dictionary
from flair.datasets.entity_linking import InMemoryEntityLinkingDictionary
from flair.data import EntityCandidate

ner = Classifier.load("hunflair2")          # may download
linker = EntityMentionLinker.load("disease-linker")  # may download
```

Use [`../sub-skills/biomedical-nlp/SKILL.md`](../sub-skills/biomedical-nlp/SKILL.md) for HunFlair/HunFlair2 workflows, biomedical corpora, entity linking, dictionaries, SciSpaCy, and abbreviation handling.
