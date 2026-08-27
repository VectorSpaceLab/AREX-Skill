# Python SDK API Reference

## Constructors

- `R2RClient(base_url: str | None = None, timeout: float = 300.0, custom_client=None)`
- `R2RAsyncClient(base_url: str | None = None, timeout: float = 300.0, custom_client=None)`

## Result wrappers

- `R2RResults.results` unwraps a typed response.
- `PaginatedR2RResult.results` contains the page items.
- `PaginatedR2RResult.total_entries` reports the total page count.

## Auth and client state

- `client.set_api_key(api_key)` / `client.unset_api_key()`
- `client.set_project_name(project_name)` / `client.unset_project_name()`
- `client.users.login(email, password)` sets the access token on the client.
- `client.users.refresh_token()` refreshes the login token.
- `client.users.logout()` clears the token state.

## High-frequency method families

### `system`
- `health()`, `status()`, `settings()`

### `users`
- `login()`, `refresh_token()`, `me()`, `list()`, `retrieve()`, `create_api_key()`, `list_api_keys()`, `delete_api_key()`, `update()`

### `documents`
- `create(file_path=None, raw_text=None, chunks=None, s3_url=None, ingestion_mode=None, collection_ids=None, metadata=None, ingestion_config=None, run_with_orchestration=True)`
- `retrieve()`, `list()`, `download()`, `download_zip()`, `export()`, `export_entities()`, `export_relationships()`
- `append_metadata()`, `replace_metadata()`, `delete()`, `delete_by_filter()`
- `list_chunks()`, `list_collections()`, `list_entities()`, `list_relationships()`
- `extract()`, `deduplicate()`, `search()`

### `chunks`
- `list()`, `list_by_document()`, `retrieve()`, `search()`, `update()`, `delete()`

### `collections`
- `create()`, `list()`, `retrieve()`, `retrieve_by_name()`, `update()`, `delete()`
- `add_document()`, `remove_document()`, `add_user()`, `remove_user()`, `list_documents()`, `list_users()`, `extract()`

### `retrieval`
- `search()`, `rag()`, `agent()`, `completion()`, `embedding()`

### `graphs`
- `build()`, `pull()`, `reset()`, `retrieve()`, `list()`, `list_entities()`, `list_relationships()`, `list_communities()`
- `create_entity()`, `create_relationship()`, `create_community()`, `update_community()`, `delete_community()`

### `prompts`
- `create()`, `retrieve()`, `update()`, `delete()`, `list()`

### `indices`
- `create()`, `list()`, `retrieve()`, `delete()`

## Notes

- The async client mirrors the sync method names and takes the same constructor arguments.
- The client raises an error if both access-token and API-key auth are active at once.
- Group-specific details belong in the neighboring workflow references and sibling sub-skills.
