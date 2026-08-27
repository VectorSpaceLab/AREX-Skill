# Backends and Extras

## Backend families to think about

| Family | Examples | Extra to check |
| --- | --- | --- |
| Vector DBs | Chroma, Qdrant, Milvus, Weaviate, Pinecone, FAISS, PGVector, SuperMemory | `vectordb` or the provider-specific extra |
| Embeddings | OpenAI, Anthropic, Google, AWS, local embedding stacks | `embeddings` |
| Loaders | PDF, Markdown, DOCX, HTML, JSON, XML, CSV, text, docling | `loaders` or a format-specific loader extra |
| OCR | EasyOCR, RapidOCR, Tesseract, PaddleOCR, DeepSeek OCR | `ocr` |

## Workflow guidance

- Use the smallest backend combination that can read the source data and answer the retrieval question.
- A smoke-level KB workflow should start with a tiny fixture and `InMemoryStorage` unless persistence is the test target.
- If a document cannot be parsed, solve the loader or OCR problem before touching the vector DB.
