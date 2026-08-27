# task-authoring troubleshooting

Use this page when a task YAML, `utils.py`, or metric contract is wrong.
It covers parsing errors, request-shape mismatches, and scorer wiring problems.

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| YAML parsing fails | The file has an indentation error, a bad `include`, or a stale key | Re-check the config against the task reference and load the registry smoke first. |
| The model gets the wrong request tuple shape | `output_type` and formatter choice do not match the model family | Compare the task against the request-shape table in `api-reference.md`. |
| `process_results` returns a key that is not scored | `metric_list` and the scorer disagree on metric names | Align the returned keys and the metric list before changing any logic. |
| `doc_to_messages` exists but the model still sees text-only input | The task is being loaded as the wrong task type or the formatter returns the wrong structure | Revisit `task_type` and the message-shape examples in the task reference. |
| A dataset split cannot be found | The split name or dataset metadata is wrong | Check the split names, template inheritance, and any dataset-specific kwargs. |
| Reasoning stripping changes the score unexpectedly | The task-level `reasoning_tags` override is different from the CLI default | Decide whether the task or the command should own stripping, then make the choice explicit. |

## Fast recovery steps

1. Confirm the task is visible in the registry.
2. Identify the intended output type before changing the formatter.
3. Make the request shape and `process_results` contract explicit.
4. Use the task registry smoke after every YAML or formatter change.
5. If the bug is actually model-specific, hand it to `model-backends`.
