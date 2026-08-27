---
name: embeddings
description: "Add embeddings to Unstructured elements with provider-specific
  encoders, credential-safe configuration, and metadata-preserving enrichment
  checks. Use when an agent needs BaseEmbeddingEncoder, EmbeddingConfig, OpenAI,
  OctoAI, Mixedbread, VoyageAI, VertexAI, Bedrock, or HuggingFace embedding
  guidance after partitioning or chunking."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Embeddings

Use this sub-skill after documents have already been partitioned or chunked into Unstructured `Element` objects and the task is to attach vector embeddings to those elements or embed a search query with the same provider.

## Start Here

1. Route upstream work first:
   - Use `partitioning` to create elements from files, URLs, HTML, text, or streams.
   - Use `chunking` before embedding when the vector store should index RAG-sized chunks rather than raw document elements.
   - Use `elements-and-metadata` when inspecting serialized element JSON or preserving coordinate/table/source metadata.
2. Select the provider module from `references/provider-reference.md` and install only the provider SDKs needed for that route.
3. Read credentials from environment variables or a secret manager at runtime; never hard-code, log, serialize, or commit API keys.
4. Instantiate the provider-specific `EmbeddingConfig` and `EmbeddingEncoder`, then call:
   - `embed_documents(elements)` to mutate and return the same element objects with `element.embeddings` populated.
   - `embed_query(query)` to produce a single query vector for retrieval.
5. Validate vector count and dimensions before persistence, especially when mixing providers or overriding model dimensions.

## Core Model

- `unstructured.embed.interfaces.EmbeddingConfig` is a Pydantic base class; concrete providers add credential, model, region, batching, or client options.
- `unstructured.embed.interfaces.BaseEmbeddingEncoder` defines `embed_documents(elements)`, `embed_query(query)`, `num_of_dimensions`, `is_unit_vector`, and `initialize()`.
- Provider implementations convert each element to text with `str(element)` before embedding, so empty text-like elements can create low-value vectors or provider errors.
- `embed_documents()` writes vectors to `element.embeddings`; it is not a separate enrichment record and generally mutates the input elements in place.
- Serialized text elements may include an `embeddings` field, but ordinary metadata fields should remain intact if the element objects are preserved.

## Safe Pattern

```python
import os
from unstructured.embed.openai import OpenAIEmbeddingConfig, OpenAIEmbeddingEncoder

config = OpenAIEmbeddingConfig(
    api_key=os.environ["OPENAI_API_KEY"],
    model_name="text-embedding-3-small",
)
encoder = OpenAIEmbeddingEncoder(config=config)
embedded_elements = encoder.embed_documents(chunks)
query_vector = encoder.embed_query("invoice due date")
```

For provider-specific names, credentials, dependency extras, batching behavior, and model caveats, use `references/provider-reference.md`.

## Metadata and Provenance

- Preserve source metadata by embedding existing `Element` objects rather than converting them to plain strings and rebuilding them.
- If downstream systems require enrichment provenance, add non-secret metadata outside the embedding vector itself, for example provider name, model name, and embedding timestamp managed by your application.
- Keep credentials and raw provider responses out of `ElementMetadata`, logs, vector-store payloads, and serialized JSON fixtures.
- If embedding chunks, preserve `metadata.orig_elements` only when retrieval or citation workflows need source traceability; otherwise omit it upstream with the `chunking` sub-skill to keep payloads smaller.

## Bundled Helpers

Use the bundled checker to verify importability and environment-variable presence without contacting providers or printing secret values:

```bash
python sub-skills/embeddings/scripts/embedding_config_check.py --provider openai
python sub-skills/embeddings/scripts/embedding_config_check.py --all --json
```

The checker intentionally does not call `get_client()`, `embed_query()`, or `embed_documents()`, because those may create SDK clients, read credential material, write provider-specific credential files, or make network calls.

## Routing Boundaries

- Raw document partitioning, OCR, table extraction, and `partition()` kwargs belong to `partitioning`.
- Chunk sizing, overlap, table chunking, and `orig_elements` decisions belong to `chunking`.
- Element JSON conversion, schema inspection, coordinates, and staging conversions belong to `elements-and-metadata`.
- Broad ingest connectors and destination vector-store writes are excluded; the in-repo embed package README notes this area moved toward Unstructured Ingest.

## Review Checklist

- Confirm the provider SDK and optional dependencies are installed before suggesting runtime embedding.
- Confirm credentials are sourced securely and never shown in code examples, logs, or serialized elements.
- Confirm `len(elements)` equals the number of returned vectors; providers use assertions for this in several implementations.
- Confirm element text is non-empty and appropriate for the provider token/model limits.
- Confirm metadata, `element_id`, table metadata, and source provenance survive after embedding.
- Confirm query vectors use the same provider/model/dimension as indexed document vectors.
