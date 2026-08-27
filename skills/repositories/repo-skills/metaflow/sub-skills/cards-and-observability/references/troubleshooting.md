# Cards and Observability Troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `current.card['id']` appears empty | Card ID did not match allowed pattern or no card with that ID exists | Use a simple alphanumeric/underscore ID and check `card list`. |
| `current.card.append` warns with multiple cards | No single default editable card can be resolved | Add `customize=True` to one editable card or use explicit IDs. |
| Card type not found | Extension/card module not installed or type name wrong | Verify package/extension loading and list available cards. |
| Card render times out | Card rendering exceeds `timeout` or component serialization is heavy | Increase timeout carefully, reduce component payload, or use `save_errors=True` for diagnostics. |
| `card view` fails in automation | Browser/server not available | Use `card get` or `card list` instead of opening a browser. |
| Logs missing | Wrong pathspec, datastore/profile mismatch, or remote logs not synced | Query the task with Client API, verify metadata/datastore, then run `logs show` in the same context. |
