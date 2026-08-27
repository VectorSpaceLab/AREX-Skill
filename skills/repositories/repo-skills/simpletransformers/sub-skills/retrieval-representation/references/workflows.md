# Retrieval and Representation Workflows

## Sentence representation

```python
from simpletransformers.language_representation import RepresentationModel
model = RepresentationModel("bert", "bert-base-uncased", use_cuda=False)
embeddings = model.encode_sentences(["first sentence", "second sentence"], combine_strategy="mean")
```

This downloads the model unless cached. Use it when downstream work needs vector representations rather than classification labels.

## Dense retrieval training skeleton

```python
from simpletransformers.retrieval import RetrievalArgs, RetrievalModel
args = RetrievalArgs()
args.no_save = True
args.overwrite_output_dir = True
args.num_train_epochs = 1
args.include_title = True
model = RetrievalModel(model_type="dpr", model_name="facebook/dpr-question_encoder-single-nq-base", args=args, use_cuda=False)
model.train_model(train_df)  # query_text, gold_passage, optional title
```

Exact model names and query/context encoder choices are task-dependent. Validate data first and ask before large retrieval training.

## Prediction with passages

When predicting, the model needs access to passages or an index. Confirm whether `prediction_passages` is a path, dataset, preloaded object, or indexed artifact. Missing passage/index state is a setup error.

## BEIR/MSMARCO evaluation

Use BEIR/TREC evaluation only when the user needs those benchmark metrics and has installed optional dependencies. Otherwise, keep evaluation to package-native metrics or a small synthetic retrieval check.

## Hard negatives

Before enabling hard negatives or ANCE-style refresh, verify:

1. Positive passages are correct.
2. Negative fields/lists are present and not duplicates of positives.
3. Loss flags match the data shape.
4. Training budget supports repeated mining or clustering.

## Cross-links

- Use [classification](../../classification/SKILL.md) for cross-encoder pair scoring when candidates already exist.
- Use [generative-workflows](../../generative-workflows/SKILL.md) for monoT5-style text-to-text reranking.
