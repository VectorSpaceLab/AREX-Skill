# Core API Reference

This reference distills the service-free AdalFlow APIs owned by this sub-skill. It intentionally excludes `Generator`, provider clients, tools/agents, and training optimizers except where their boundaries affect core component design.

## Verified signatures

| API | Verified contract |
|---|---|
| `Component.__init__` | `Component(name: Optional[str] = None, *args, **kwargs)` |
| `DataClass.to_dict` | `instance.to_dict(*, exclude=None, include=None) -> Dict[str, Any]` |
| `DataClassParser.__init__` | `DataClassParser(data_class, return_data_class=True, format_type="json" | "yaml")` |
| `Prompt.__init__` | `Prompt(template=None, prompt_kwargs={})` |

Useful public imports are available from top-level `adalflow` in an installed package: `Component`, `DataComponent`, `Sequential`, `Prompt`, `DataClass`, `required_field`, `DataClassParser`, `JsonParser`, `YamlParser`, `IntParser`, `FloatParser`, `ListParser`, and `BooleanParser`.

## Component lifecycle

`Component` is AdalFlow's pipeline base class. It resembles a small `nn.Module`-style object tree but works with arbitrary Python data.

```python
import adalflow as adal

class NormalizeQuery(adal.Component):
    def __init__(self):
        super().__init__()

    def call(self, query: str) -> str:
        return " ".join(query.strip().split())
```

Lifecycle methods:

- `call(*args, **kwargs)`: implement for synchronous inference. `component(...)` dispatches here when `component.training` is `False` and the class does not override `bicall`.
- `acall(*args, **kwargs)`: implement for asynchronous work and invoke explicitly with `await component.acall(...)`. The base method is a placeholder.
- `forward(*args, **kwargs)`: implement for training-mode calls when a differentiable/optimizable `Parameter` should be returned.
- `bicall(*args, **kwargs)`: optional unified call path. If a subclass overrides it, `__call__` uses `bicall` in both train and eval modes, then validates the output type for the current mode.
- `train(mode=True)`: sets `training` recursively on child components.
- `eval()`: shorthand for `train(False)`.
- `trace(mode=True)` and `use_teacher(mode=True)`: recursively toggle tracing/teacher state; advanced tracing details belong to the tracing sub-skill.

Training/eval output validation matters:

- In `train()` mode, `Component.__call__` expects an `adalflow.Parameter` result and raises if ordinary data is returned.
- In `eval()` mode, `Component.__call__` rejects `Parameter` output and expects ordinary inference data.
- If you are building ordinary service-free preprocessing or parsing steps, keep the component in eval mode and implement `call`.

## DataComponent

`DataComponent` is for preprocessing/postprocessing components such as `Prompt` and string parsers.

- It is not trainable: `train()` keeps `training=False`.
- `__call__` always dispatches directly to `call`.
- Use it when a component should transform Python/text data and never return optimizable `Parameter` objects.

```python
class StripLower(adal.DataComponent):
    def call(self, text: str) -> str:
        return text.strip().lower()
```

## Nested components and parameters

Child components are registered automatically when assigned as attributes after `super().__init__()`:

```python
class QueryPipeline(adal.Component):
    def __init__(self):
        super().__init__()
        self.normalize = NormalizeQuery()
        self.prompt = adal.Prompt(template="Question: {{ question }}")

    def call(self, query: str) -> str:
        return self.prompt(question=self.normalize(query))
```

Inspection helpers:

- `named_children()` / `children()`: immediate child components.
- `named_components()` / `components()`: recursive component tree. The root is emitted with name `""`.
- `named_parameters()` / `parameters()`: recursive `Parameter` members.
- `state_dict()`: shallow parameter state mapping.
- `load_state_dict(state_dict, strict=True)`: update registered parameters from a state mapping.
- `to_dict(exclude=None)` and `from_dict(...)`: component serialization/deserialization for picklable component state. Exclude unserializable attributes.

Important failure mode: assigning a child component before `super().__init__()` raises an attribute error because `_components` has not been initialized.

## Sequential

`Sequential` chains `Component` objects in order.

```python
class Add(adal.Component):
    def call(self, a: int, b: int) -> int:
        return a + b

class Double(adal.Component):
    def call(self, value: int) -> int:
        return value * 2

pipeline = adal.Sequential(Add(), Double())
assert pipeline(2, 3) == 10
```

Rules:

- The first component can receive arbitrary `*args`/`**kwargs`.
- Later components should usually accept one positional input: the previous component's output.
- A component may return `(args, kwargs)` where `args` is a tuple and `kwargs` is a dict to feed multiple arguments into the next component.
- Index by integer or key; append/insert/extend components as needed.

## Prompt

`Prompt` renders Jinja2 templates and is a `DataComponent`.

```python
prompt = adal.Prompt(
    template="""Task: {{ task }}\nInput: {{ input_text }}""",
    prompt_kwargs={"task": "classify sentiment"},
)
text = prompt(input_text="Great service")
```

Key behavior:

- Missing variables are strict Jinja undefineds and surface as render errors.
- `prompt_kwargs` are copied on construction and can be updated with `update_prompt_kwargs(...)`.
- `get_prompt_variables()` returns variables detected from the template.
- Nested `Prompt` values can be passed as prompt kwargs and are rendered recursively with the same context.
- `Parameter` prompt values are converted to their `.data` for rendering; optimization ownership belongs to the optimization sub-skill.

## DataClass basics

`DataClass` must be combined with Python's `@dataclass` decorator:

```python
from dataclasses import dataclass, field
import adalflow as adal

@dataclass
class Answer(adal.DataClass):
    question: str = field(default=None, metadata={"desc": "Input question."})
    answer: str = field(default_factory=adal.required_field(), metadata={"desc": "Final answer."})
    confidence: float = field(default=1.0, metadata={"desc": "Confidence from 0 to 1."})

    __input_fields__ = ["question"]
    __output_fields__ = ["answer", "confidence"]
```

Instance methods:

- `to_dict(exclude=None, include=None)`: serialize with stable field order and support nested dataclasses, lists, dicts, and sets.
- `to_json(...)`, `to_yaml(...)`: string serialization for prompts/examples.
- `to_json_obj(...)`, `to_yaml_obj(...)`: parse the serialized string back to Python objects.
- `format_example_str(DataClassFormatType.EXAMPLE_JSON | EXAMPLE_YAML)`: prompt-ready examples.

Class methods:

- `from_dict(data)`, `from_json(text)`, `from_yaml(text)`: reconstruct instances; missing required fields raise a wrapped error.
- `to_schema(...)`, `to_schema_str(...)`: JSON-schema-like structure.
- `to_json_signature(...)`, `to_yaml_signature(...)`: concise field-name-to-description signatures for prompts.
- `format_class_str(DataClassFormatType.SCHEMA | SIGNATURE_JSON | SIGNATURE_YAML)`: choose the schema/signature representation programmatically.

`include` and `exclude` are mutually exclusive. A list applies to the current dataclass; a dict maps dataclass class names to fields, which is useful for nested structures.

## Parsers owned here

String parsers are deterministic `DataComponent` objects:

| Parser | Input pattern | Return |
|---|---|---|
| `JsonParser(add_missing_right_brace=True)` | JSON object/list, including fenced JSON; can patch some missing braces/commas | `dict` or `list` |
| `YamlParser()` | YAML text or fenced YAML | `dict` or `list` |
| `ListParser(add_missing_right_bracket=True)` | First `[...]` list string | `list` |
| `BooleanParser()` | First boolean-like token | `bool` |
| `IntParser()` | First integer-like token | `int` |
| `FloatParser()` | First float-like token | `float` |

`DataClassParser` wraps `JsonParser` or `YamlParser` with a `DataClass` schema:

```python
parser = adal.DataClassParser(Answer, return_data_class=True, format_type="json")
format_instructions = parser.get_output_format_str()
parsed = parser('{"answer": "Paris", "confidence": 0.98}')
assert isinstance(parsed, Answer)
```

Use `return_data_class=False` when downstream code expects a plain dict.
