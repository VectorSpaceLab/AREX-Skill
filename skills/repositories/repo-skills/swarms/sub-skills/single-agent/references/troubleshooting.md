# Single-agent troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: swarms` | The package is not installed in the active environment | Reinstall `swarms` in the inspection environment and rerun the smoke check. |
| Memory files appear in an unexpected folder | `WORKSPACE_DIR` is unset or points somewhere else | Set `WORKSPACE_DIR` before constructing the agent. |
| Skills do not load | `skills_dir` is missing, empty, or points at the wrong level | Point it at the directory that contains one folder per skill, each with `SKILL.md`. |
| Marketplace prompt fetch fails | `SWARMS_API_KEY` is missing or invalid | Set the API key and retry the fetch or publish action. |
| Provider call fails even though the agent built | Model, cache, reasoning, or multimodal parameters do not match the provider | Remove unsupported options or switch to a compatible model family. |
| Streaming works but the final answer fails | A later tool or fallback step failed | Re-run with a fixed loop count and inspect the fallback or tool output path. |
| Artifact save/load errors | The target file path is not writable or the parent folder does not exist | Move the artifact to a writable temp path and retry. |

## Recovery order

1. Verify the package imports and the version matches the repo.
2. Confirm `WORKSPACE_DIR`, `skills_dir`, and any required provider keys.
3. Retry with a minimal constructor before turning on caching, memory, marketplace prompts, or multimodal input.
4. Only after the offline check passes should you attempt a live model call.
