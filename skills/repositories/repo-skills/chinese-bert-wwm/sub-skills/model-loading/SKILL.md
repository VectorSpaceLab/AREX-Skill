---
name: model-loading
description: "Load HFL Chinese BERT-wwm family models with Transformers or
  PaddleHub while avoiding RoBERTa-class and offline-cache mistakes."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# model-loading

Use this sub-skill when a task is about loading or validating HFL Chinese BERT-wwm family model identifiers, choosing the correct `MODEL_NAME` or PaddleHub `MODULE_NAME`, checking whether a model is available in an offline Hugging Face cache, or fixing errors caused by using RoBERTa classes for RoBERTa-wwm-named checkpoints.

## Route here for

- `hfl/chinese-bert-wwm`, `hfl/chinese-bert-wwm-ext`, `hfl/chinese-roberta-wwm-ext`, `hfl/chinese-roberta-wwm-ext-large`, `hfl/rbt3`, `hfl/rbt4`, `hfl/rbt6`, or `hfl/rbtl3` loading.
- Deciding between `BertTokenizer`/`BertModel` and `AutoTokenizer`/`AutoModel` for these identifiers.
- Explaining why `RobertaTokenizer` or `RobertaModel` is wrong for these models despite names containing `RoBERTa`.
- Distinguishing TensorFlow checkpoint zips from Hugging Face/PyTorch files.
- PaddleHub module-name lookup and optional Paddle/PaddleHub dependency caveats.
- Offline-safe model-id validation or cache checks with the bundled helper.

## Route elsewhere

- Fine-tuning hyperparameters, task/model selection, WWM interpretation, and benchmark-driven model choice: `../task-selection-and-finetuning/SKILL.md`.
- Dataset schemas, dataset availability, and benchmark table interpretation: `../data-and-benchmarks/SKILL.md`.
- Cross-cutting environment, cache, proxy, and framework issues that are not specific to these loading workflows: `../../references/troubleshooting.md`.

## Operating pattern

1. Identify whether the user is using Hugging Face Transformers, PaddleHub, or a downloaded checkpoint zip.
2. Normalize the requested model to a supported HFL id or PaddleHub module name using `references/loading-workflows.md`.
3. For Transformers, prefer `BertTokenizer` plus `BertModel`, or `AutoTokenizer` plus `AutoModel`. Do not use `RobertaTokenizer` or `RobertaModel` for this repository's Chinese RoBERTa-wwm family.
4. Decide the loading mode before calling `from_pretrained`:
   - offline/cache validation: use `local_files_only=True` or the bundled checker's default offline mode;
   - online download: make the network action explicit and ensure the user expects checkpoint downloads;
   - local checkpoint directory: verify the directory contains files matching the framework path being used.
5. If the goal is only to validate a model id or check local cache state, run `scripts/check_transformers_model.py` instead of writing ad hoc loading code.

## Bundled helper

Run the checker from this sub-skill directory or provide its path explicitly:

```bash
python scripts/check_transformers_model.py --help
python scripts/check_transformers_model.py hfl/rbt3 --try-load-tokenizer --offline-only
python scripts/check_transformers_model.py --model-id hfl/chinese-roberta-wwm-ext --try-load-config --allow-download
```

The helper validates the bundled model-id map and imports the expected Transformers classes. It does not download by default. It exits nonzero for unknown ids, missing imports/backends, or any requested config/tokenizer/model load that fails.

## References

- `references/loading-workflows.md`: model-id and PaddleHub mappings, offline/online/cache workflows, and checkpoint-format notes.
- `references/api-reference.md`: verified public APIs and signatures for the minimum Transformers workflow.
- `references/troubleshooting.md`: workflow-specific failure diagnosis and fixes.
