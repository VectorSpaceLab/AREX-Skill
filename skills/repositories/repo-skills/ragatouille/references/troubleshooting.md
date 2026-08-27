# RAGatouille Troubleshooting

This reference covers cross-cutting problems that can block every RAGatouille workflow. For workflow-specific errors, use the nearest sub-skill troubleshooting reference.

## Top-Level Import Fails on LangChain

Symptom:

```text
ModuleNotFoundError: No module named 'langchain.retrievers'
```

Likely cause: RAGatouille 0.0.9post2 imports `langchain.retrievers.document_compressors.base.BaseDocumentCompressor`, but recent LangChain 1.x packages no longer expose that legacy path.

Recovery:

1. Verify the failure without downloading models:
   ```bash
   python scripts/check_ragatouille_environment.py --json
   ```
2. Pin to a legacy-compatible LangChain line for this RAGatouille version. One verified combination is:
   ```bash
   python -m pip install "langchain==0.1.20" "langchain-core==0.1.53"
   ```
3. Re-run `python -m pip check` and the root checker.
4. If a newer application requires LangChain 1.x, isolate RAGatouille in a separate environment or verify whether a newer RAGatouille/PyLate backend release supports the new import paths.

## Import Fails on `psutil` Through `fast_pytorch_kmeans`

Symptom:

```text
ModuleNotFoundError: No module named 'psutil'
```

Likely cause: importing RAGatouille reaches `ragatouille.models.torch_kmeans`, which imports `fast_pytorch_kmeans`; that package can require `psutil` even when dependency metadata does not force it.

Recovery:

```bash
python -m pip install psutil
python -m pip check
python scripts/check_ragatouille_environment.py --json
```

## Future Backend Warning Appears on Import

RAGatouille 0.0.9post2 emits a warning that version 0.0.10 will migrate from the Stanford ColBERT backend to PyLate.

Use this as a routing signal:

- Pin `<0.0.10` when a task explicitly depends on the Stanford ColBERT backend behavior documented by this skill.
- Refresh this skill before relying on it for a later PyLate-based RAGatouille release.

## Model Downloads or Hub Access Fail

`RAGPretrainedModel.from_pretrained(...)`, `RAGTrainer(...)`, hard-negative mining, LlamaIndex/LlamaHub loaders, and Hugging Face export paths can trigger network calls.

Before retrying:

- Confirm the model id or local checkpoint path.
- Confirm whether network access is allowed.
- Check authentication for private Hugging Face models or uploads.
- Prefer local checkpoint/index paths when the task is offline.
- Do not hide download failures by replacing them with unverified mock results.

## Torch, FAISS, and Backend Confusion

RAGatouille depends on Torch, ColBERT, FAISS CPU by default, and optional GPU paths.

Guidance:

- CPU importability is enough for API inspection and offline validators.
- Actual indexing can be slow on CPU; the PLAID implementation may use a PyTorch k-means fallback unless `use_faiss=True` is passed.
- If GPU is available but only `faiss-cpu` is installed, indexing may print a warning and continue on CPU.
- Training is commonly GPU/compute intensive; run tiny smoke tests only when hardware and model downloads are explicitly allowed.

## Windows and WSL

The upstream README states that Windows is not supported, RAGatouille does not appear to work outside WSL, and WSL1 has issues. Prefer Linux or WSL2 for real indexing/training workflows.

## Script Entry Point Requirement

The upstream README warns that scripts using RAGatouille should be run inside:

```python
if __name__ == "__main__":
    ...
```

Use that guard for standalone scripts that initialize models, index, train, or run multiprocessing-adjacent code.

## Native Examples and Tests Are Not Lightweight Checks

Many repo notebooks and tests require one or more of:

- model downloads such as `colbert-ir/colbertv2.0`;
- network-backed external loaders;
- OpenAI or Hugging Face credentials;
- GPU or long training/indexing work;
- writes to index or training-data directories.

For lightweight validation, use bundled skill scripts first. Escalate to native tests only after the generated skill is integrated and the user approves the required network/compute/write side effects.

## Choosing a Sub-Skill for Workflow Failures

- Index creation, search, ID/metadata validation, index roots, `doc_ids`, or CRUD: `../sub-skills/pretrained-indexing-search/references/troubleshooting.md`.
- Raw training-data shape, hard negatives, generated training files, or GPU training: `../sub-skills/training-data-finetuning/references/troubleshooting.md`.
- `rerank`, `encode`, stale in-memory docs, result shapes, or transient collection limits: `../sub-skills/index-free-reranking/references/troubleshooting.md`.
- LangChain/LlamaIndex adapters, Hugging Face auth, upload permissions, Vespa ONNX, or optional integration imports: `../sub-skills/integrations-export/references/troubleshooting.md`.
