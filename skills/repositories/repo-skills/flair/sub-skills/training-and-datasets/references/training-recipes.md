# Training Recipes for Flair Models

This reference gives CPU-first recipes for training and fine-tuning with public pip-installed Flair. It assumes the corpus and label dictionary have already been selected with `dataset-formats.md`. Model downloads, prepared dataset downloads, CUDA, ONNX/provider runtimes, SciSpaCy, `pyab3p`, and two-or-more-GPU execution are optional and unverified unless separately proven.

## Choose `ModelTrainer.train` or `ModelTrainer.fine_tune`

The installed API exposes both trainer methods:

```python
trainer = ModelTrainer(model, corpus)
trainer.train(base_path, learning_rate=0.1, mini_batch_size=32, max_epochs=100, embeddings_storage_mode="cpu", ...)
trainer.fine_tune(base_path, learning_rate=5e-5, mini_batch_size=4, max_epochs=10, embeddings_storage_mode="none", ...)
```

Use `fine_tune(...)` when trainable transformer weights or other pretrained neural encoders are updated. Its defaults are oriented around low learning rate AdamW, warmup, smaller batches, final-model evaluation, and `embeddings_storage_mode="none"`.

Use `train(...)` when most trainable parameters are a task head or RNN over frozen/static features. Its defaults are oriented around SGD, larger learning rate, annealing on validation score, more epochs, and `embeddings_storage_mode="cpu"`.

Shared trainer knobs include:

- `base_path`: output directory for models, logs, loss files, and evaluation artifacts.
- `max_epochs`, `mini_batch_size`, `eval_batch_size`, and `mini_batch_chunk_size`.
- `learning_rate`, `decoder_learning_rate`, `optimizer`, and optimizer keyword arguments such as `weight_decay` where supported.
- `train_with_dev`, `train_with_test`, `monitor_test`, and `monitor_train_sample`.
- `main_evaluation_metric=("micro avg", "f1-score")`, `exclude_labels`, and `gold_label_dictionary_for_eval`.
- `save_final_model`, `save_optimizer_state`, `save_model_each_k_epochs`.
- `create_file_logs`, `create_loss_file`, and `write_weights`.
- `reduce_transformer_vocab` when optional dependencies and the selected transformer route support it.
- `use_amp` for mixed precision; this is not verified by the CPU baseline.
- `multi_gpu`; use only inside `launch_distributed(...)` after CUDA and at least two GPUs are proven.

## Output files and model selection

A normal trainer directory can contain:

- `final-model.pt` when `save_final_model=True`.
- `best-model.pt` when dev-based best model selection is active.
- Periodic model files when `save_model_each_k_epochs` is nonzero, plus optimizer state when `save_optimizer_state=True`.
- `training.log` when `create_file_logs=True`.
- `loss.tsv` when `create_loss_file=True`.
- `weights.txt` when `write_weights=True`.
- `dev.tsv`, `test.tsv`, or split-specific evaluation TSV files.
- Serialized model metadata such as model-card content inside the saved state.

Use the saved model corresponding to the evaluation policy. If `use_final_model_for_eval=False` and a best model exists, final test evaluation normally uses the best dev checkpoint. If `use_final_model_for_eval=True`, the last epoch model is used for evaluation.

## Storage mode decision

`embeddings_storage_mode` can be `"none"`, `"cpu"`, or `"gpu"`.

- `"none"`: conservative for transformer fine-tuning and memory-constrained runs. Embeddings are recomputed and cleared.
- `"cpu"`: useful for classic static embedding workflows when host memory is sufficient.
- `"gpu"`: optional/unverified; use only after CUDA and enough device memory are explicitly proven.

If memory grows unexpectedly, first switch to `"none"`, reduce `mini_batch_size`, and use `mini_batch_chunk_size` before changing architecture.

## SequenceTagger: NER, POS, chunking, token labels

Use `SequenceTagger` for sequence labeling with span or token labels.

Transformer fine-tuning pattern:

```python
from flair.embeddings import TransformerWordEmbeddings
from flair.models import SequenceTagger
from flair.trainers import ModelTrainer

label_type = "ner"
label_dictionary = corpus.make_label_dictionary(label_type=label_type, add_unk=False)
embeddings = TransformerWordEmbeddings(
    model="distilbert-base-uncased",
    layers="-1",
    subtoken_pooling="first",
    fine_tune=True,
    use_context=True,
)
model = SequenceTagger(
    embeddings=embeddings,
    tag_dictionary=label_dictionary,
    tag_type=label_type,
    hidden_size=256,
    use_crf=False,
    use_rnn=False,
    reproject_embeddings=False,
)
trainer = ModelTrainer(model, corpus)
trainer.fine_tune("outputs/ner", learning_rate=5e-5, mini_batch_size=4, embeddings_storage_mode="none")
```

Classic frozen-feature pattern:

```python
from flair.embeddings import FlairEmbeddings, StackedEmbeddings, WordEmbeddings
from flair.models import SequenceTagger
from flair.trainers import ModelTrainer

embeddings = StackedEmbeddings([
    WordEmbeddings("glove"),
    FlairEmbeddings("news-forward"),
    FlairEmbeddings("news-backward"),
])
model = SequenceTagger(
    embeddings=embeddings,
    tag_dictionary=label_dictionary,
    tag_type="ner",
    hidden_size=256,
    use_crf=True,
)
trainer = ModelTrainer(model, corpus)
trainer.train("outputs/ner-classic", learning_rate=0.1, mini_batch_size=32, max_epochs=150)
```

Named embeddings and transformer model IDs can download unless cached or replaced by local files. For no-download smoke checks, use the embeddings sub-skill to choose local or in-memory embedding options.

## TextClassifier: document classification

Use `TextClassifier` for single-label or multi-label document classification. The label type might be `"class"`, `"topic"`, `"sentiment"`, or a task-specific layer.

```python
from flair.embeddings import TransformerDocumentEmbeddings
from flair.models import TextClassifier
from flair.trainers import ModelTrainer

label_type = "topic"
label_dictionary = corpus.make_label_dictionary(label_type=label_type)
embeddings = TransformerDocumentEmbeddings("distilbert-base-uncased", fine_tune=True)
classifier = TextClassifier(embeddings=embeddings, label_dictionary=label_dictionary, label_type=label_type)
trainer = ModelTrainer(classifier, corpus)
trainer.fine_tune("outputs/topic", learning_rate=5e-5, mini_batch_size=4, max_epochs=10, embeddings_storage_mode="none")
```

For classic classification, use `DocumentPoolEmbeddings`, `DocumentRNNEmbeddings`, or `DocumentCNNEmbeddings` over token embeddings, then choose `train(...)` or `fine_tune(...)` according to whether the embedding stack is trainable.

## SpanClassifier: classify existing spans

Use `SpanClassifier` when the corpus already contains spans and the model should assign a label to those spans, such as span typing or entity linking.

```python
from flair.embeddings import TransformerWordEmbeddings
from flair.models import SpanClassifier
from flair.trainers import ModelTrainer

label_type = "nel"
label_dictionary = corpus.make_label_dictionary(label_type=label_type, add_unk=True)
embeddings = TransformerWordEmbeddings("bert-base-uncased", fine_tune=True, use_context=True)
model = SpanClassifier(
    embeddings=embeddings,
    label_dictionary=label_dictionary,
    label_type=label_type,
    span_label_type="ner",
)
trainer = ModelTrainer(model, corpus)
trainer.fine_tune("outputs/span-classifier", mini_batch_size=4, embeddings_storage_mode="none")
```

Check that the corpus contains both the span layer named by `span_label_type` and the target label layer named by `label_type`. Candidate generators and specialized dictionaries can require extra resources; mark them optional unless verified.

## RelationClassifier and RelationExtractor

Use relation models only after confirming entity spans and relation labels.

`RelationClassifier` uses document embeddings over entity-marked text and requires entity label types:

```python
from flair.embeddings import TransformerDocumentEmbeddings
from flair.models import RelationClassifier
from flair.trainers import ModelTrainer

relation_type = "relation"
relation_dictionary = corpus.make_label_dictionary(relation_type, add_unk=False)
embeddings = TransformerDocumentEmbeddings("distilbert-base-uncased", fine_tune=True)
model = RelationClassifier(
    embeddings=embeddings,
    label_dictionary=relation_dictionary,
    label_type=relation_type,
    entity_label_types="ner",
)
trainer = ModelTrainer(model, corpus)
trainer.fine_tune("outputs/relation-classifier", embeddings_storage_mode="none")
```

`RelationExtractor` uses token embeddings and builds candidate pairs from entity spans:

```python
from flair.embeddings import TransformerWordEmbeddings
from flair.models import RelationExtractor
from flair.trainers import ModelTrainer

model = RelationExtractor(
    embeddings=TransformerWordEmbeddings("distilbert-base-uncased", fine_tune=True),
    label_type="relation",
    entity_label_type="ner",
    pooling_operation="first_last",
    train_on_gold_pairs_only=False,
)
trainer = ModelTrainer(model, corpus)
trainer.fine_tune("outputs/relation-extractor", embeddings_storage_mode="none")
```

Before training, inspect relation labels, entity labels, candidate-pair filters, negative pair policy, and whether pairs come from gold or predicted entities.

## TARSClassifier and TARSTagger

Use TARS for few-shot, zero-shot, or task-adaptive classification/tagging. Pretrained TARS model IDs and default transformer names can download; require local paths, proven cache, or explicit download approval.

Text classification setup:

```python
from flair.models import TARSClassifier
from flair.trainers import ModelTrainer

label_type = "topic"
label_dictionary = corpus.make_label_dictionary(label_type=label_type)
model = TARSClassifier(
    task_name="topic-task",
    label_dictionary=label_dictionary,
    label_type=label_type,
    embeddings="distilbert-base-uncased",
)
trainer = ModelTrainer(model, corpus)
trainer.fine_tune("outputs/tars-topic", mini_batch_size=4, embeddings_storage_mode="none")
```

Sequence tagging setup:

```python
from flair.models import TARSTagger
from flair.trainers import ModelTrainer

label_dictionary = corpus.make_label_dictionary(label_type="ner", add_unk=False)
model = TARSTagger(
    task_name="ner-task",
    label_dictionary=label_dictionary,
    label_type="ner",
    embeddings="distilbert-base-uncased",
)
trainer = ModelTrainer(model, corpus)
trainer.fine_tune("outputs/tars-ner", mini_batch_size=4, embeddings_storage_mode="none")
```

For inference-only zero-shot prediction with a loaded TARS model, route to `tagging-and-annotations` unless the task includes training or fine-tuning.

## MultitaskModel and make_multitask_model_and_corpus

Use multitask training when one run should optimize multiple model/corpus pairs. The installed API includes `MultitaskModel(models, task_ids=None, loss_factors=None, use_all_tasks=False)` and `make_multitask_model_and_corpus(mapping)`.

```python
from flair.embeddings import TransformerEmbeddings
from flair.models import TextClassifier, TokenClassifier
from flair.nn.multitask import make_multitask_model_and_corpus
from flair.trainers import ModelTrainer

shared = TransformerEmbeddings(
    "distilbert-base-uncased",
    fine_tune=True,
    is_token_embedding=True,
    is_document_embedding=True,
)

topic_model = TextClassifier(
    embeddings=shared,
    label_dictionary=topic_corpus.make_label_dictionary("topic"),
    label_type="topic",
)
ner_model = TokenClassifier(
    embeddings=shared,
    label_dictionary=ner_corpus.make_label_dictionary("ner", add_unk=False),
    label_type="ner",
)

multitask_model, multicorpus = make_multitask_model_and_corpus([
    (topic_model, topic_corpus),
    (ner_model, ner_corpus, 0.5),
])
trainer = ModelTrainer(multitask_model, multicorpus)
trainer.fine_tune("outputs/multitask", embeddings_storage_mode="none")
```

Use weights or `loss_factors` when one task dominates the data volume or loss scale. Validate each task-specific label layer after training.

## Checkpointing and resuming

The trainer methods expose periodic model saving and optimizer-state saving. Exact resume behavior can vary across installed versions, so document what is proven.

Conservative resume pattern:

1. Save model files periodically with `save_model_each_k_epochs` if mid-run recovery matters.
2. Save optimizer state with `save_optimizer_state=True` if exact resume is required.
3. Load a saved model with the appropriate class or `Classifier.load(...)`.
4. Recreate `ModelTrainer(model, corpus)` and pass a correct `epoch` value only when the installed API and saved state support that continuation path.

If optimizer state restoration is not proven, describe the run as continued fine-tuning from saved weights, not bit-exact resume.

## Minimal post-training validation

After training, run a tiny in-memory prediction that resembles the task:

```python
from flair.data import Sentence
from flair.models import SequenceTagger

model = SequenceTagger.load("outputs/ner/final-model.pt")
sentence = Sentence("Ada Lovelace wrote notes.")
model.predict(sentence)
print(sentence.get_spans("ner"))
```

For classifiers, inspect `sentence.get_labels(label_type)`. For relation models, inspect entity spans and relation labels together. For multitask models, check each task's label layer separately.
