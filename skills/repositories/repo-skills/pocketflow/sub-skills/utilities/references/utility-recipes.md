# PocketFlow utility recipes

Utilities are the external functions that PocketFlow nodes call from `exec()` or from an async node method. Keep them small, deterministic when possible, and explicit about required environment variables or services.

## 1. LLM wrapper

### Goal
Provide one local helper that sends a prompt or messages to a provider API.

### Good contract
- Input: prompt string or chat message list
- Output: text response
- Required config: API key in an environment variable
- Optional config: model name, base URL, timeout, cache, streaming support

### Good practices
- Keep provider-specific code out of graph nodes.
- Log prompts and responses only when privacy policy allows it.
- Add a non-network smoke path for import and argument validation.

## 2. Search wrapper

### Goal
Search the web or another index and return structured results.

### Good contract
- Input: query string
- Output: list of result dictionaries or a parsed response object
- Required config: search API key or endpoint

### Good practices
- Normalize the result shape before nodes consume it.
- Preserve titles, snippets, and links if available.
- Treat network failures as retriable outside the graph when possible.

## 3. Chunking helper

### Goal
Split large text into manageable chunks for map-reduce or RAG.

### Good contract
- Input: text plus chunk size or boundary policy
- Output: list of strings

### Good practices
- Keep the chunking strategy simple first.
- Ensure the helper returns an empty list for empty input.
- Make the chunk size visible to the caller.

## 4. Embedding helper

### Goal
Turn text into a numeric vector.

### Good contract
- Input: text string
- Output: list of floats or a vector-like object
- Required config: embedding provider credentials or local model weights

### Good practices
- Validate vector dimension before storing or querying.
- Use the same embedding family for indexing and query time.
- Keep the output type stable across calls.

## 5. Vector search helper

### Goal
Store vectors and retrieve nearest neighbors.

### Good contract
- Input: query vector, index or collection handle, top-k
- Output: matched ids or payloads

### Good practices
- Check vector dimensionality.
- Document backend choice: FAISS, Chroma, Qdrant, Milvus, Redis, or a service API.
- Keep the query helper separate from indexing.

## 6. TTS and audio helper

### Goal
Convert text to speech or read audio from a device.

### Good contract
- Input: text or audio buffer
- Output: file path, bytes, or waveform buffer
- Required config: API key, local audio backend, or device permissions

### Good practices
- Keep microphone capture and playback outside the graph runtime.
- Document platform-specific packages such as PortAudio when needed.
- Offer a local no-audio validation path if possible.

## 7. Database helper

### Goal
Read from or write to SQLite or another data store.

### Good contract
- Input: connection information and query or payload
- Output: rows, records, or status object

### Good practices
- Use parameterized queries.
- Close connections or context-manage them.
- Keep schema checks close to the calling node.

## 8. Streaming helper

### Goal
Expose partial LLM responses or long-running job progress.

### Good contract
- Input: prompt or work item
- Output: chunks, events, or progress updates

### Good practices
- Keep the streaming transport separate from node logic.
- Support a fake or deterministic mode for local checks.
- Document cancellation or interruption behavior.

## 9. Secure environment handling

### Patterns
- Read keys from environment variables.
- Fail with a clear message when a required key is missing.
- Provide a small validation function that checks the environment without making a network request.
- Do not hardcode secrets in runtime files.

## 10. Utility layering

A healthy PocketFlow app often uses this layering:

- node: workflow logic and state routing
- utility: provider or service interaction
- config: environment variables and small CLI parsing
- validation: local smoke or schema checks

That separation keeps graph logic understandable and reusable.
