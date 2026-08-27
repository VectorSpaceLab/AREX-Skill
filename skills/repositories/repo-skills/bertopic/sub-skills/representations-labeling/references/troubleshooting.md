# representations-labeling troubleshooting

Use this page when BERTopic can fit, but label generation or topic-representation tuning fails.

## Missing optional dependencies

BERTopic intentionally exposes placeholders for optional representation backends when their dependencies are not installed.

Typical placeholders include:

- `OpenAI`
- `LiteLLM`
- `LangChain`
- `LlamaCPP`
- `PartOfSpeech`
- `TextGeneration`
- `ZeroShotClassification`
- `Cohere`
- `VisualRepresentation`

What to do:

1. Confirm that the missing class is optional rather than core.
2. Install only the extra required for the workflow you are actually using.
3. Re-run the label smoke before trying a larger corpus.

## `KeyBERTInspired` or `MaximalMarginalRelevance` appears to do nothing

Likely causes:

- the fitted model has no embedding backend;
- the reranker was nested in a chain or aspect layout that changed the expected shortcut behavior;
- the topic model was not fitted yet.

Recovery:

- verify the model is fitted;
- make sure `topic_model.embedding_model` is available when the reranker needs it;
- use the embeddings-backends sub-skill if the failure is really about the encoder.

## Prompt labelers fail

Typical causes:

- wrong prompt format
- missing client or pipeline object
- missing API key or network access
- model-specific output that does not contain the expected label prefix

Recovery:

- check the prompt format in the workflow reference;
- confirm the selected backend package is installed;
- keep the prompt concise and explicit about the output shape;
- route client setup questions to the embeddings-backends sub-skill when the issue is backend creation rather than labeling logic.

## `set_topic_labels()` or `generate_topic_labels()` errors

Common symptoms:

- length mismatch for a label list
- outlier topic `-1` was forgotten
- aspect name not found
- labels were generated from the wrong aspect

Recovery:

- compare the label count to the number of unique topics;
- include the outlier when the model has one;
- inspect `topic_model.topic_aspects_` before using `aspect=...`;
- prefer a dict update when only a subset of labels should change.

## `topic_aspects_` is empty

This usually means the model was created with a single representation instead of a dict of aspects.

Recovery:

- use a dict-style `representation_model` with a `Main` view and one or more aspect names;
- then re-fit the model and call `get_topics(full=True)` again.

## `PartOfSpeech` problems

If spaCy is missing, the model is not installed and the placeholder is expected.

If spaCy is installed but the output is poor:

- confirm the language model name;
- confirm the POS patterns;
- make sure the tokens you expect exist in the corpus and are not filtered away earlier.

## `ZeroShotClassification` problems

Symptoms:

- every topic keeps the original c-TF-IDF representation
- the candidate labels look reasonable but none pass the threshold

Recovery:

- lower `min_prob` or `zeroshot_min_similarity`;
- make the candidate labels more descriptive;
- confirm that the optional transformers backend is actually installed.

## `VisualRepresentation` problems

Symptoms:

- image aspect is missing from the output
- the model complains about image data or a missing visual backend

Recovery:

- confirm that the model was fitted with image data;
- confirm the visual dependencies are installed;
- route deeper image/model questions to the embeddings-backends sub-skill because the image path starts there.
