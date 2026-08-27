# NLP and generation API reference

## Client methods

| Method | Use it when | Important inputs | Stored key / result |
|---|---|---|---|
| `text_classification_query(instruction, label_column=None, ...)` | Train an LSTM text classifier over a selected text column. | `instruction`, `label_column`, `max_text_length`, `epochs`, `batch_size`, `learning_rate`, `test_size`, `drop` | `text_classification` with `model`, `classes`, `vocabulary`, `interpreter`, `losses`, `accuracy`, `test_data`. |
| `classify_text(text)` | Classify a new string after `text_classification_query`. | `text` | Returns the predicted class from `classes`. |
| `summarization_query(instruction, label_column=None, ...)` | Fine-tune T5-small for text summarization. | `instruction`, `label_column`, `max_text_length`, `epochs`, `batch_size`, `learning_rate`, `gpu`, `test_size` | `summarization` with `model`, `tokenizer`, `max_text_length`, `losses`, and optional plots. |
| `get_summary(text, num_beams=4, no_repeat_ngram_size=2, num_return_sequences=1, early_stopping=True)` | Generate summaries after `summarization_query`. | `text`, generation parameters | Returns a list of decoded summary strings. |
| `generate_text(file_data=True, prefix=None, max_length=512, top_k=50, top_p=0.9, temperature=0.3, return_sequences=2)` | Generate GPT-2 text from a file or prompt prefix. | `file_data`, `prefix`, sampling parameters | `text_generation` with `generated_text`. |
| `named_entity_query(instruction)` | Detect named entities in a selected text column. | `instruction` | `named_entity_recognition` with `model`, `tokenizer`, and `name_entities`. |
| `image_caption_query(instruction, label_column=None, ...)` | Train InceptionV3 + encoder/decoder captioning from image paths and captions. | `instruction`, `label_column`, `top_k`, `batch_size`, `embedding_dim`, `units`, `gpu`, `test_size` | `image_caption` with `decoder`, `encoder`, `tokenizer`, `feature_extraction`, `losses`, and plots. |
| `generate_caption(image)` | Caption a new image after `image_caption_query`. | `image` path | Returns a caption string. |
| `vocab(model=None)` | Inspect stored NLP vocabulary. | optional model key | Returns model vocabulary if present. |

## Defaults that matter
- `text_classification_query` uses `label` if `label_column` is omitted.
- `summarization_query` uses `summary` if `label_column` is omitted.
- `image_caption_query` uses the instruction as the default caption label unless `label_column` is provided.
- `generate_text` uses the client dataset file by default; prefix-only generation requires `file_data=False`.

## Runtime downloads
The NLP API can load or download NLTK corpora, TextBlob taggers, GPT-2, T5-small, default HuggingFace NER models, and InceptionV3 weights. Check cache/network constraints before running these workflows.
