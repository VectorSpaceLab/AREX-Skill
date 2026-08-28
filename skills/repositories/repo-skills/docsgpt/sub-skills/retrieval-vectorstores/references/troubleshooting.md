# Retrieval Troubleshooting

| Symptom | Likely cause | Recovery |
|---|---|---|
| no chunks returned | source empty/inaccessible, wrong source id, vector write failed, overly strict threshold, bad index/filter | confirm chunks and ownership, run classic baseline, inspect store query |
| relevant chunks rank poorly | embedding mismatch, chunking too broad/narrow, query rephrase, top-k too small | inspect raw query/embedding, compare chunk strategies and top-k on a fixed set |
| hybrid behaves like classic | non-pgvector store, no keyword candidates | use pgvector for verified keyword path or accept vector-only behavior |
| threshold appears ignored | selected store/path does not honor it | check API warnings; enforce only on supported pgvector/Mongo path |
| semantic chunking slow/costly | extra embedding calls during ingest | test on a tiny source; use recursive/markdown fallback if cost is unjustified |
| dimension/mapping error | embedding model changed without rebuilding store | provision matching dimension and re-embed all affected sources |
| pgvector returns too few filtered rows | approximate index selects global candidates before source filter | increase probes, compare exact search, rebuild/drop badly sized index with backup |
| GraphRAG enable returns 400 | flag off, store not pgvector, permission denial | validate prerequisites and source editor access |
| GraphRAG answers are vector-only | extraction pending/failed or graph empty | poll task, inspect graph endpoints and extraction error/cap |
| pre-screen drops useful chunks | candidate pool too small, screening prompt/model mismatch | compare base candidates, raise candidate/max_keep carefully or disable stage |
| retrieval latency/cost spikes | query rephrase, pre-screen batches, GraphRAG or remote embeddings | attribute each stage; disable one optional stage at a time |

Always capture the effective source config, instance allow-list, selected store, embedding identity/dimension, raw candidate count, final chunks and warnings. Do not infer a store feature from a setting name alone.
