# Compatibility

## Version and runtime baseline

- Package: `quivr-core 0.0.33`
- Python: `>= 3.11`
- Minimum verified smoke path: CPU-only
- Default vector-store backend in the verified path: FAISS

## Optional backend families

These backends are useful, but they are not part of the minimum smoke path:

- `unstructured`-backed parsers for Markdown, PDF, DOCX, EPUB, ODT, and related document types
- Tika server support for PDF parsing
- MegaParse-backed document parsing
- Web search via Tavily when `TAVILY_API_KEY` is present
- Live provider calls for OpenAI, Anthropic, Mistral, Gemini, Groq, Azure, Cohere, or Jina

## Function-calling heuristic

The RAG layer uses a model-name heuristic to decide whether function calling is supported.
In this snapshot, model names containing `llama2`, `test`, or `ollama3` are treated as non-tool-calling.

## Serialization boundary

`Brain.save(...)` and `Brain.load(...)` are only reliable for the supported
serialization path: OpenAI embeddings plus FAISS. Do not imply that fake
embeddings or arbitrary vector stores are portable.

## Documentation drift note

Some older docs or examples still use legacy wording such as `max_input_tokens`
or omit the current `run_id` requirement. When that happens, trust the live API
and the bundled smoke scripts over the older snippet.
