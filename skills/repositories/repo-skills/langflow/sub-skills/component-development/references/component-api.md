# Component API Reference

Langflow components are Python classes that inherit from `Component`. In current Langflow, the canonical runtime implementation lives in `lfx.custom.custom_component.component.Component`; `langflow.custom.custom_component.component.Component` remains a compatibility shim that re-exports the same class.

## Minimal Skeleton

```python
from lfx.custom.custom_component.component import Component
from lfx.io import MessageTextInput, Output
from lfx.schema.message import Message


class EchoComponent(Component):
    display_name = "Echo"
    description = "Return the input text as a Langflow message."
    icon = "message-square"

    inputs = [
        MessageTextInput(
            name="input_value",
            display_name="Input",
            required=True,
            info="Text to echo.",
            tool_mode=True,
        ),
    ]

    outputs = [
        Output(display_name="Message", name="message", method="build_message"),
    ]

    def build_message(self) -> Message:
        return Message(text=self.input_value)
```

## Imports and Schema Objects

- Prefer `from lfx.custom.custom_component.component import Component` for new code.
- `from langflow.custom import Component` and `langflow.custom.custom_component.component.Component` remain compatible for older code, but new components should use `lfx` imports.
- Common input/output imports are available from `lfx.io`: `MessageTextInput`, `MessageInput`, `DataInput`, `DataFrameInput`, `HandleInput`, `DropdownInput`, `BoolInput`, `IntInput`, `FloatInput`, `SecretStrInput`, `FileInput`, `MultilineInput`, `TableInput`, `ToolsInput`, and `Output`.
- Common return schemas are `lfx.schema.message.Message`, `lfx.schema.data.Data`, and `lfx.schema.dataframe.DataFrame`.
- `Message(...)` accepts text/message metadata and is the right return for chat-like outputs. `Data(...)` carries a `data` dict and text key for structured records. `DataFrame(...)` is used when table-like outputs should appear in the UI.

## Class Metadata

Set these class attributes when authoring a component:

- `display_name`: human-readable palette and node name.
- `description`: concise user-facing purpose.
- `icon`: a Lucide icon name or project-supported custom icon identifier.
- `documentation`: optional URL or documentation pointer.
- `priority`: optional sort hint; lower numbers appear earlier.
- `name`: optional stable internal identifier; if omitted, the class name is used.
- `legacy = True`: marks an old component that must remain loadable while a replacement class takes over new usage.

Do not rely on instance-level metadata assignment during execution. Langflow reads class metadata to build frontend node templates and indexes.

## Inputs

Define `inputs` as a list of input objects. Each input should have a stable `name`, useful `display_name`, and clear `info` text. The runtime maps input values to instance attributes with matching names, so `MessageTextInput(name="query")` becomes `self.query` during execution.

Practical input rules:

- Keep released input names stable. Removing or renaming inputs can disconnect saved flow edges or break tweaks.
- Prefer adding optional inputs with defaults over changing required inputs.
- Mark fields as deprecated instead of deleting them when an old flow may still reference the field.
- Use `SecretStrInput` or password-capable inputs for credentials. The runtime unwraps password input values for component code while preserving secret masking in templates.
- Use `HandleInput` when a component expects another component/integration object rather than a scalar value.
- Use `tool_mode=True` only for fields that should be exposed to tool-calling flows.
- Avoid mutable global objects outside `inputs`; the `Component` constructor deep-copies input templates per instance.

## Outputs

Define `outputs` as a list of `Output` objects. Every output needs a stable `name`, a `display_name`, and normally a `method` string:

```python
outputs = [
    Output(display_name="Data", name="data", method="build_data"),
]
```

Output method rules:

- `method` must be the exact name of an instance method on the component.
- The method can be sync or async; Langflow calls coroutine functions directly and runs sync methods safely in a thread where needed.
- Return type annotations help Langflow infer output types. Use `-> Message`, `-> Data`, `-> DataFrame`, `-> list[Data]`, or the integration type expected by downstream handles.
- Keep released output names and methods stable. Removing outputs can disconnect edges in saved flows.
- If an output has `method=None`, the runtime cannot execute it as a normal component output; use this only for advanced dynamic-output patterns with explicit handling.
- Avoid overlapping input and output names. The base `Component` constructor raises a `ValueError` when an input name and output name collide.

## Execution Methods and State

- Use `component.set(input_name=value)` in tests and helper code to set input values fluently.
- `component.run()` executes the component's selected output path through the base runtime.
- Output methods may update `self.status` with a `Message`, `Data`, `DataFrame`, list, or error payload to improve UI feedback.
- If a component needs graph context, use `self.ctx` only after the graph is built; otherwise the base class raises `ValueError("Graph not found. Please build the graph first.")`.
- Use `self.log(...)` sparingly for useful runtime diagnostics, not for control flow.
- Prefer asynchronous methods for file, network, or service operations. Use async file libraries and async clients when practical.

## Compatibility Rules

Langflow saved flows identify components by class name or the component `name` attribute. Treat both as public API once released.

Do:

- Change `display_name` when wording or UX needs improvement.
- Add optional fields and outputs with defaults.
- Deprecate old fields in place and document the replacement.
- Keep old output methods callable even if a new method becomes preferred.
- Create a new component class for a true replacement and mark the old class with `legacy = True`.

Do not:

- Rename a released class for style only.
- Rename or remove a released `name` attribute.
- Delete fields or outputs without a migration plan.
- Reuse the same input/output `name` for a different semantic meaning.
- Return non-serializable provider objects from outputs intended for UI display.

## Component Tests

Component tests use standardized base classes from `tests.base`:

```python
import pytest
from tests.base import ComponentTestBaseWithoutClient


class TestEchoComponent(ComponentTestBaseWithoutClient):
    @pytest.fixture
    def component_class(self):
        return EchoComponent

    @pytest.fixture
    def default_kwargs(self):
        return {"input_value": "hello"}

    @pytest.fixture
    def file_names_mapping(self):
        return []
```

Use `ComponentTestBaseWithClient` when a component needs a FastAPI test client. Use `ComponentTestBaseWithoutClient` for pure component logic.

Test conventions:

- Mirror component directory structure under the component unit test tree.
- Name test files `test_<component_file>.py`.
- Group tests in classes named `Test<ClassName>`.
- Implement `component_class`, `default_kwargs`, and `file_names_mapping` fixtures.
- Keep standalone helper tests only when they are clearly outside a component class contract.
- Use Arrange, Act, Assert structure and assert on `Message`, `Data`, `DataFrame`, frontend node template fields, and error behavior.
- For released components, `file_names_mapping` records historical `version`, `module`, and `file_name` values so compatibility tests can build previous component versions. New unreleased components may use an empty mapping.
- Guard credentialed tests with skip logic or project markers instead of requiring secrets locally.

## Static Preflight Checklist

Before running expensive tests, verify:

- The file parses with `python -m py_compile`.
- Exactly the intended class inherits from `Component`.
- The class has `display_name`, `description`, `icon`, `inputs`, and `outputs`.
- Every statically visible `Output(method="...")` references a method defined on the class or inherited intentionally.
- Input names and output names do not overlap.
- Released class/name identifiers are unchanged.
- Optional dependencies are imported lazily or declared in the owning package metadata.
