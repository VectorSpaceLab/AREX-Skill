# UltraRAG UI and Storage Troubleshooting

## Purpose

Use this when the UI, chat, KB, or case-study workflow fails.

## Failure patterns

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `show ui` starts but the page is blank or 404s on assets | Frontend dist is missing or `ULTRARAG_FRONTEND_DIR` points to the wrong place | Confirm `ui/frontend/dist` exists or point the env var at a valid build directory. |
| `show case` cannot load the file | The file does not exist or is not a valid memory case JSON/JSONL file | Provide a `memory_*.json` export or a case file with `step` and `memory` entries. |
| UI startup fails with missing `fastapi` | The case-study viewer or a standalone FastAPI wrapper was imported without the extra dependency | Install `fastapi` and retry. |
| UI startup or route calls fail with DB or permission errors | `ULTRARAG_UI_STORAGE_ROOT` points to a non-writable or corrupted storage root | Move the storage root or repair the SQLite files under `ui/storage`. |
| Auth registration fails | Username violates the regex or the password is too short | Use a username starting with a letter, 3-32 chars long, and a password of at least 6 characters. |
| KB upload or visibility calls fail | Milvus is unavailable, the collection name is invalid, or the visibility mapping is malformed | Check the KB config, the Milvus connection, and the collection name/user id inputs. |
| Background chat task never completes | The task queue is full or the pipeline backend is failing | Clear completed tasks and inspect the underlying pipeline or server failure. |
| Memory sync returns nothing | No usable memory content was found for the user or the collection lookup failed | Confirm the chat history exists and that the pipeline declares memory retrieval. |

## Debugging order

1. Confirm the storage root and frontend directory.
2. Check whether the relevant data file exists.
3. Verify the SQLite database and KB config.
4. Only then inspect the pipeline or server backend that produced the data.

## Useful next checks

- `references/ui-backend.md` for the route map and data format.
- `references/storage-auth.md` for the storage tree and auth rules.
- `sub-skills/pipelines/references/troubleshooting.md` if the root cause is a
  pipeline output problem rather than the UI itself.
