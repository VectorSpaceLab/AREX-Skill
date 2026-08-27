---
name: core-components-and-structured-io
description: "Build service-free AdalFlow Component, DataClass, Prompt, parser,
  and structured-output pipelines."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Core Components and Structured I/O

Use this sub-skill when a task needs AdalFlow's service-free building blocks:

- `Component`, `DataComponent`, `Sequential`, nested component/parameter registration, state dictionaries, and lifecycle methods.
- `DataClass`, `required_field`, JSON/YAML/schema/signature helpers, and nested dataclass serialization.
- `DataClassParser`, string parsers, output parser selection, and Jinja `Prompt` rendering.
- Small deterministic task-pipeline prototypes that do not call a live provider.

Do **not** use this sub-skill for live model calls, provider clients, or `Generator` internals; route those to `model-client-and-generator-workflows`. Route tool/agent/streaming work to `agents-tools-and-streaming`, and trainer/optimizer work to `evaluation-and-optimization`.

## Load order

1. Read [core API reference](references/core-api-reference.md) for verified signatures, lifecycle rules, object relationships, and routing boundaries.
2. Read [structured I/O and parsers](references/structured-io-and-parsers.md) for copyable DataClass, parser, prompt, and mini-pipeline recipes.
3. If behavior is surprising, read [troubleshooting](references/troubleshooting.md) before changing code.
4. For a deterministic environment check, run [structured IO smoke](scripts/structured_io_smoke.py) or [core component smoke](scripts/core_component_smoke.py). These scripts do not use provider credentials, network, datasets, or model calls.

## Operating rules

- Always call `super().__init__()` before assigning child `Component` or `Parameter` attributes in a custom `Component`.
- Implement `call` for synchronous inference. Implement `acall` only when the component genuinely has async work. Implement `forward` or `bicall` only for training-mode behavior.
- In `train()` mode, `Component.__call__` expects a `Parameter` output; in `eval()` mode, it rejects `Parameter` outputs. `DataComponent` is intentionally non-trainable and dispatches directly to `call`.
- Decorate every `DataClass` subclass with `@dataclass`; use `field(metadata={"desc": ...})` or `metadata={"description": ...}` to make prompt schemas useful.
- Prefer `default_factory` for mutable fields, and use `required_field()` when a required field must appear after optional fields.
- For structured model outputs, generate prompt instructions with `DataClassParser.get_output_format_str()` and parse service-free strings with the same parser before connecting a `Generator` elsewhere.
