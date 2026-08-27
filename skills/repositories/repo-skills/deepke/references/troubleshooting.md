# DeepKE cross-cutting troubleshooting

Use this reference before changing code, rerunning expensive jobs, or treating a workflow failure as a model-quality problem.

## Start with the smallest safe check

| Area | Safe check |
| --- | --- |
| Whole installation | `python scripts/check_deepke_core.py --json` |
| Supervised NER/RE/AE/EE | `python sub-skills/supervised-extraction/scripts/check_supervised_env.py --task <task> --json` |
| Triple extraction | `python sub-skills/triple-extraction/scripts/check_triple_env.py --task <task> --json` |
| DeepKE-LLM | `python sub-skills/llm-workflows/scripts/check_llm_workflow_env.py --workflow <workflow> --json` |
| MCP wrapper | `python sub-skills/mcp-tools/scripts/check_mcp_env.py --json` |

These scripts are diagnostics only. They do not train, download, call APIs, launch servers, or mutate configs.

## Dependency families and conflicts

DeepKE examples were built across multiple dependency eras. If one environment fails after adding unrelated requirements, isolate the workflow instead of forcing all examples into one stack.

- Classic supervised workflows: PyTorch, Transformers, Hydra, task dependencies, sometimes TensorBoard/TorchCRF.
- PURE: AllenNLP and older Transformers/PyTorch/Hugging Face Hub compatibility are common pain points.
- ASP: CUDA-enabled PyTorch plus Apex is a real backend requirement.
- MT5: DeepSpeed/Transformers/generation settings and GPU count matter.
- DeepKE-LLM: PEFT/OpenDelta/Accelerate/DeepSpeed/API clients vary by model family.
- MCP: FastMCP import path and environment-variable handling must match the local MCP package version.

## Data shape mistakes

| Symptom | First checks |
| --- | --- |
| `Extra data` while reading JSON | The file is probably JSONL; parse one line at a time. |
| Empty NER labels or offset errors | Slice the raw text using each offset and verify it equals the entity surface. |
| Relation training fails immediately | Check CSV headers, one candidate pair per row, `relation.csv`/`rel2id.json`, and head/tail offsets. |
| Event pipeline cannot find role/trigger output | Verify trigger-stage prediction paths before running role prediction. |
| MT5/LLM parsed triples are empty | Inspect raw generated text for parentheses, delimiters, schema labels, and prompt drift. |
| Instruction data looks valid but model ignores schema | Split large schemas, add examples, and validate task/language prompt choice. |

## Backend and resource mistakes

- Do not treat CPU import success as proof that CUDA/Apex/DeepSpeed/large-model workflows can run.
- If the user requested a real GPU workflow and CUDA is unavailable, report a backend block or ask the user to narrow scope.
- If model/checkpoint paths are absent, do not trigger downloads unless the user approved network use and storage/time cost.
- For API workflows, require credentials, endpoint/model name, and budget approval before making calls.
- For MCP workflows, warn that the source server shells out and can mutate local DeepKE example configs/data.

## Config and path mistakes

- Many native DeepKE examples depend on working directory and Hydra-relative paths. Record the resolved working directory and config overrides before running.
- Keep output directories unique; several training scripts can overwrite logs/checkpoints/predictions.
- Avoid publishing private local paths in shared docs, prompts, or exported skill files.
- Prefer local model/checkpoint paths in runtime configs when offline or reproducibility matters.

## When to ask before proceeding

Ask the user for a concrete decision when:

- A requested action would start training, inference on a large checkpoint, DeepSpeed, Apex build, or API calls.
- Required backend hardware or credentials are missing.
- Dependency repair would mutate an existing environment in a way that could break it.
- The source data schema is ambiguous enough that an automatic converter could corrupt labels.
- MCP deployment would expose shelling-out tools to untrusted input or concurrent callers.
