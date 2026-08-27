# Component Development

Kotaemon treats a component as the reusable unit of execution. Pipelines are also components: they declare typed construction fields, optionally depend on nested components, and implement processing in `run(...)`.

## Core Contract

A custom component should:

1. Import `BaseComponent` from `kotaemon.base`.
2. Define a class that subclasses `BaseComponent` or a more specific Kotaemon/ktem base class.
3. Declare init params and child nodes with type annotations.
4. Implement `run(...)` with the input and output contract expected by the caller.

Minimal shape:

```python
from kotaemon.base import BaseComponent


class MyPipeline(BaseComponent):
    prompt_prefix: str = "Answer briefly"
    top_k: int = 5

    def run(self, question: str):
        return f"{self.prompt_prefix}: {question}"
```

Kotaemon's `BaseComponent` comes from `kotaemon.base.component`. It inherits from `theflow.Function`, exposes `flow()` for upstream chaining, supports `set_output_queue(...)`/`report_output(...)` for streaming UI output, and requires subclasses to implement `run(...)`.

## Params, Nodes, and UI Visibility

- Plain annotated fields become component parameters that can be inspected by tooling.
- Fields annotated with `BaseComponent` or another component type represent nested nodes when they are assigned component instances.
- `Param(...)` from `kotaemon.base` can set defaults, help text, or `ignore_ui=True` when a field should not be exported to UI settings.
- `Node(...)`, `Node.auto(...)`, and `lazy(...)` are used in built-in pipelines to declare dependent subcomponents without immediately instantiating all resources.

Use type annotations deliberately. Prompt UI and settings exporters depend on annotations to decide which fields are user-tunable params and which fields are component nodes.

## Reasoning Pipeline Contract

Reasoning pipelines are registered by dotted class path in `KH_REASONINGS` in `flowsettings.py`. The app imports each class, calls `get_info()["id"]`, stores it in the `reasonings` registry, and calls `reasoning_cls().get_user_settings()` to populate the Settings page.

A reasoning class should provide:

```python
class CustomReasoning(BaseComponent):
    @classmethod
    def get_info(cls) -> dict:
        return {
            "id": "custom-reasoning",
            "name": "Custom Reasoning",
            "description": "Short user-facing description",
        }

    @classmethod
    def get_user_settings(cls) -> dict:
        return {
            "max_steps": {
                "name": "Max steps",
                "value": 4,
                "component": "number",
            }
        }

    @classmethod
    def get_pipeline(cls, settings: dict):
        return cls(max_steps=settings["reasoning.custom-reasoning.max_steps"])

    def run(self, question: str, history: list, **kwargs):
        ...
```

The documented reasoning `run` signature is `run(self, question: str, history: list, **kwargs) -> Document`. Async `run(...)` is allowed for streaming. Use `self.report_output({"output": text})` for answer text and `self.report_output({"evidence": evidence_text})` for evidence-panel updates when the pipeline is wired with an output queue.

## Prompt UI and Developer Utilities

Kotaemon's prompt engineering utility can export component params to a YAML config and run a Gradio test UI. Use it for developer/tester workflows where prompts and other params need iteration:

```bash
kotaemon promptui export package.module.PipelineClass --output promptui.yml
kotaemon promptui run promptui.yml
```

The exported config includes `params`, `inputs`, `outputs`, and `logs`. Remove fields that should not be user-editable, or declare them with `Param(..., ignore_ui=True)` in the component.

Supported prompt/settings component ids are `text`, `checkbox`, `dropdown`, `file`, `image`, `number`, `radio`, `slider` for prompt UI. The ktem Settings page supports `text`, `number`, `checkbox`, `dropdown`, `radio`, and `checkboxgroup`.

## Project and Component Templates

The repository includes a cookiecutter project template with:

- `cookiecutter.json` defaults such as `project_name` and `ptl`.
- Generated project metadata in `setup.py`.
- A Python package directory containing `pipeline.py`.
- Test and repository hygiene files such as `.pre-commit-config.yaml`, `.gitignore`, and `.gitattributes`.

A generated project must be importable before its dotted paths are added to `flowsettings.py`. Install it editable during development, then reference classes by full module path such as `my_project.pipeline.QuestionAnsweringPipeline`.

The component template is sparse in this checkout. Treat it as a reminder to create a class file plus packaging metadata, not as a complete compatibility guarantee.

## Contribution Clues

For source contributions:

- Use Python 3.10 or newer for local development when possible.
- Install the `kotaemon` library in editable mode with optional dependencies only when the task needs them.
- Install pre-commit hooks before preparing a pull request.
- Run focused tests for the changed package; optional provider/parser tests may require credentials or large dependencies.
- If dependencies change, bump the package version so CI environment caches are refreshed; use `[ignore cache]` only when intentionally forcing a fresh CI environment.

## Cross-Links

- Use `index-extension.md` when the component will be registered as a file-index indexing or retrieval pipeline.
- Use `plugin-ui-extension.md` when the component needs a settings tab, page, public event, pluggy package, or app lifecycle integration.
- Use `../../rag-core/SKILL.md` for deeper `Document`, retrieval, vector index, reranker, QA, and citation internals.
- Use `../../model-providers/SKILL.md` for LLM/embedding/reranking managers and provider setup.
