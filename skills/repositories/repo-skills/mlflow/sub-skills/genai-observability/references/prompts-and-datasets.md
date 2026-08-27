# Prompts And Datasets

## Prompt Registry

- Prefer `mlflow.genai.register_prompt`, `mlflow.genai.load_prompt`, and `mlflow.genai.search_prompts` for new GenAI work. Legacy top-level prompt APIs may still exist but can emit migration warnings.
- Prompt templates can be text templates or chat-message lists. Chat templates must include message dictionaries with `role` and `content`.
- `register_prompt` creates prompt versions and can record commit messages, tags, response format schemas, and model configuration where supported.
- `load_prompt` accepts name/version forms and `prompts:/...` URIs, including alias forms such as `prompts:/name@production` and latest-style aliases.
- `set_prompt_alias` and `delete_prompt_alias` move aliases between versions; cache behavior means tests that reassign aliases should bypass cache or wait for linkage threads when needed.
- `set_prompt_tag`, `set_prompt_version_tag`, `set_prompt_model_config`, and corresponding delete/get APIs support routing, ownership, model parameters, and evaluation metadata.

## Prompt Linkage

- Loading a prompt during an active run links prompt metadata to that run.
- Loading a prompt inside a traced function can link prompt version information into trace metadata/tags in recent MLflow versions.
- Preserve prompt linkage during refactors by pinning either an immutable version or an alias update plan, and by tagging traces/evaluation rows with prompt name and version/alias.

## GenAI Datasets

- `mlflow.genai.create_dataset(name=..., experiment_id=..., tags=...)` creates evaluation datasets; local stores use MLflow tracking datasets and Databricks tracking URIs delegate to Databricks agent datasets.
- `search_datasets`, `get_dataset`, `delete_dataset`, `set_dataset_tags`, and `delete_dataset_tag` manage dataset discovery and metadata.
- In local/non-Databricks environments, `dataset_id` is the unambiguous handle for get/delete; in Databricks environments, `name` is used and tags may be Unity Catalog managed.
- Dataset records used by GenAI evaluation should contain stable `inputs`, optional `outputs`, and optional `expectations`. Keep secrets and raw credentials out of datasets.

## Refactor Checklist

- Preserve prompt names when downstream traces/evaluations search by prompt identity.
- Reassign aliases intentionally and document whether `production` points at a newly tested version.
- Keep response formats and model configs compatible with consumers before changing templates.
- Link datasets to the relevant experiment ids so `search_traces` and `evaluate` see the same application slice.
- Tag datasets and traces with app version, prompt version/alias, scorer version, and evaluation purpose.
