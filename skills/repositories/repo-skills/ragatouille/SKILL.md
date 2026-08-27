---
name: ragatouille
description: "Use RAGatouille to train, index, search, rerank, integrate, and
  export ColBERT-style late-interaction retrieval models in RAG pipelines."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# RAGatouille Repo Skill

Use this skill when a task mentions RAGatouille, `RAGPretrainedModel`, `RAGTrainer`, ColBERT indexing/search, RAG reranking, RAGatouille LangChain adapters, or exporting RAGatouille-trained ColBERT checkpoints.

RAGatouille 0.0.9post2 focuses on making ColBERT-style late-interaction retrieval usable from Python. It has four main surfaces:

- persisted pretrained model indexing/search through `RAGPretrainedModel`;
- training-data preparation and fine-tuning through `RAGTrainer`;
- index-free reranking and in-memory encoded search;
- framework adapters and export helpers.

## Start Here

1. Run a lightweight import check before model downloads or training:
   ```bash
   python scripts/check_ragatouille_environment.py --json
   ```
2. If `import ragatouille` fails, read `references/troubleshooting.md` before changing code; RAGatouille 0.0.9post2 has known loose dependency pins.
3. Pick the sub-skill by task shape, not by source file name.
4. Avoid running notebook examples, model downloads, Hugging Face uploads, or training loops unless the user explicitly approves network, credentials, compute, and write locations.

## Route by Task

- **Build, load, query, or update persisted indexes**: read `sub-skills/pretrained-indexing-search/SKILL.md` for `RAGPretrainedModel.from_pretrained`, `from_index`, `index`, `search`, `add_to_index`, `delete_from_index`, document IDs, metadata, result schemas, and input validation.
- **Prepare training data or fine-tune/train ColBERT**: read `sub-skills/training-data-finetuning/SKILL.md` for raw pair/labeled pair/triplet formats, `TrainingDataProcessor`, `CorpusProcessor`, hard negative mining, exported training files, and `RAGTrainer.train`.
- **Rerank candidate documents or search temporary in-memory docs**: read `sub-skills/index-free-reranking/SKILL.md` for `rerank`, `encode`, `search_encoded_docs`, `clear_encoded_docs`, metadata propagation, and result-shape checks.
- **Use framework integrations or export models**: read `sub-skills/integrations-export/SKILL.md` for LangChain retriever/compressor adapters, LlamaIndex/LlamaHub-style loader patterns, Hugging Face Hub upload planning, and Vespa ONNX export.

## Common Decisions

- Use a persisted index when documents must survive process restarts, collections are reused, `document_id`/metadata filtering matters, or query latency must be optimized.
- Use index-free reranking when another retriever already produced a small candidate set or the collection is temporary for one process.
- Use `TrainingDataProcessor` or the bundled training validator for safe data checks before initializing `RAGTrainer`, because trainer construction can load model dependencies.
- Use the integration checker before debugging LangChain or export wiring; it catches legacy import path and optional dependency problems without uploads or downloads.

## Install and Import Notes

Typical user install:

```bash
pip install ragatouille
python -c "import ragatouille; print(ragatouille.__version__)"
```

For this repo version, be prepared to pin a legacy-compatible LangChain line if top-level import fails on `langchain.retrievers.document_compressors.base`. A known-good inspection combination used `langchain==0.1.20` and `langchain-core==0.1.53`; current environments may need equivalent versions that still expose the legacy retriever/compressor path.

If import then fails through `fast_pytorch_kmeans` on `psutil`, install `psutil` in the active environment. See `references/troubleshooting.md` for the full decision tree.

## Bundled Root References and Scripts

- `references/evidence-summary.md`: source files, docs, examples, tests, and installed-package facts distilled into this skill.
- `references/repo-provenance.md`: public source snapshot and evidence paths for future staleness checks.
- `references/repo-routing-metadata.json`: structured scenario metadata used by DisCo's repo-skills router.
- `references/troubleshooting.md`: cross-cutting installation, import, backend, network, and workflow safety guidance.
- `scripts/check_ragatouille_environment.py`: safe import/signature/backend checker that does not load models, download checkpoints, train, or upload artifacts.

## Safety Boundaries

- Do not make runtime skill instructions depend on the original repository checkout, notebooks, or tests.
- Do not assume notebook examples are safe: several require model downloads, external loaders, OpenAI/Hugging Face credentials, or GPU-scale training.
- Do not run `export_to_huggingface_hub` during validation unless the user authorizes upload side effects and credentials are configured.
- Do not treat CPU import verification as proof that long training or GPU indexing is available; validate backend and hardware separately for those tasks.
- Keep standalone RAGatouille scripts under `if __name__ == "__main__":` as recommended by the upstream README.
