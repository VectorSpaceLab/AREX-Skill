# SPLADE Cross-Cutting Troubleshooting

Use this reference before deciding that a SPLADE command, import, or workflow is broken. Workflow-specific troubleshooting lives in each sub-skill's `references/troubleshooting.md`.

## Install and Import

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'splade'` | SPLADE is not installed in the active Python or the package root is not on `PYTHONPATH` | Install the package in the intended environment or run commands from a context where `python -c "import splade"` succeeds. |
| `TypeError: main() got an unexpected keyword argument 'version_base'` | Current source uses Hydra `version_base` while the environment has older `hydra-core` | Use a Hydra/OmegaConf pair compatible with current source, or pin the source/environment to a historical matching state. |
| `pip check` reports `SPLADE 2.1 requires omegaconf==2.1.2` after upgrading Hydra | Metadata pins an older OmegaConf, but current source needs newer Hydra behavior for some modules | Treat this as source/metadata drift; document the chosen environment and prefer command help/import checks over trusting metadata alone. |
| `ModuleNotFoundError: pytrec_eval` | Retrieval/evaluation/reranking imports metric helpers | Install `pytrec-eval` where build/network access is available, or avoid metric-executing paths until the dependency is present. |
| `pytrec-eval` install tries to fetch `trec_eval` and fails | The package builds against external NIST `trec_eval` sources | Retry with network access, a cached source, or an environment that already provides metric tooling; do not treat this as a SPLADE API bug. |

## Data and Download Requirements

- Training configs often assume MS MARCO, distillation, hard-negative, or model-weight downloads that are not bundled with this skill.
- BEIR evaluation downloads datasets unless a dataset cache/path is already prepared.
- Hugging Face model names such as `naver/splade-cocondenser-ensembledistil` require network or a local HF cache.
- If a user requests a no-network plan, use command builders, schema validators, API inspection, or tiny fixtures instead of launching downloads.

## Hardware Expectations

- CPU is enough for import checks, Hydra help, command construction, schema validation, and small API inspection.
- Training, full indexing, large retrieval, and reranking can be GPU-heavy; batch-size and FLOPS regularization settings may need adjustment on smaller GPUs.
- PISA, Anserini, Pyserini, Java, and external metric engines are separate runtime prerequisites from SPLADE itself.

## Routing Recovery

- If the failure occurs before command execution or while composing Hydra configs, use `sub-skills/hydra-pipelines/SKILL.md`.
- If the failure involves HF Trainer dataclasses, hard-negative files, reranker models, or `torchrun`, use `sub-skills/hf-training-reranking/SKILL.md`.
- If the failure is a schema/API/id mismatch, use `sub-skills/model-data-api/SKILL.md`.
- If the failure mentions Anserini JSONL, BEIR, PISA, Pyserini, Java, or pruning scripts, use `sub-skills/pruning-export-evaluation/SKILL.md`.
