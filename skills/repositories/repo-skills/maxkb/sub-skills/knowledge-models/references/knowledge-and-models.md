# Knowledge and model surfaces

## Knowledge/RAG surface
- `apps/knowledge/urls.py` exposes the workspace knowledge tree for knowledge bases, documents, paragraphs, termbases, problems, exports, tags, sync, embedding, hit tests, workflow publishing, and datasource hooks.
- `apps/knowledge/task/embedding.py`, `sync.py`, `generate.py`, and `handler.py` cover the async document lifecycle.
- `apps/knowledge/vector/pg_vector.py` implements vector search against PostgreSQL/pgvector.
- `apps/knowledge/models/*` carries the knowledge and action state used by the views and tasks.

## Provider abstraction
- `apps/models_provider/base_model_provider.py` defines `IModelProvider`, `BaseModelCredential`, `MaxKBBaseModel`, `ModelTypeConst`, `ModelInfo`, and `ModelInfoManage`.
- Model types include LLM, EMBEDDING, STT, TTS, IMAGE, TTI, RERANKER, TTV, and ITV.
- `apps/models_provider/urls.py` exposes provider/model CRUD, parameter forms, download controls, and shared-model endpoints.
- `apps/models_provider/impl/*` contains vendor-specific provider implementations.

## Local model runtime
- `apps/local_model/urls.py` exposes validation, embedding, compression, and unload endpoints for the local model server.
- The local provider registers the bundled sentence-transformer embedding model and reranker defaults.
- `SERVER_NAME=local_model` is the switch that activates the local-model URL profile and associated routes.

## Interaction map
- Knowledge search depends on a usable embedding or reranker model.
- Provider failures often surface as knowledge failures, so check the model catalog before blaming the vector store.
- The local model service is a runtime dependency for some embedding/reranker checks but not for every knowledge route.

## Validation notes
- A static route/catalog script is usually enough to prove surface coverage.
- Optional live verification needs the database, vector extension, and the relevant model providers or local service.
