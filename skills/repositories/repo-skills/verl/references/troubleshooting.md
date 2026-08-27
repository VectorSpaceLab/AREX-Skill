# Cross-Cutting Troubleshooting

Use this reference when a verl failure spans more than one sub-skill. Route to the nearest sub-skill once the failure surface is clear.

## First Triage

1. **Import or dependency failure**: run `sub-skills/setup-and-backends/scripts/check_verl_environment.py --pretty --check-pip` and route to `setup-and-backends`.
2. **Data or reward failure**: validate parquet rows with `sub-skills/data-and-rewards/scripts/validate_verl_parquet.py` and route to `data-and-rewards`.
3. **Hydra or config failure**: inspect the exact override path and route to `training-and-configs`.
4. **Rollout/tool failure**: identify whether the engine, tool schema, tokenization, or generation server failed and route to `rollout-and-tools`.
5. **Checkpoint/export failure**: classify the path with `sub-skills/checkpoints-and-model-ops/scripts/inspect_checkpoint_path.py` and route to `checkpoints-and-model-ops`.
6. **Repository contribution failure**: route to `repo-development` before editing generated configs, AGENTS.md, tests, or PR-facing changes.

## Common Symptoms

| Symptom | Likely Surface | Next Step |
| --- | --- | --- |
| `ModuleNotFoundError` for `torch`, `ray`, `tensordict`, `hydra`, `transformers`, or backend packages | Setup | Use `setup-and-backends`; verify base vs optional extras and package bounds. |
| `tensordict` resolver conflict or runtime behavior drift | Setup/training | Install a compatible `tensordict>=0.8.0,<=0.10.0,!=0.9.0`; re-run import checks. |
| `data.train_files` loads but training crashes on prompt keys or ground truth | Data/training | Validate parquet schema and reward metadata before changing PPO overrides. |
| `data.truncation=error` reports overlong prompts | Data/training | Decide between filtering, increasing max prompt length, or explicit truncation; check memory impact. |
| Hydra says an override key is unknown or cannot merge | Training | Read `training-and-configs/references/configuration.md`; verify the current config group and nested key. |
| vLLM/SGLang rollout imports fail after base verl install | Setup/rollout | Install the selected backend stack in a compatible environment; base import success is not rollout validation. |
| Function tool schema generation fails | Rollout/tools | Run the function-tool validator; fix type hints, `Args:` docs, varargs, or duplicate tool names. |
| Tokenization sanity mismatch in multi-turn rollout | Rollout/tools | Keep strict mode until the model chat template is understood; use `ignore_strippable` only for whitespace drift. |
| `verl.model_merger` cannot identify checkpoint layout | Checkpoints | Inspect the run/step/role directory and select FSDP, Megatron, or existing HuggingFace export path deliberately. |
| Generated trainer config CI fails | Repo development/training | Regenerate through the repo script and review generated diffs; do not hand-edit generated YAML. |

## Safety Boundaries

- Do not run GPU/NPU/e2e tests, dataset download scripts, Docker builds, long training jobs, checkpoint merge commands, or repo-mutating generation scripts unless explicitly authorized.
- Treat CPU-safe import, parser, schema, and directory-layout checks as first-line diagnostics.
- Record skipped native checks as skipped, not passed, when hardware, credentials, network, or large data are unavailable.
