# Model Install and Records

InvokeAI stores model metadata in model records and performs install/import work through a separate installer service. Keep record edits, file moves, downloads, and deletion semantics distinct.

## Record Operations

A model record service supports:

| Operation | Meaning |
| --- | --- |
| `add_model(config)` | Add a validated config. Duplicate keys or duplicate uniqueness constraints raise duplicate errors. |
| `get_model(key)` | Fetch a full config by database key. Unknown keys raise an unknown-model error. |
| `get_model_by_hash(hash)` / `search_by_hash(hash)` | Find reinstalled or recalled models by stable hash. External records use synthetic provider hashes. |
| `search_by_attr(name, base, type, format)` | Filter by exact attributes; no filters means all models. |
| `search_by_path(path)` | Find records pointing to a path. |
| `update_model(key, changes, allow_class_change=False)` | Patch fields with validation. Changing class-defining fields requires class-change-aware update. |
| `replace_model(key, new_config)` | Replace after re-identification while preserving intended key. |
| `del_model(key)` | Remove only the record. It does not imply file deletion. |

Record changes may include common fields (`name`, `path`, `description`, `source`, `source_type`, `hash`, `file_size`), taxonomy fields (`base`, `type`, `format`, `variant`, `prediction_type`), adapter defaults, trigger phrases, `config_path`, `cpu_only`, and external-provider fields. Do not blindly carry fields between classes; target-class validation should decide what is legal.

## Install Source Types

Model installs accept these source categories:

- Local path: existing file or directory. Use register/import semantics carefully because local paths may stay in place or be moved under the managed models directory.
- URL: remote checkpoint-style source, downloaded through the download queue.
- Hugging Face repo id: supports optional variant and optional subfolder syntax. Multiple subfolders can be combined for multi-part models.
- External provider: `external://provider_id/provider_model_id`, creating a provider-backed record instead of a disk-probed model.

## Register, Install, Import, Delete

- `register_path(path, config_overrides)` probes a local model and records it while keeping it at its current location.
- `install_path(path, config_overrides)` probes a local model and moves/copies it into the managed models directory before recording it.
- `heuristic_import(source, config, access_token, inplace)` guesses local/HF/URL/external source type and starts the appropriate import path.
- `import_model(source, config)` returns a job for asynchronous imports; poll job status and error fields instead of assuming immediate completion.
- `unregister(key)` removes the database record only.
- `delete(key)` removes the record and deletes files only when they are inside the managed models directory.
- `unconditionally_delete(key)` removes record and files without that managed-directory safeguard; treat this as destructive and require explicit user authorization.

## Install Jobs

Install jobs track:

- `status`: `waiting`, `downloading`, `downloads_done`, `running`, `paused`, `completed`, `error`, or `cancelled`.
- `source`, `local_path`, `inplace`, download parts, total/received bytes, and source metadata.
- `config_in` overrides and `config_out` after a successful install.
- `error`, `error_reason`, and traceback after failures.

Paused or interrupted remote installs can be restored from install markers. Completed, errored, and cancelled jobs are terminal. Restart failed jobs or individual file downloads only when the user expects network work.

## API Surface

The model manager API exposes routes for common operations through operation ids. Useful diagnostic operations include:

- `list_model_records`, `get_model_record`, `get_model_records_by_attrs`, and `get_model_records_by_hash` for record lookup.
- `list_missing_models` and `scan_for_models` for non-destructive path diagnostics.
- `reidentify_model` and bulk reidentify for re-probing existing records.
- `update_model_record` for validated metadata edits.
- `install_model`, `install_hugging_face_model`, and install job status/pause/resume/cancel/restart/prune operations.
- `delete_model` and bulk delete operations, which require careful distinction between unregistering and deleting files.
- `get_stats` and `empty_model_cache` for cache diagnostics and explicit cache clearing.
- starter model and external-provider-related endpoints for records that do not correspond to local weights.

## Missing and Orphaned Models

- Missing model scan checks records whose files are absent and skips external API records.
- Missing records should usually be repaired by restoring the path, updating the path, reidentifying a moved model, or unregistering only the missing record.
- Orphan scans find files under model storage that are not registered. Registering or deleting orphaned files is a user-visible mutation and should not be automatic in a diagnostic-only task.
- On startup, missing files are reported as warnings rather than deleting records automatically.

## External Provider Records

External models use provider fields rather than disk paths:

- `provider_id` and `provider_model_id` identify the backend and provider-specific model.
- Capabilities describe modes, reference images, negative prompts, seeds, guidance, steps, max images, size constraints, aspect-ratio presets, mask format, and required input-image modes.
- Default settings may include width, height, and number of images.
- API keys and base URL overrides belong to operations configuration, not model records.
- External records are not probed from disk; failed external generation should be triaged through provider configuration, provider status, and capability mismatches.

## Hash and Source Notes

- Disk models compute a model hash during classification; the configured hashing algorithm affects cost and output.
- `get_by_hash` is useful when a model was deleted and reinstalled with a new key.
- External records populate a synthetic hash based on provider and provider model id.
- A changed `path` without a changed `hash` can hide moved/mismatched weights; prefer reidentification when the file changed.