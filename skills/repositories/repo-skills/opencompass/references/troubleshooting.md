# Cross-Cutting Troubleshooting

## Import or CLI Fails

Symptoms:

- `import opencompass` fails.
- `opencompass --help` is not found.
- Distribution metadata is missing.

Fixes:

- Install the base package with `pip install -U opencompass` or `pip install -e .` in a development checkout.
- Run `python scripts/opencompass_environment_check.py` from this skill to separate package import, metadata, CLI, and optional-module failures.
- If only optional modules are missing, route to the relevant sub-skill instead of installing every extra.

## Config Loads but Run Fails

Route by symptom:

- Missing `models`, `datasets`, `summarizer`, `read_base()`, `reader_cfg`, or local data files: `sub-skills/configuration-and-datasets/SKILL.md`.
- Model constructor, tokenization, API credentials, vLLM/LMDeploy, GPU memory, or Torch/Transformers compatibility: `sub-skills/model-backends/SKILL.md`.
- Literal prompt fields, answer leakage, `PromptList`, retriever, or `GenInferencer`/`PPLInferencer`: `sub-skills/prompt-and-inference/SKILL.md`.
- Runner/partitioner, `--mode`, `--reuse`, `--work-dir`, Slurm, DLC, or dry-run/debug behavior: `sub-skills/evaluation-workflows/SKILL.md`.
- Missing summary cells, judge outputs, result station, or repeat analysis: `sub-skills/results-and-analysis/SKILL.md`.

## Network and Data Problems

- First runs may download datasets or model weights. Use `--dry-run` for planning and small subsets for smoke tests.
- Offline usage needs local dataset paths, local model weights, or configured dataset mirrors such as ModelScope where supported.
- `DATASET_SOURCE=ModelScope` changes dataset source behavior for supported mappings; verify the dataset appears in OpenCompass dataset mappings before relying on it.

## Credentials and Secrets

- Keep API keys, judge keys, provider tokens, cloud credentials, and private endpoints in environment variables or secret stores.
- Do not commit secrets into OpenCompass configs, generated examples, result summaries, or copied fixtures.
- For LLM judge configs, prefer environment variables when supported: `OC_JUDGE_MODEL`, `OC_JUDGE_API_KEY`, and `OC_JUDGE_API_BASE`.

## Runtime Compatibility

- A CLI help check proves only that the entry point imports enough to display help.
- A config dry-run proves only task/config planning, not actual model inference.
- Real model execution requires compatible model dependencies, backend packages, hardware, driver, memory, credentials, and data access.
- If `transformers` disables PyTorch or reports version incompatibility, fix the target runtime before claiming HuggingFace inference is verified.
