---
name: models-resources-vector
description: "Guides SuperAGI model providers, resource ingestion, knowledge
  flows, vector stores, embeddings, and storage configuration troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# SuperAGI Models, Resources, and Vector Stores

Use this sub-skill when the task is about provider selection, model API keys,
resource summarization, knowledge installation, vector DB configuration, or
embedding/vector-store behavior.

## Read First

- [references/model-provider-reference.md](references/model-provider-reference.md)
  for model source enums, provider factory behavior, and local LLM notes.
- [references/resources-and-knowledge.md](references/resources-and-knowledge.md)
  for resource storage, summarization, and knowledge flow.
- [references/vector-store-reference.md](references/vector-store-reference.md)
  for vector-store enums, factory coverage, and backend expectations.
- [references/troubleshooting.md](references/troubleshooting.md) for provider,
  storage, credential, and vector failures.
- [scripts/check_provider_config.py](scripts/check_provider_config.py) for a
  safe structural check of model/vector/resource config combinations.

## Main Topics

- Model provider enums and factories: OpenAI, Google Palm, Replicate, Hugging
  Face, and Local LLM.
- Resource storage: FILE vs S3, plus resource summarization into vector stores.
- Knowledge records and vector DB indices.
- Vector store selection and factory paths for Redis, Pinecone, Weaviate,
  Qdrant, and related enums.
- Image LLM wrappers when a task names DALL·E or Stable Diffusion.

## Safe Workflow

1. Decide whether the user is asking about providers, resources, knowledge, or
   vector stores; use the specific reference rather than general troubleshooting.
2. Check the config and credential requirements before assuming a backend is
   available.
3. Treat provider-key validation and vector-store connection checks as live
   operations that may touch external services.
4. Use the config checker for structural validation before running a live
   request.

## Boundary Notes

- API route prefixes, controllers, and CRUD endpoints belong to `api-service`.
- Tool wrappers that call model/vector providers belong to `toolkits-integrations`.
- Deployment/runtime setup and config file creation belong to
  `deployment-configuration`.
- Agent execution logic that consumes the selected provider or vector store
  belongs to `agents-workflows`.
