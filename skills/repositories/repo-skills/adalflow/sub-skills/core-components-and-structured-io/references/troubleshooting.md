# Troubleshooting Core Components and Structured I/O

Use this table before changing an AdalFlow core pipeline. Keep fixes service-free until the component/data contract is correct.

| Symptom | Likely cause | Recovery |
|---|---|---|
| `to_dict()` says it was not called on a dataclass instance, or `DataClassParser` says `data_class must be a dataclass` | The class inherits `DataClass` but is missing Python's `@dataclass` decorator. | Add `@dataclass` above the class, keep fields as dataclass fields, then rerun serialization/parser checks. |
| `DataClassParser` says the class is not a subclass of `DataClass` | A plain dataclass or dict schema was passed where AdalFlow expects a `DataClass` subclass. | Make the output class inherit `adalflow.DataClass`, or use a lower-level `JsonParser`/`YamlParser` if a plain dict is enough. |
| Constructor or `from_dict` fails with a required-field error | A field uses `required_field()` or has no default, but the input dict/string omitted it. | Add the required key to the parsed data. Do not exclude required fields before restoration. If the field should be optional, give it an explicit default. |
| `TypeError: non-default argument ... follows default argument` when defining a dataclass | A required field without a default appears after an optional field. | Reorder fields so required ones come first, or use `field(default_factory=required_field(), metadata=...)` for required fields that must appear after optional fields. |
| Mutable values are shared or field defaults behave unexpectedly | A list/dict/set was used as a direct dataclass default, or a factory captures a mutable object incorrectly. | Use `field(default_factory=list)`, `field(default_factory=dict)`, or a factory function that creates a fresh object. |
| `Either include or exclude can be used, not both.` | `to_dict`, `to_schema`, or signature helper received both options. | Choose one. Use `include=[...]` for allowlists on the current dataclass, or `exclude={"ClassName": [...]}` for nested removals. |
| Nested fields are not excluded | The nested exclusion key does not match the dataclass class name, or a list exclusion was used for nested data. | Use a dict keyed by class name, such as `exclude={"Parent": ["secret"], "Child": ["url"]}`. |
| Parsed output is a dict but code expects attributes | Parser was created with `return_data_class=False` or a low-level string parser was used. | Use `DataClassParser(..., return_data_class=True)` when attribute access is wanted. Otherwise access dict keys. |
| Parser raises `ValueError` for invalid JSON | The text has extra prose, unmatched brackets, malformed quotes, unescaped newlines, trailing syntax, or schema text instead of actual values. | First isolate the raw model text. Ensure the output is actual JSON data, not the schema. Prefer `JsonParser` for complex strings and make the prompt say "output only valid JSON". |
| Parser repair succeeds on simple mistakes but fails on code-like strings | `JsonParser` can repair some missing braces/commas, but cannot fix arbitrary quoting or embedded code fences inside JSON strings. | Escape quotes/backslashes/newlines in string values. For code-like payloads, validate with a local parser before live generator use. |
| YAML parser accepts unexpected scalars or fails on nested data | YAML is permissive and the parser extracts text before `yaml.safe_load`. Complex structures may be ambiguous. | Prefer JSON for nested structured model outputs. If YAML is required, wrap the YAML block in fences and keep indentation simple. |
| Prompt rendering raises `Error rendering Jinja2 template` or undefined-variable errors | Template variable names do not match `prompt_kwargs` or call-time kwargs. AdalFlow uses strict Jinja undefineds. | Check `prompt.get_prompt_variables()`. Pass every variable by the same name or provide defaults in `prompt_kwargs`. |
| Prompt prints `None` or stale values | A variable was preset to `None`, omitted at call time, or `prompt_kwargs` was copied during construction and not updated. | Pass the runtime value to `prompt(...)`, or call `prompt.update_prompt_kwargs(name=value)` before rendering. |
| Child component is absent from `named_components()` | The child was assigned before `super().__init__()` or stored inside a plain container that does not register components. | Call `super().__init__()` first. Assign direct child components as attributes or use `Sequential`/`ComponentList`. |
| Error says `cant assign component before Component.__init__() call` | A subclass forgot `super().__init__()` before assigning a `Component` attribute. | Put `super().__init__()` as the first statement in `__init__`. |
| `Component.__call__` raises that output should be `Parameter` in training mode | `train()` was enabled on a component whose `call`/`bicall` returns ordinary data. | Use `eval()` for inference/preprocessing, or implement `forward`/training `bicall` to return an AdalFlow `Parameter`. Optimizer details belong to the optimization sub-skill. |
| `Component.__call__` raises that output should not be `Parameter` in eval mode | A training-oriented component returned a `Parameter` while in eval mode. | Return ordinary `.data`/inference output in eval mode, or switch to `train()` only when an optimizer workflow expects parameters. |
| `Sequential` passes the wrong arguments to later steps | Only the first component receives the original arbitrary args/kwargs; later components receive the previous output. | Make later components accept one positional input, or have an intermediate component return `(args_tuple, kwargs_dict)` for the next step. |
| Async component did not run | `acall` must be invoked explicitly with `await component.acall(...)`; ordinary `component(...)` uses sync `call`/`forward`/`bicall`. | Add an async call path and test it with `asyncio.run(...)` in service-free code before connecting to external I/O. |

## Quick isolation checklist

1. Run the relevant bundled smoke script from this sub-skill.
2. Confirm imports and class decorators before debugging parser behavior.
3. Serialize a hand-built `DataClass` instance with `to_dict`, `to_json`, and `to_yaml`.
4. Parse a hand-written JSON/YAML string with the exact parser instance used in the workflow.
5. Render the `Prompt` with all variables supplied and inspect `get_prompt_variables()`.
6. Only after the service-free path passes, connect a generator/provider workflow in the appropriate sub-skill.
