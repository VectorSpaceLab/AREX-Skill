# Ingestion Troubleshooting

| Symptom | Likely cause | Recovery |
|---|---|---|
| upload returns task id forever pending | no worker, wrong broker/result backend, wrong queue | verify Redis, worker process and queue routing; do not re-upload repeatedly |
| parser reports unsupported type | extension/MIME mismatch or optional parser missing | test a tiny valid fixture; verify required parser/system package |
| PDF/image has no text | scanned input and OCR disabled/unavailable | enable selected OCR path; validate one page; bound memory/cost |
| audio source is empty | STT provider/key/model/optional backend failed | transcribe a short safe clip and inspect transcript before indexing |
| connector callback succeeds but files cannot sync | expired/wrong user session, scope, tenant/site id, worker cannot decrypt credentials | revalidate session and selected resource; inspect sanitized worker error |
| URL/crawler blocked | URL safety policy rejects private/link-local/redirect target | do not disable SSRF controls; use an approved reachable endpoint |
| source config patch returns 400 | extra key, invalid range/strategy, incoherent pre-screen, attempted `kind` change | run bundled validator; use dedicated Wiki/GraphRAG action |
| chunking change has no visible effect | existing chunks were not re-ingested | re-ingest source and verify new chunk metadata/count |
| task succeeds but retrieval is empty | parser produced no chunks, embedding/vector write failed, or retrieval misconfigured | inspect source/chunks first, then route to retrieval troubleshooting |
| worker memory spikes | large archive/table/PDF, OCR, parser queue buffering | enforce limits, lower Docling queue size, split parsing worker, recycle child |
| repeated sync duplicates or loses content | loader-specific reconciliation semantics misunderstood | test on a disposable source; compare stable remote ids and chunk counts |

## Safe evidence

Capture source type/id, task id/status, filename without sensitive path, parser class, chunk count, configured strategy, embedding/vector-store identity, and sanitized error. Never copy connector tokens or document content into logs.

Stop before destructive re-ingestion of a production source unless backups, citation/source-id impact, expected downtime, and rollback are understood.
