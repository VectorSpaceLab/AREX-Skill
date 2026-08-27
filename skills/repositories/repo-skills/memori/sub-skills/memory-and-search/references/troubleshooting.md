# Memory and Search Troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Empty recall | attribution was skipped, the session is wrong, or the write path did not settle | set `entity_id`, keep `process_id` consistent, and wait for augmentation |
| Query validation error | the query is empty or not a string | pass a non-empty string |
| Limit validation error | the limit is missing or not a positive integer | pass a positive integer or omit the limit |
| Nothing is deleted | `delete_entity_memories(...)` was called in cloud mode | switch to BYODB mode first |
| Candidate search looks wrong | the candidate list is not the expected shape | pass `FactCandidate` objects with `content`, `score`, and `date_created` |
| TEI embed failure | the TEI response shape or timeout is wrong | verify the URL, timeout, and returned embedding payload |
| Native core unavailable | the optional Rust core is disabled or could not be imported | use the pure Python path or diagnose the native extension separately |
| Model download/bootstrap failure | an optional runtime asset could not be fetched | treat it as a separate setup step, not a default install failure |

## Recovery order

1. Confirm the memory mode and storage backend.
2. Check attribution and session continuity.
3. Use the offline candidate smoke to separate search logic from database and
   embedding issues.
4. Only then investigate TEI or native runtime setup.
