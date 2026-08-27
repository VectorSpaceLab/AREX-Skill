# ColBERT Cross-Cutting Troubleshooting

Use this reference for package-wide install, import, optional dependency, backend, and runtime setup failures. Workflow-specific failures live in the nearest sub-skill troubleshooting file.

## Install and Import Failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'colbert'` | The distribution is not installed in the active Python environment. | Install `colbert-ai` in the environment that runs the task, then run `python scripts/check_colbert_env.py`. |
| `ModuleNotFoundError: No module named 'torch'` | Installed `colbert-ai` without the `torch` extra or in an environment missing PyTorch. | Install a compatible PyTorch build or use `pip install "colbert-ai[torch,faiss-cpu]"` for CPU inspection. |
| `No module named 'faiss'` or FAISS import errors | Missing or mismatched FAISS backend. | Use `faiss-cpu` for CPU search/inspection or a CUDA-compatible FAISS GPU package for GPU workflows. Verify with the root check script. |
| `No module named 'pkg_resources'` from `torch.utils.cpp_extension` | Older Torch/ColBERT stacks may rely on `pkg_resources`, while newer `setuptools` versions removed it. | Pin or install a compatible setuptools release, for example `python -m pip install 'setuptools<81'`, then rerun import checks. |
| `transformers` or tokenizer download failures | Hugging Face access/cache is unavailable or model name is remote. | Prefer local checkpoint paths for deterministic work, or explicitly allow network/cache access before model loading. |

## Backend and Resource Failures

- CPU import checks do not prove full indexing, training, passage update, or Baleen execution will work. Those workflows may require CUDA-capable PyTorch, FAISS GPU, enough VRAM, local checkpoints, and local datasets.
- If `torch.cuda.is_available()` is false on a GPU machine, verify container GPU passthrough, driver compatibility, and whether the installed Torch wheel is CPU-only.
- Use CPU/FAISS CPU for static validation, data checks, and many search-inspection tasks; do not promise production-speed indexing or training on CPU.
- For memory-mapped index loading, remember ColBERT search raises an error when `load_index_with_mmap=True` and GPU search is active.

## Path and Artifact Confusion

- ColBERT combines `RunConfig(root=..., experiment=...)`, `ColBERTConfig(index_root=...)`, and index names to resolve index and output paths. Make the root/experiment/index choices explicit in scripts.
- `Ranking.save(...)` can write relative to the active run context. Prefer absolute output paths or print the resolved path.
- Generated indexes contain multiple metadata, doclens, codes, residuals, and IVF files. Back up or copy the index before mutable update/coalescing workflows.

## Data and API Misuse

- Validate `collection.tsv`, `queries.tsv`, qrels, rankings, and training examples with bundled scripts before expensive GPU work.
- Keep task ownership clear: data/evaluation validates and scores files; modeling/tokenization checks checkpoint/config/text encoding behavior; training creates checkpoints; indexing/search builds and queries indexes; index-updates/serving mutates and serves existing indexes.
- When a helper script succeeds, treat it as validation of file shape or import surface, not as proof that remote checkpoints, full datasets, or GPU-heavy workflows are available.
