# Application Troubleshooting

## Dependency conflicts

- ColossalQA can require an older torch/langchain stack than the core ColossalAI package. Use a separate environment.
- ColossalEval can require vLLM or evaluation packages that are not needed for core training.
- ColossalChat and Colossal-LLaMA can require flash-attn, Apex, datasets, PEFT, and large-model tooling. Install only after selecting that app workflow.

## Model/data assets

- Missing model path: ask for a local checkpoint or explicit download approval.
- Dataset format mismatch: read the app-specific data preparation reference and validate a tiny sample before full training/evaluation.
- Tokenizer/model mismatch: use tokenizer and model from the same family/checkpoint.
- Output directory permissions: create explicit writable output/checkpoint paths.

## Credentials and services

- OpenAI/Pangu/vLLM/API paths require endpoints and secrets. Do not hard-code tokens; use environment variables or secret managers.
- Web UI or API demos start services and may bind ports. Ask before starting long-running listeners.
- Locust or benchmark clients generate traffic; use only for approved performance tests.

## GPU and memory

- RLHF/PPO and large LLaMA pretraining are multi-GPU, memory-heavy workflows.
- Use smaller dummy datasets and tiny configs for smoke checks.
- Route memory-sharding decisions to core Booster/Gemini/parallelism sub-skills.
