# Resources and Knowledge

## When to Read

Read this when dealing with uploaded files, resource summaries, knowledge
installation, or resource-backed agent context.

## Resource Storage

Resource records include name, storage type, path, size, type, channel, agent id,
execution id, and summary. The config controls whether resources use FILE or S3
storage paths.

- FILE storage uses local workspace-style paths configured by
  `RESOURCES_INPUT_ROOT_DIR` and `RESOURCES_OUTPUT_ROOT_DIR`.
- S3 storage requires bucket and AWS credential settings.

## Resource Manager

`ResourceManager` creates LlamaIndex documents from files or S3 objects and can
save document chunks into a selected vector store. Resource summarization is
performed by a Celery task in `superagi.worker`.

## Knowledge Flow

Knowledge records connect a named knowledge item to a vector DB index. The
controller layer includes routes to list marketplace/user knowledge, fetch
knowledge details, add/update user knowledge, install selected knowledge into an
index, and uninstall knowledge.

## Safety Notes

- Document loaders can require optional dependencies such as `unstructured`,
  PDF/PPT/docx readers, or parser libraries.
- Resource summarization may call model providers and vector stores.
- S3 paths and external vector DBs require credentials and network access.

## Practical Debugging

- Confirm `STORAGE_TYPE` before debugging resource paths.
- If FILE storage works but S3 does not, inspect bucket/key/credential settings
  before changing resource code.
- If knowledge installation fails, check both the knowledge record and the target
  vector DB index.
- If summarization does nothing, check the Celery worker and model provider
  configuration.
