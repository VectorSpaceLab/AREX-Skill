# API reference

This page captures the BERTopic post-hoc representation and labeling contract for this sub-skill. It intentionally excludes embedding backend choice, c-TF-IDF/vectorizer tuning, plotting, and serialization.

## Integration contract

`BERTopic(representation_model=...)` accepts three shapes that matter here:

- a single `BaseRepresentation` instance
- a list of `BaseRepresentation` instances, which BERTopic applies in order as a chain
- a dict of aspect names to either a single model, a list chain, or a falsy value for the default c-TF-IDF view

Important notes:

- `Main` is the primary view in dict mode.
- Non-`Main` dict entries are stored in `topic_aspects_`.
- `get_topics(full=True)` and `get_topic(topic, full=True)` surface those aspects.
- BERTopic only forwards the precomputed-embedding shortcut to a top-level `KeyBERTInspired` instance; if you nest it inside a list or aspect dict, it will run without that shortcut.

## Representation base class

### `BaseRepresentation`

- `extract_topics(topic_model, documents, c_tf_idf, topics) -> Mapping[int, list[tuple[str, float]]]`
- Custom subclasses may keep internal state.
- The method should return a mapping with the same topic ids as the input topics.
- Each topic value should remain a list of `(term, weight)` tuples.

## Keyword rerankers and labelers

### `KeyBERTInspired(top_n_words=10, nr_repr_docs=5, nr_samples=500, nr_candidate_words=100, random_state=42)`

- Re-ranks topic keywords by comparing topic embeddings with candidate word embeddings.
- Uses representative documents plus semantic similarity to produce a cleaner keyword list.
- Needs either a live embedding backend on the topic model or a precomputed-embedding path that reaches the top-level shortcut.
- Best for semantic keyword cleanup rather than final human-readable labels.

### `MaximalMarginalRelevance(diversity=0.1, top_n_words=10)`

- Diversifies a topic’s keywords by balancing relevance and redundancy.
- Requires `topic_model.embedding_model`; without it, BERTopic warns and leaves the topics unchanged.
- Good as the first step in a chain before a label generator.

### `PartOfSpeech(model="en_core_web_sm", top_n_words=10, pos_patterns=None)`

- Uses spaCy POS patterns to extract noun-phrase-like keywords.
- `model` may be a spaCy model name or a loaded `Language` object.
- The default patterns are adjective+noun, noun, and adjective.
- Good when labels should be grammatical rather than purely semantic.

### `ZeroShotClassification(candidate_topics, model="facebook/bart-large-mnli", pipeline_kwargs={}, min_prob=0.8)`

- Classifies topic descriptions against a candidate label list.
- Uses a Hugging Face zero-shot pipeline or a compatible `transformers.pipeline` instance.
- `pipeline_kwargs["multi_label"] = True` enables multiple labels above the threshold.
- Topics below `min_prob` keep their original c-TF-IDF representation.

## Prompt-based labelers

### `TextGeneration(model, prompt=None, pipeline_kwargs={}, random_state=42, nr_docs=4, diversity=None, doc_length=None, tokenizer=None)`

- Wraps a Hugging Face text-generation or text2text-generation pipeline.
- Default prompt uses `[KEYWORDS]`; custom prompts may also use `[DOCUMENTS]`.
- `doc_length` and `tokenizer` control prompt truncation.
- `tokenizer` must be `"char"`, `"whitespace"`, `"vectorizer"`, or a callable with `encode` and `decode`.

### `OpenAI(client, model="gpt-4o-mini", prompt=None, system_prompt=None, generator_kwargs={}, delay_in_seconds=None, exponential_backoff=False, nr_docs=4, diversity=None, doc_length=None, tokenizer=None, **kwargs)`

- Uses `client.chat.completions.create(...)` and strips the `topic: ` prefix from the response.
- Default prompt and system prompt are optimized for concise topic labels.
- `exponential_backoff=True` retries rate-limited calls.
- `nr_docs`, `diversity`, `doc_length`, and `tokenizer` control the representative-document prompt.

### `LiteLLM(model="gpt-3.5-turbo", prompt=None, generator_kwargs={}, delay_in_seconds=None, exponential_backoff=False, nr_docs=4, diversity=None)`

- Uses `litellm.completion(...)` as a provider-agnostic label generator.
- The prompt should usually end with `topic: <topic label>` or an equivalent extraction instruction.
- Delay/backoff settings mirror the OpenAI wrapper.

### `LangChain(chain, prompt=None, nr_docs=4, diversity=None, doc_length=None, tokenizer=None, chain_config=None)`

- Expects a chain or Runnable with `.batch(...)` support.
- Input keys must be `input_documents` and `question`.
- Output must include `output_text`.
- Unlike the other prompt labelers, LangChain does not use `[DOCUMENTS]` inside the prompt; the chain formats the documents itself.
- `prompt` may still include `[KEYWORDS]`.

### `Cohere(client, model="command-r", prompt=None, system_prompt=None, delay_in_seconds=None, nr_docs=4, diversity=None, doc_length=None, tokenizer=None)`

- Calls `client.chat(...)` to generate a label from representative documents.
- The BERTopic wrapper itself does not import the `cohere` package, but creating the client usually requires it.
- Prompt and truncation behavior match the other LLM labelers.

### `LlamaCPP(model, prompt=None, system_prompt=None, pipeline_kwargs={}, nr_docs=4, diversity=None, doc_length=None, tokenizer=None)`

- Accepts either a local model path or a `llama_cpp.Llama` instance.
- Uses `create_chat_completion(...)` to generate the label.
- Local file paths and model-format details are caller responsibilities.

## Multimodal and visual representations

### `VisualRepresentation(nr_repr_images=9, nr_samples=500, image_height=600, image_squares=False, image_to_text_model=None, batch_size=32)`

- Builds a collage-style visual representation from topic images.
- Can also convert images to text when `image_to_text_model` is provided.
- Best treated as an additional aspect, not as the only topic view.
- Requires a document table with an `Image` column.

## Custom and chained representations

### Chain lists

- When `representation_model` is a list, BERTopic runs each tuner in order.
- Each tuner receives the previous tuner’s topic output.
- Chain order matters: rerank first, then label.

### Aspect dicts

- A dict lets you keep multiple topic views at once.
- `Main` is the primary view used by `get_topic`, `get_topics`, and the default topic table.
- Each non-`Main` aspect is stored in `topic_aspects_`.
- `topic_aspects_` may hold tuple lists or strings, and `get_topic_info()` normalizes them into table columns.

### Custom models

A custom representation model should:

1. inherit `BaseRepresentation`
2. accept the standard `extract_topics(topic_model, documents, c_tf_idf, topics)` contract
3. return a topic-to-term mapping with the same topic ids
4. keep topic values list-like so `get_topic_info()` and `generate_topic_labels()` can read them

## Label helpers on `BERTopic`

### `generate_topic_labels(nr_words=3, topic_prefix=True, word_length=None, separator="_", aspect=None) -> list[str]`

- Builds ordered labels from the fitted topics.
- When `aspect` is set, labels are read from `topic_aspects_[aspect]` instead of the main topic view.
- `topic_prefix=True` prefixes each label with the topic id.
- `word_length` truncates each word before joining.

### `set_topic_labels(topic_labels) -> None`

- Accepts either a list or a dict.
- A list must contain one label per unique topic, sorted from the lowest topic id to the highest.
- If the model contains outliers, the list order includes `-1`.
- A dict can update only selected topics; missing topics keep their previous labels.
- After setting labels, `get_topic_info()` exposes a `CustomName` column when the label count matches the topic count.

### `get_topics(full=True)` / `get_topic(topic, full=True)`

- `get_topics(full=True)` returns a mapping with `Main` plus each aspect name.
- `get_topic(topic, full=True)` returns the same idea for one topic.
- These helpers are the fastest way to confirm that an aspect pipeline actually wrote the labels you expected.

### `get_topic_info()`

- Returns the topic table with `Topic`, `Count`, `Name`, and `Representation`.
- Adds `CustomName` after `set_topic_labels` when the label count fits.
- Adds aspect columns for each entry in `topic_aspects_`.

## Common failure cues

| Symptom | Likely cause |
| --- | --- |
| `NotInstalled` placeholder for a representation class | Optional dependency missing for that class (`spacy`, `transformers`, `openai`, `litellm`, `langchain`, `llama-cpp-python`, or vision extras). |
| `KeyBERTInspired` gives no useful change | The model has no embedding backend, or the class was nested in a chain and no longer received the top-level embedding shortcut. |
| `MaximalMarginalRelevance` leaves topics unchanged | No embedding model was available. |
| `set_topic_labels` raises a length error | The list length does not match the number of unique topics, including `-1` when outliers exist. |
| `generate_topic_labels(aspect=...)` fails | The requested aspect was never created in a dict-style `representation_model`. |
| `LangChain` fails with missing keys | The chain does not accept `input_documents` and `question`, or it does not return `output_text`. |
