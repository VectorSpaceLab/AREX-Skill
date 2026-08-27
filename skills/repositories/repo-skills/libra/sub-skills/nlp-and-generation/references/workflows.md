# NLP and generation workflows

## Text classification

1. Prepare a CSV with one text column and one label column.
2. If the label column is not named `label`, pass `label_column="..."`.
3. Keep the instruction close to the text column name.
4. Train with small `epochs` first, then call `classify_text`.

```python
from libra import client

c = client("reviews.csv")
c.text_classification_query("classify review_text", label_column="sentiment", epochs=1, max_text_length=32)
print(c.classify_text("the service was fast and friendly"))
```

## Summarization

1. Prepare a table with a source text column and a summary/target column.
2. Use `label_column` when the summary column is not named `summary`.
3. Expect a T5-small load or download.
4. Call `get_summary(...)` after training.

```python
c = client("articles.csv")
c.summarization_query("summarize article", label_column="abstract", epochs=1, max_text_length=128)
print(c.get_summary("Long article text goes here."))
```

## Text generation

Use file mode when the client path is a plain text file:

```python
c = client("corpus.txt")
c.generate_text(max_length=80, return_sequences=1)
```

Use prefix mode when the user supplies a prompt rather than a text file:

```python
c = client("placeholder.txt")
c.generate_text(file_data=False, prefix="Once upon a time", max_length=80, return_sequences=1)
```

Run `scripts/smoke_text_generation.py` first if you only need to verify the API surface without fetching GPT-2 weights.

## Named entity recognition

```python
c = client("documents.csv")
c.named_entity_query("detect entities in article_text")
print(c.models["named_entity_recognition"]["name_entities"])
```

This uses a HuggingFace TensorFlow NER pipeline and stopword filtering, so cache and corpora availability matter.

## Image captioning

```python
c = client("captions.csv")
c.image_caption_query("caption_text", label_column="caption", epochs=1, top_k=1000)
print(c.generate_caption("images/example.jpg"))
```

Image captioning uses the NLP API but depends on image paths and InceptionV3 features. Use the vision sub-skill's image-layout helper if path detection is the hard part.
