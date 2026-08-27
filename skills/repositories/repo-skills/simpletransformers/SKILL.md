---
name: simpletransformers
description: "Use Simple Transformers package workflows for NLP classification,
  NER, QA, generation, T5, Seq2Seq, retrieval, representations, data validation,
  and troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Simple Transformers Repo Skill

Use this skill when the user asks about the `simpletransformers` Python package,
Simple Transformers task wrappers, task-specific training/evaluation/prediction
data formats, `ClassificationModel`, `NERModel`, `QuestionAnsweringModel`,
`LanguageModelingModel`, `LanguageGenerationModel`, `T5Model`, `Seq2SeqModel`,
`RepresentationModel`, `RetrievalModel`, `ConvAIModel`, or package-specific
import/runtime errors.

## Install and import baseline

Simple Transformers wraps Hugging Face Transformers and uses PyTorch in model
modules. Install a compatible PyTorch build before importing task model classes:

```bash
pip install torch        # choose CPU or CUDA wheel for the target machine
pip install simpletransformers
python -c "import simpletransformers; print(simpletransformers.name)"
```

For smoke runs, pass `use_cuda=False` to model constructors unless the user has
already verified a CUDA-capable PyTorch environment.

## Route by task

| User task | Read |
|---|---|
| binary/multiclass/regression/sentence-pair/multilabel/LayoutLM/multimodal classification, cross-encoder reranking | [classification](sub-skills/classification/SKILL.md) |
| named entity recognition, token classification, CoNLL, LayoutLM token boxes, extractive QA, SQuAD JSON/JSONL | [token-and-qa](sub-skills/token-and-qa/SKILL.md) |
| language model training/fine-tuning, generation, T5, Seq2Seq, ConvAI, text-to-text tasks | [generative-workflows](sub-skills/generative-workflows/SKILL.md) |
| sentence/word representations, dense retrieval, DPR, hard negatives, BEIR/MSMARCO/TREC, FAISS/pytrec | [retrieval-representation](sub-skills/retrieval-representation/SKILL.md) |

## Shared references

- [Package overview](references/package-overview.md) maps public tasks to model classes and notes install/backend constraints.
- [Configuration](references/configuration.md) explains shared `ModelArgs`/task args and safe smoke-run defaults.
- [CLI and viewer](references/cli-and-viewer.md) explains the `simple-viewer` Streamlit launcher and why not to run it in automated checks.
- [Troubleshooting](references/troubleshooting.md) covers import/version, PyTorch, CUDA, downloads, outputs/cache, multiprocessing, and optional dependencies.
- [Repository provenance](references/repo-provenance.md) records the source snapshot and refresh baseline.

## Bundled helper scripts

- `scripts/check_simpletransformers_env.py`: run to check package versions, task-module imports, and optional CUDA visibility.
- `scripts/inspect_model_args.py`: run in an environment where Simple Transformers imports cleanly to list args dataclass fields.
- Sub-skill validators under `sub-skills/*/scripts/`: use these before model construction to catch data/schema mistakes without downloads or training.

## Compatibility warning

Simple Transformers 0.70.8 declares `transformers>=4.31.0` but package
inspection found runtime hazards with modern Transformers versions: removed
`SequenceSummary` aliases, `TransfoXLConfig`, and top-level `cached_path` can
break imports before any dataset is read. When import errors mention these
symbols, debug dependency compatibility first and use the troubleshooting
references; do not rewrite user data prematurely.

## Safe operating defaults

1. Validate data with the nearest bundled validator.
2. Use CPU (`use_cuda=False`) and no-save settings for smoke/debug runs.
3. Avoid full examples/tests unless model downloads, data downloads, training time, and compute budget are approved.
4. Choose explicit `output_dir`, `cache_dir`, and checkpoint policy before production runs.
5. Install optional dependencies such as ONNX, FAISS, BEIR, pytrec, Streamlit server usage, or WandB only for workflows that need them.
6. If the current repository/package has changed from [provenance](references/repo-provenance.md), refresh this skill before relying on exact API/version claims.

## Non-goals

- Raw Hugging Face Transformers Trainer/model/tokenizer guidance when the user is not using Simple Transformers.
- Generic vector database or RAG framework workflows outside Simple Transformers retrieval APIs.
- Long-running training, benchmark execution, dataset downloads, or Streamlit server launches as default verification steps.
