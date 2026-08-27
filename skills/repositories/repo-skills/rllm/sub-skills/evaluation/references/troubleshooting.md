# Evaluation Troubleshooting

| Symptom | Likely cause | Action |
| --- | --- | --- |
| `No evaluator found for '<benchmark>'` | Dataset has no catalog reward function or verifier, and no `--evaluator` override | Add a `[verifier]` block in the dataset/task metadata or pass an evaluator registry name/import path. |
| `AgentFlow returned unsupported type` | Rollout returned a raw string/dict/object | Return `Episode`, `Trajectory`, or `None`; put raw text in a `Step.output` or trajectory metadata. |
| `@evaluator function returned unsupported type` | Evaluator returned a custom object/list/dict | Return `EvalOutput`, `float`, `bool`, or `(float, bool)`. |
| Import failure for `AgentConfig` | Using stale docs/imports | Import `AgentConfig` from `rllm.types`. |
| Import failure for `SimpleWorkflow` from `rllm.workflows` | `SimpleWorkflow` is not top-level exported in this revision | Import from `rllm.workflows.simple_workflow`. |
| Eval hangs or fails before rollout | Sandbox backend unavailable or task environment requires remote/local setup | Re-run a small slice with `--max-examples 1`, explicit `--sandbox-backend`, and `--no-snapshot`; verify backend credentials/runtime separately. |
| `--base-url` run fails model validation | Missing model string | Pass `--model` whenever using explicit `--base-url`. |
| Saved episode files are absent | `--no-save-episodes` was used or output directory was not writable | Re-run with `--save-episodes` and explicit `--episodes-dir`. |
| pass@k metrics look wrong | `--attempts` too small or evaluator returns only rewards with no correctness signal | Increase attempts and return `EvalOutput(is_correct=...)` when correctness matters. |

For dataset layout failures, switch to the datasets sub-skill. For gateway trace/token/logprob failures, switch to the training sub-skill and `references/gateway-and-traces.md`.
