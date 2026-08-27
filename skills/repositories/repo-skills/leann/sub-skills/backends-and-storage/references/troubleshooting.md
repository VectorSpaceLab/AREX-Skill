# Backend and storage troubleshooting

Start with the read-only checker. It distinguishes metadata/passage-offset
failures from backend artifact failures without importing optional native code:

```text
python scripts/inspect_leann_index.py path/to/name.leann --strict
```

Then run the smallest backend-native smoke test that matches the failure. Do
not repair an index by deleting individual files or editing ID maps by hand.

| Symptom | Likely cause | Safe diagnosis | Corrective action |
|---|---|---|---|
| Backend name not discovered | Distribution absent, wrong Python environment, or optional import raised `ImportError` | Compare installed `leann-backend-*` distribution with the exact registry name; run deterministic autodiscovery and inspect import logs | Install the matching distribution in the runtime environment, install its required native dependency, then rediscover; do not rename a package or silently fall back |
| HNSW/FAISS import has ABI or symbol errors | Source wheel/native library mismatch, stale build, architecture/SIMD mismatch | Import HNSW and FAISS alone; capture Python, platform, package versions, and native loader error | Rebuild/reinstall one coherent HNSW/FAISS stack; on source builds verify CMake/compiler/OpenMP/BLAS/LAPACK and initialized submodules |
| HNSW build fails around ZeroMQ, BLAS, or submodules | `libzmq` not found by pkg-config, missing cppzmq/msgpack-c/FAISS sources, or BLAS/LAPACK not discoverable | Read CMake's first missing target/library; check `pkg-config --modversion libzmq` and the source submodules without modifying them | Initialize the required submodules and expose explicit CMake/library prefixes; install ZeroMQ and BLAS/LAPACK; rerun a clean package build |
| FAISS says dimension mismatch or search returns invalid labels | Metadata dimension differs from embeddings/index, or an ID map is stale | Inspect metadata `dimensions`; compare the source embedding width and `.ids.txt`/backend map counts | Rebuild with one embedding model/dimension/metric; never pad or truncate vectors to make an old index load |
| FAISS says unsupported metric | Metric is not one of the backend's supported names or metadata has a typo | Read `backend_kwargs.distance_metric` and compare with the backend tuning table | Rebuild or update metadata through the owning builder using `mips`, `cosine`, or `l2`; normalize vectors for cosine policy |
| IVF training fails or search is invalid | `nlist` is too large for the training population, index was never trained, or `.index` and `ivf_id_map.json` diverged | Check `nlist`, row count, index presence, ID-map JSON structure, and inspector output | Rebuild with a smaller viable `nlist`; preserve `DirectMap.Hashtable`; for updates remove old IDs then add matching new rows |
| IVF update reports duplicate ID or short removal | Passage IDs were reused incorrectly, update was run twice, or offset/ID maps disagree | Compare live offset IDs with `ivf_id_map.json`; inspect update log's requested/found/removed counts | Reconcile by a supported full rebuild when maps disagree; do not reuse old integer FAISS IDs or hand-edit the JSON map |
| DiskANN native dependency/build fails | `diskannpy`/compiled extension or its CMake dependencies are unavailable; native process exited | Import `diskannpy` alone and preserve the child-process exit/status message; inspect required submodule and compiler libraries | Install/build the optional DiskANN package for the target platform, use explicit memory limits, and rerun an isolated build; HNSW/IVF are CPU alternatives |
| DiskANN partition search cannot load | Only one of graph/map exists, medoid/norm/PQ files were not copied, or cleanup removed a required file | Check the complete standard vs partition artifact set with the inspector | Restore the complete artifact directory from the same build or rebuild with recomputation; never mix prefixes from different indexes |
| FlashLib says no CUDA, wheel, or device is available | `torch`/FlashLib wheel does not match the driver, CUDA runtime, architecture, or active device | Probe `torch.cuda.is_available()` and import FlashLib in the search environment; test the same environment that discovered the registry entry | Install a compatible torch/FlashLib/driver combination or choose CPU HNSW/IVF; do not claim CPU support for FlashLib search |
| FlashLib exact index is missing vectors/ID map | Full-vector `.flashlib.npy` or ordered ID JSON was not copied | Inspect the two files and validate the NPY header/row count | Restore both files from one build or rebuild; FlashLib does not reconstruct missing vectors from HNSW artifacts |
| MPS/Apple Silicon path fails | MPS/MLX is an embedding runtime option, not proof of a native backend accelerator; an extension may be CPU-only or ABI-incompatible | Separate the embedding-mode probe from the backend import/search probe | Use the supported CPU backend or a verified platform-specific build; label MLX/MPS as optional and do not route to CUDA FlashLib |
| Recompute requires a port or ZMQ request times out | Search flag/index pruning state needs fresh vectors, server failed to start, port is occupied, or metadata/source changed | Confirm effective recompute, embedding model/mode, passage source paths, server module import, and the actual selected port; enable diagnostic logging | Start/reuse the backend server through the public searcher, pass the actual `zmq_port` for direct backend calls, and fix ZeroMQ/model/provider setup; for no-recompute rebuild HNSW non-compact with full vectors |
| Search returns a label but text enrichment fails | Passage `.idx` lacks the label, offset points to a different JSONL record, or stale JSONL survived an update | Run the inspector; compare offset-map IDs and record IDs per source | Rebuild or use the supported IVF compaction/update path; do not patch offsets by hand |
| Inspector reports incomplete/corrupt artifacts | Metadata JSON, source JSONL, offset pickle, backend file, or backend ID map is missing/invalid | Read the structured `--json` report and fix the first error; optional native files may be unparseable without their dependency | Restore the complete same-build artifact family or rebuild; the inspector intentionally cannot prove native headers or CUDA tensor contents |

## What not to infer

- A discovery entry is not a successful search.
- A file-level pass is not a dimension/metric header pass for native indexes.
- A benchmark README result is not a deployment guarantee; benchmark scripts are
  excluded from this operating skill because they require datasets, downloads,
  hardware, or unbounded runtime.
- A server fallback to direct query embedding does not prove that HNSW/DiskANN
  neighbor recomputation succeeded.
