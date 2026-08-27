---
name: representations-labeling
description: "Fine-tune BERTopic topic representations, labels, and multi-aspect outputs."
disable-model-invocation: true
metadata:
  disco-role: operating
  package: "BERTopic"
  package-version: "0.17.4"
  parent-skill: "bertopic"
license: MIT
---

# representations-labeling

Use this sub-skill when the task is about post-hoc topic representations, topic labeling, multi-aspect outputs, or prompt-based label generation.

## Route here for

- `KeyBERTInspired`, `MaximalMarginalRelevance`, and other keyword rerankers.
- `PartOfSpeech` keyword refinement with spaCy patterns.
- `ZeroShotClassification` against a candidate label list.
- Prompt-based labelers: `TextGeneration`, `OpenAI`, `LiteLLM`, `LangChain`, `Cohere`, and `LlamaCPP`.
- `VisualRepresentation` for image-centered or multimodal topic aspects.
- Custom `BaseRepresentation` classes, including chained representation lists and multi-aspect dicts.
- `generate_topic_labels`, `set_topic_labels`, `topic_aspects_`, `get_topic(full=True)`, and `get_topics(full=True)` when the question is about labels or aspect views.

## Route elsewhere

- Embedding backend selection, model download, or encoder troubleshooting: use the embeddings-backends sub-skill.
- c-TF-IDF, CountVectorizer, online vocabulary updates, or tokenization choices: use the vectorizers-ctfidf sub-skill.
- Core fit/transform/partial_fit, clustering, topic mutation, or topic reduction: use the topic-modeling sub-skill.
- Plotting, dashboarding, and figure interpretation belong in the analysis/visualization sub-skill.
- Save/load, hub publishing, and serialization format choices belong in the serialization sub-skill.

## Operating references

1. [`references/api-reference.md`](references/api-reference.md)
2. [`references/workflows.md`](references/workflows.md)
3. [`references/troubleshooting.md`](references/troubleshooting.md)
4. [`scripts/smoke_representations.py`](scripts/smoke_representations.py)

## Minimal decision flow

- If you only want to soften or diversify the default keywords, start with `KeyBERTInspired` or `MaximalMarginalRelevance`.
- If you need noun-phrase or POS filtering, use `PartOfSpeech` and keep a spaCy model available.
- If you already know the labels, use `ZeroShotClassification` before falling back to generated labels.
- If you want generated labels, use `TextGeneration`, `OpenAI`, `LiteLLM`, `LangChain`, `Cohere`, or `LlamaCPP` with a prompt that names the label format clearly.
- If you need several views of the same topic, use a dict `representation_model` with a `Main` pipeline plus aspect names, then inspect `topic_aspects_`.
- If you need a chained label flow, pass a list of representation models in order; each tuner sees the previous output.
- If you need `KeyBERTInspired` to use the top-level embeddings shortcut, keep it at the top level instead of hiding it inside a list or aspect dict.
- If you only need to rename topics after fitting, prefer `generate_topic_labels` or `set_topic_labels` rather than retraining.

## Verification anchors

- A chained representation model that reranks keywords and then emits a concise topic label.
- Label-setting edge cases for outlier and non-outlier topic ids.
- Multi-aspect topic retrieval through `topic_aspects_` and aspect-aware `generate_topic_labels(aspect=...)`.
