# Data ingestion

## When to use it
Use data ingestion when the agent needs retrieval-backed answers, document grounding, or recurring data refresh.

## Main modes
### Vertex AI Search
- Uses a GCS data connector.
- Suits document-style corpora that can be synced from storage.
- Often pairs with simpler operational workflows.

### Vertex AI Vector Search
- Uses a pipeline-oriented ingestion path.
- Suits embedding-backed retrieval and custom chunking/processing workflows.
- Usually implies more infrastructure and more explicit dataplane configuration.

## User signals
- `agentic_rag`
- `--datastore`
- `vertex_ai_search`
- `vertex_ai_vector_search`
- `make data-ingestion`
- `make sync-data`
- `make setup-datastore`

## What to explain
- Data ingestion is a generation-time choice for some templates and an explicit flag for others.
- The chosen datastore changes generated Terraform and runtime behavior.
- The generated project may include sample data or pipeline hooks depending on the template.

## Troubleshooting cues
- Wrong datastore type chosen.
- Generated resources do not match the selected retrieval style.
- Data refresh or sync commands are missing because the template does not support that backend.
- A deployment wants project credentials or bucket permissions before syncing can work.
