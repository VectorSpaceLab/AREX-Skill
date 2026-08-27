# Pipeline Catalog

This reference summarizes txtai pipeline families relevant to deterministic workflows. Pipelines are callable objects and can be passed directly to `txtai.workflow.Task`; YAML configuration uses the lower-case class name as a top-level key.

## General Rules

- Pipelines expose a `__call__` method. A workflow task calls a pipeline with a batch/list of elements unless a task subclass prepares each element first.
- Default model-backed pipelines can download models from Hugging Face or other configured backends. For offline validation, prefer pure callables or already-cached explicit model paths.
- YAML config creates pipelines from top-level keys. Example: `summary: {path: t5-small}` creates the `summary` action for workflow tasks.
- `Application` delays dependent pipeline wiring for `similarity`, `extractor`, `rag`, and `reranker`; for `extractor` and `rag`, a missing `similarity` is filled with the application embeddings index when available.
- `textractor` and `urlretrieve` default to safe-open behavior in `Application` configuration unless overridden.

## Focused Extras

Install the smallest extra that matches the chosen pipeline family:

| Extra | Covers | Typical signals |
| --- | --- | --- |
| `txtai[pipeline-data]` | document/text extraction, segmentation, tabular data, tokenizer, URL/file conversions | imports fail for `docling`, `pandas`, `nltk`, `tika`, `beautifulsoup4`, `liteparse`, or `chonkie` |
| `txtai[pipeline-text]` | text classification helpers beyond default transformers, entity extraction, static vectors | imports fail for `gliner-py`, `sentencepiece`, or `staticvectors` |
| `txtai[pipeline-audio]` | transcription, text-to-speech, audio streams/mixing/microphone | imports fail for `sounddevice`, `soundfile`, `scipy`, `onnxruntime`, or audio backend packages |
| `txtai[pipeline-image]` | captioning, image hashing, object detection | imports fail for `pillow`, `imagehash`, or `timm` |
| `txtai[pipeline-llm]` | `LLM`/`RAG` backends through llama.cpp, LiteLLM, LiteRT | imports fail for `llama_cpp`, `litellm`, `httpx`, or LiteRT packages |
| `txtai[pipeline-train]` | trainer and ONNX export/quantization helpers | imports fail for `accelerate`, `peft`, `onnx`, `onnxmltools`, `skl2onnx`, or `onnxruntime` |
| `txtai[workflow]` | workflow extras: scheduling, service, export, image task dependencies | imports fail for `croniter`, `requests`, `xmltodict`, `openpyxl`, `pandas`, `pillow`, or `apache-libcloud` |

The standard distribution already includes core dependencies such as `torch`, `transformers`, `pyyaml`, `numpy`, and `faiss-cpu`, but optional extras are still required for many specialized families.

## Data Processing Pipelines

| YAML key | Class | Use in workflows | Notes |
| --- | --- | --- | --- |
| `textractor` | `Textractor` | Extract text from URLs, documents, HTML, PDFs, or other supported inputs before summarization/indexing | Backends such as Docling/Tika/liteparse require `pipeline-data`; URL use can require network; local file use should be filtered with `FileTask` |
| `segmentation` | `Segmentation` | Split text into sentences, paragraphs, sections, or chunks | Useful before `index` actions; one-to-many output can expand a single document into multiple rows |
| `tabular` | `Tabular` | Convert tabular files/data into text or rows | Often needs `pandas`; validate file format and column selection |
| `tokenizer` | `Tokenizer` | Tokenize text for chunk sizing or model preparation | Use explicit settings when downstream model token limits matter |
| `filetohtml` | `FileToHTML` | Convert supported local files to HTML | Requires data conversion dependencies and local readable files |
| `htmltomarkdown` / `htmltomd` | `HTMLToMarkdown` | Convert HTML into markdown-like text | Confirm actual YAML key through `PipelineFactory.list()` when using a custom environment |
| `urlretrieve` | `URLRetrieve` | Retrieve URL content before file/data processing | Network-dependent; use only when remote access is intended |

## Text Pipelines

| YAML key | Class | Use in workflows | Notes |
| --- | --- | --- | --- |
| `summary` | `Summary` | Summarize text after extraction or segmentation | Default models can download; pass an explicit `path` for reproducible environments |
| `labels` | `Labels` | Classify text against labels | Useful for deterministic routing/classification; explicit labels may be passed at call time depending on pipeline construction |
| `similarity` | `Similarity` | Score query/text similarity or support dependent extractor/reranker pipelines | Low-level indexing/search belongs in [embeddings-search](../../embeddings-search/SKILL.md) |
| `questions` | `Questions` | Answer questions over supplied context | Model-backed and download-prone; for RAG prompt details route to [agents-and-llm-orchestration](../../agents-and-llm-orchestration/SKILL.md) |
| `translation` | `Translation` | Translate each text item, commonly with `args: [fr]` in YAML | Pass language args explicitly; defaults can download translation models |
| `entity` | `Entity` | Extract named entities | Extra/model requirements vary; validate offline cache before production use |
| `reranker` | `Reranker` | Rerank candidate results | Often depends on embeddings/similarity configuration; search details route to embeddings sub-skill |
| `llm` | `LLM` | Deterministic workflow action for prompt-to-text generation | Backend/prompt/agent design belongs in [agents-and-llm-orchestration](../../agents-and-llm-orchestration/SKILL.md); this sub-skill only covers using it as a workflow action |
| `rag` / `extractor` | `RAG` / `Extractor` alias | Can be called in a workflow after context preparation | Route deep RAG setup to [agents-and-llm-orchestration](../../agents-and-llm-orchestration/SKILL.md) |

## Audio Pipelines

| YAML key | Class | Use in workflows | Notes |
| --- | --- | --- | --- |
| `transcription` | `Transcription` | Convert audio files to text before translation/indexing | Needs audio/model dependencies; use `FileTask(..., select=r"\.wav$")` or similar to avoid sending non-audio data |
| `texttospeech` / `texttoaudio` | `TextToSpeech` / `TextToAudio` | Generate speech/audio from text | Requires audio extras and output handling; can be heavyweight |
| `audiostream` / `audiomixer` / `microphone` | Audio stream helpers | Live audio or stream processing | Avoid in deterministic smoke tests; hardware/audio devices may be unavailable |

## Image Pipelines

| YAML key | Class | Use in workflows | Notes |
| --- | --- | --- | --- |
| `caption` | `Caption` | Generate captions for image files or image objects | Use `ImageTask` when converting file paths to PIL images; model downloads likely |
| `imagehash` | `ImageHash` | Produce perceptual hashes | Requires Pillow/imagehash; good for deterministic image workflows when dependency is present |
| `objects` | `Objects` | Detect objects in images | Model-backed and potentially GPU/model-download heavy |

## Training and Export Pipelines

Training helpers such as `HFTrainer`, `HFOnnx`, and `MLOnnx` belong to long-running model training/export workflows. Use them only when the user explicitly asks for training or model export. They require `txtai[pipeline-train]` plus model/training data and should not be part of lightweight workflow smoke checks.

## Input and Output Shapes

- Plain text workflows usually use `list[str] -> list[str]` or `list[dict] -> list[dict]`.
- Indexing workflows often use `(id, text, tags)` tuples. `Task` unpacks tuple element `1` by default and repacks transformed data into the same tuple shape.
- One-to-many pipelines, especially segmentation/chunking, can expand a single input into multiple outputs.
- Multi-action tasks return tuples with `merge="hstack"`, flattened row-wise output with `merge="vstack"`, joined strings with `merge="concat"`, or separate action result lists with `merge=None`.
- Model-backed pipelines may return strings, lists, dicts, tensors, or model-specific objects; inspect one small batch before wiring into an indexing or API workflow.
