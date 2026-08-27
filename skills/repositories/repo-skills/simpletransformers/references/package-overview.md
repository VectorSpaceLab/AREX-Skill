# Simple Transformers Package Overview

## Purpose

Simple Transformers is a high-level wrapper around Hugging Face Transformers for quickly training, evaluating, and predicting with task-specific NLP models.

## Task-to-class map

| Task family | Public class | Owning sub-skill |
|---|---|---|
| binary/multiclass/regression/sentence-pair classification | `ClassificationModel` | [classification](../sub-skills/classification/SKILL.md) |
| multilabel classification | `MultiLabelClassificationModel` | [classification](../sub-skills/classification/SKILL.md) |
| text+image multimodal classification | `MultiModalClassificationModel` | [classification](../sub-skills/classification/SKILL.md) |
| named entity recognition/token classification | `NERModel` | [token-and-qa](../sub-skills/token-and-qa/SKILL.md) |
| extractive question answering | `QuestionAnsweringModel` | [token-and-qa](../sub-skills/token-and-qa/SKILL.md) |
| language model fine-tuning/from-scratch training | `LanguageModelingModel` | [generative-workflows](../sub-skills/generative-workflows/SKILL.md) |
| language generation | `LanguageGenerationModel` | [generative-workflows](../sub-skills/generative-workflows/SKILL.md) |
| T5 text-to-text | `T5Model` | [generative-workflows](../sub-skills/generative-workflows/SKILL.md) |
| generic Seq2Seq | `Seq2SeqModel` | [generative-workflows](../sub-skills/generative-workflows/SKILL.md) |
| conversational AI | `ConvAIModel` | [generative-workflows](../sub-skills/generative-workflows/SKILL.md) |
| sentence/word representations | `RepresentationModel` | [retrieval-representation](../sub-skills/retrieval-representation/SKILL.md) |
| dense retrieval | `RetrievalModel` | [retrieval-representation](../sub-skills/retrieval-representation/SKILL.md) |

## Installation baseline

The package metadata declares Python `>=3.6`, package version `0.70.8`, and runtime dependencies including `transformers`, `datasets`, `scipy`, `scikit-learn`, `seqeval`, `tensorboard`, `pandas`, `wandb`, `streamlit`, and `sentencepiece`. The source imports PyTorch in model modules, so install a compatible `torch` build even though setup metadata does not list it directly.

Use CPU first unless the user explicitly asks for GPU:

```bash
pip install torch  # choose CPU/CUDA wheel according to the user's platform
pip install simpletransformers
python -c "import simpletransformers; print(simpletransformers.name)"
```

For local development from a checkout, use editable installation in an isolated environment after installing PyTorch.

## Compatibility warning

Simple Transformers 0.70.8 has no upper bound on Transformers. Runtime inspection found that latest Transformers and some 4.x versions can break imports for removed aliases such as `SequenceSummary` variants, `TransfoXLConfig`, or top-level `cached_path`. If imports fail, read [troubleshooting](troubleshooting.md) before changing user data.

## Backend policy

- CPU is sufficient for schema validation, API inspection, and small smoke workflows with cached/tiny models.
- CUDA is optional acceleration for training/evaluation/prediction. Do not claim GPU support until the target environment has a CUDA-capable PyTorch build and a successful tiny tensor allocation.
- Retrieval extras (`faiss`, `pytrec_eval`, `beir`) are optional and should be installed only for workflows that need them.

## Output and side effects

Most training APIs write `outputs/`, `cache_dir/`, `runs/`, and sometimes WandB artifacts unless args disable them. For smoke runs, set `no_save=True`, `overwrite_output_dir=True`, `reprocess_input_data=True`, and use a temporary output directory. For production runs, choose explicit persistent output/cache directories.
