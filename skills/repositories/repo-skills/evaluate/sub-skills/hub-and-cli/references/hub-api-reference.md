# Evaluate Hub API Reference

Evaluate exposes Hub-facing helpers for publishing custom modules and recording evaluation results. These calls are useful but should be treated as network-bound and potentially mutating.

## `evaluate.push_to_hub`

`evaluate.push_to_hub(...)` writes evaluation results into a model repository's card metadata under `model-index`. The source builds a metadata object and calls `huggingface_hub.repocard.metadata_update(repo_id=model_id, metadata=metadata, overwrite=overwrite)`.

Required arguments:

| Argument | Meaning |
| --- | --- |
| `model_id` | Hub model repository id, for example `username/model-name`. |
| `task_type` | Hub task id. Must be in Evaluate's allowed task list or a `ValueError` is raised. |
| `dataset_type` | Hub dataset id used for the evaluation. |
| `dataset_name` | Human-readable dataset name. |
| `metric_type` | Hub metric id, for example `accuracy` or `bleu`. |
| `metric_name` | Human-readable metric name. |
| `metric_value` | Numeric metric result value. |

Optional arguments:

| Argument | Metadata location |
| --- | --- |
| `task_name` | `task.name` |
| `dataset_config` | `dataset.config` |
| `dataset_split` | `dataset.split` |
| `dataset_revision` | `dataset.revision` |
| `dataset_args` | `dataset.args` |
| `metric_config` | `metrics[0].config` |
| `metric_args` | `metrics[0].args` |
| `overwrite` | Passed through to `metadata_update`; `False` avoids overwriting existing metric fields. |

Example shape:

```python
import evaluate

evaluate.push_to_hub(
    model_id="username/model-name",
    task_type="text-classification",
    dataset_type="glue",
    dataset_name="GLUE MRPC",
    dataset_config="mrpc",
    dataset_split="validation",
    metric_type="accuracy",
    metric_name="Accuracy",
    metric_value=0.91,
)
```

## Validation and Failure Behavior

The helper checks that `task_type` is supported before contacting the Hub. It then calls `dataset_info(dataset_type)` and logs a warning if the dataset is not found, but continues. It calls `model_info(model_id)` and raises `ValueError` if the model repository is not found.

The final metadata write requires Hub network access and credentials with permission to update the target model card. Use `overwrite=True` only when the user intends to replace existing fields.

## Published Module Spaces

`evaluate-cli create` publishes evaluation modules as Hugging Face Spaces with Gradio SDK. The CLI calls `create_repo(namespace + "/" + module_slug, repo_type="space", space_sdk="gradio", private=args["private"])`, then clones the Space, renders the cookiecutter template, and pushes the default commit through `Repository.git_add()`, `Repository.git_commit(...)`, and `Repository.git_push()`.

Namespace behavior:

- With `--organization`, the organization string becomes the Space namespace.
- Without `--organization`, the CLI calls `HfApi().whoami()["name"]`, requiring an authenticated token.
- `--private` requests private Space creation and may require permissions or plan support.

## Credential Boundaries

Safe to run without credentials:

- importing Evaluate modules for local inspection;
- `evaluate-cli --help` when optional CLI dependencies are compatible;
- the bundled `scripts/inspect_evaluate_cli.py` inspector;
- drafting module files and tests manually.

Requires token/network and explicit approval:

- `huggingface-cli login` or any token setup;
- `evaluate-cli create ...`;
- `git clone`, `git push`, or `Repository.git_push()` against Hub Spaces;
- `evaluate.push_to_hub(...)` metadata writes;
- creating private Spaces or writing under an organization namespace.

## Dependency Compatibility Notes

The current CLI source imports `Repository` from `huggingface_hub`. If an installed Hub client no longer exposes that symbol, importing `evaluate.commands.evaluate_cli` can raise `ImportError`. Either install a compatible `huggingface_hub` version for this Evaluate checkout or avoid CLI publishing flows and author the module files manually.

The template extra installs CLI/template dependencies such as Cookiecutter. Gradio is relevant for widget execution, but not required for safe CLI help inspection unless the installed extra pulls it in for the user's environment.
