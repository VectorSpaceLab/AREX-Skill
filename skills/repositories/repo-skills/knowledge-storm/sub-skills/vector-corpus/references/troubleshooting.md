# Vector corpus troubleshooting

Use `--dry-run` or `--validate-only` before full runs. Those modes do not embed, connect to Qdrant, call LLMs, or use the network.

## CSV and schema problems

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ERROR: input path does not exist` | The CSV path is wrong for the current working directory. | Pass an absolute path or a correct relative path. |
| `ERROR: input path must end with .csv` or `Not valid file format. Please provide a csv file.` | The corpus file is not named as a CSV or is a different format. | Export to a real CSV file and pass the `.csv` path. |
| `ERROR: CSV has no header row` | Empty file or file was not exported with headers. | Re-export with a header row containing at least `content,url`. |
| `ERROR: missing required column(s): content` or `Content column content not found in the csv file.` | Header is missing exact lowercase `content`. | Rename the text column to `content` or use a conversion script. |
| `ERROR: missing required column(s): url` or `URL column url not found in the csv file.` | Header is missing exact lowercase `url`. | Add a stable id column named `url`; values may be synthetic ids. |
| `ERROR: row N has empty content` | A document row has no text to embed. | Fill the cell or remove the row. |
| `ERROR: row N has empty url` | A row cannot be cited or traced. | Fill with a stable unique id such as `doc-000123`. |
| `WARNING: duplicate url value ...` | Multiple original rows share the same source id. | Fix duplicates and rerun `validate_vector_corpus_csv.py --strict-unique-url`. |
| STORM citations point to the wrong row or repeated source ids | Duplicate `url` values were indexed. | Rebuild the collection with unique row identifiers and a fresh collection name. |
| Optional metadata appears as blank/`nan` | `title` or `description` cells were missing. | Fill optional columns with empty strings or short metadata before indexing. |

## Offline Qdrant problems

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `Please provide a folder path.` | Offline mode was selected but no vector-store path was passed. | Pass `--offline-vector-db-dir ./vector_store` or another writable directory. |
| `Error occurs when loading the vector store: ...` | The local Qdrant path is absent, locked, corrupt, or not writable/readable. | If creating from CSV, choose a writable directory. If reusing, confirm the directory exists and was created by Qdrant. |
| `Collection <name> does not exist. Please create the collection first.` | `VectorRM` loaded a Qdrant path but the requested collection name is missing. | Create/update the collection with `--csv-file-path ... --collection-name <name>`, or pass the existing collection name. |
| Empty retrieval results despite a non-empty store | Collection name, embedding model, or path does not match the indexed collection. | Verify collection name and rebuild with a fresh path/name if uncertain. |
| Local Qdrant reports a lock or storage error | Another process is using the same local Qdrant directory. | Stop the other process or use a separate offline directory per run. |

## Online Qdrant problems

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `Please provide a url for the Qdrant server.` | Online mode is selected but no URL was passed. | Pass `--online-vector-db-url https://...`. |
| `Please provide an api key.` | Online mode needs a Qdrant API key. | Set `QDRANT_API_KEY` or pass `--qdrant-api-key` if command-line secrets are acceptable. |
| `Error occurs when connecting to the server: ...` | Invalid URL, wrong API key, network block, TLS issue, or Qdrant service outage. | Verify URL/key, test network access, and retry. Use offline mode if network access is not allowed. |
| Collection is missing online | `VectorRM` only loads existing collections; it does not create one. | Create/update with `QdrantVectorStoreManager` by passing `--csv-file-path`, or create the collection by another trusted process. |
| Authorization or 403/401 response | Qdrant key lacks access to the collection/server. | Use a key with read/write access for creation and at least read access for retrieval. |

## Embedding model and dependency problems

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| First full run stalls or downloads model files | `HuggingFaceEmbeddings` is downloading `BAAI/bge-m3` or another embedding model. | Pre-download in a network-enabled environment, keep cache available, or choose an already-cached embedding model. |
| `ModuleNotFoundError` for `langchain_huggingface`, `langchain_qdrant`, `qdrant_client`, or `sentence_transformers` | The public package dependencies are incomplete in the environment. | Reinstall/upgrade `knowledge-storm` and its dependencies. |
| `ModuleNotFoundError: pandas` during vector-store creation | The vector-store builder reads CSVs with pandas in the installed package. | Install `pandas` in the runtime environment. |
| Qdrant vector-size mismatch | Collection was created with a vector dimension that does not match the selected embedding model. | Use the default `BAAI/bge-m3`, or recreate/customize the collection with the correct vector size. |
| Out-of-memory during embedding | Batch size or device memory is too high. | Reduce `--embed-batch-size`, use `--device cpu`, or split the corpus. |

## Device fallback

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| CUDA unavailable or torch CUDA assertion | `--device cuda` was chosen on a host without usable CUDA. | Re-run with `--device cpu`; CUDA is acceleration only. |
| MPS backend error | `--device mps` was chosen on non-Apple hardware or unsupported PyTorch. | Re-run with `--device cpu`. |
| Very slow embedding | CPU path is working but slow for a large corpus. | Use CUDA/MPS if available, reduce corpus size for a smoke test, or prebuild the vector store once and reuse it. |

## STORM runner and model problems

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Helper exits with `No STORM stage selected` | No `--do-research`, `--do-generate-outline`, `--do-generate-article`, or `--do-polish-article` flag was set for a full run. | Add explicit stage flags. Use `--dry-run` first if planning. |
| LiteLLM/provider authentication error | Missing model provider environment variable such as `OPENAI_API_KEY`, or wrong model/provider name. | Set the correct provider key and verify the LiteLLM model name. |
| Rate-limit or timeout during STORM research/writing | LLM provider limits or too many concurrent STORM threads. | Lower `--max-thread-num`; retry with cheaper/faster models for simulator/question asker. |
| `conversation_log.json` or outline/article file not found when resuming later stages | You skipped a stage whose output is required by the next stage. | Run the prerequisite stage or use the sibling STORM workflow guidance for stage resume. |
| `VectorRM.forward` returns duplicate-looking sources | Multiple chunks from the same source row can share one `url`, or the CSV had duplicate URLs. | This is normal for chunks from one long document; otherwise enforce unique row URLs and rebuild. |

## Safe diagnosis commands

```bash
python scripts/validate_vector_corpus_csv.py --input-path corpus.csv --strict-unique-url
python scripts/run_storm_wiki_with_vector_rm.py --csv-file-path corpus.csv --vector-db-mode offline --offline-vector-db-dir ./vector_store --collection-name my_documents --device cpu --validate-only
python scripts/run_storm_wiki_with_vector_rm.py --csv-file-path corpus.csv --vector-db-mode offline --offline-vector-db-dir ./vector_store --collection-name my_documents --device cpu --dry-run --topic "Test topic"
```

These commands should not perform embedding, Qdrant access, LLM calls, or network access in `--validate-only`/`--dry-run` mode.
