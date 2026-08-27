# representations-labeling workflows

Use this page when the model is already fitted and you want to improve how topics are named, summarized, diversified, or exposed as multiple aspects.

## 1. Start with the simplest improvement

If the topic words are already sensible but need a cleaner ordering or less redundancy, start with one of the keyword rerankers.

- `MaximalMarginalRelevance` for diversity
- `KeyBERTInspired` for semantic keyword cleanup
- `PartOfSpeech` when grammatical noun-phrase style matters

## 2. Move to label generation

If you need a human-readable topic name, use a prompt-based labeler or a zero-shot labeler.

- `ZeroShotClassification` when you already know the candidate labels
- `TextGeneration`, `OpenAI`, `LiteLLM`, `LangChain`, `Cohere`, or `LlamaCPP` when you want generated labels or summaries
- `generate_topic_labels()` and `set_topic_labels()` when the labels already exist and only need to be assigned or renamed

## 3. Keep multiple views when one label is not enough

If the same topic needs several representations, use a dict-style `representation_model`.

```python
representation_model = {
    "Main": MaximalMarginalRelevance(diversity=0.2),
    "KeyBERT": KeyBERTInspired(),
    "Custom": my_custom_representation,
}
```

Typical checks:

- `topic_model.topic_aspects_` contains the extra views.
- `get_topics(full=True)` and `get_topic(topic, full=True)` expose those views.
- `generate_topic_labels(aspect="KeyBERT")` builds labels from the selected aspect.

## 4. Chain models when you want one model to clean up the output of another

A list-style `representation_model` runs in order.

```python
representation_model = [MaximalMarginalRelevance(diversity=0.2), TextGeneration(...)]
```

Use a chain when the first model removes redundancy and the second model turns the cleaned keywords into a short label.

## 5. Where to look when things fail

- If the reranker is unchanged, check whether the model has an embedding backend.
- If the prompt model fails, check its optional dependency and the prompt format.
- If `set_topic_labels()` raises a length problem, make sure the label list matches the unique topics, including outliers.
- If `generate_topic_labels(aspect=...)` fails, confirm that aspect name exists in `topic_aspects_`.

## 6. Good order for a label-fixing pass

1. Inspect the main topic words.
2. Add `KeyBERTInspired` or `MaximalMarginalRelevance`.
3. Decide whether a custom label or a generated label is needed.
4. Use a dict-style representation model if multiple outputs are useful.
5. Call `generate_topic_labels()` and `set_topic_labels()` only after the topic views are in place.
