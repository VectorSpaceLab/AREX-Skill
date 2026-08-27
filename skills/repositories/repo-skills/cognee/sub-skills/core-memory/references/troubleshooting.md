# Core Memory Troubleshooting

Read this when a user cannot store, improve, or recall memory in Cognee.

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `remember` returns a background result that never seems finished | The caller did not await the promise-like result object. | Save the returned object and `await` it if `run_in_background=True` was used. |
| `recall` returns no results | The dataset is wrong, nothing was cognified yet, or the query is too narrow. | Confirm the dataset name/id, run `cognify` after `add`, and broaden the query or increase `top_k`. |
| `dry_run` works but the real call fails | The estimate is not a substitute for provider credentials or backend readiness. | Install/configure the selected provider/backend, then retry without `dry_run`. |
| A session-backed call stores nothing useful | `session_id` is missing or the payload is just an uploaded-file placeholder. | Pass a real session id and chat-like content; avoid file-only placeholders for session cache writes. |
| `forget` does not remove what the user expects | The command targets a dataset, a data id, or all memory depending on arguments. | Recheck whether the user asked for one data item, one dataset, or all owned memory. |
| A remembered item does not improve the graph | `self_improvement=False` was used, or the background improve path is disabled/unavailable. | Re-run with `self_improvement=True`, or call `improve(...)` explicitly. |
| Session memory and permanent graph memory feel mixed together | The same `session_id` was reused for multiple unrelated tasks. | Use a dedicated session per task or agent role. |

## Safe next checks

1. Run the bundled smoke helper:

   ```bash
   python scripts/cognee_memory_smoke.py --help
   ```

2. Inspect the exact `remember`/`recall` signatures from the installed package.
3. If the problem is backend/provider related, route to
   [configuration-backends](../../configuration-backends/SKILL.md).
