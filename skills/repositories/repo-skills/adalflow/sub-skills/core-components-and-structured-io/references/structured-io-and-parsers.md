# Structured I/O and Parser Recipes

Use these recipes to build deterministic AdalFlow data contracts before connecting them to model-client or generator workflows elsewhere. All examples are service-free.

## Recipe: define an AdalFlow DataClass

```python
from dataclasses import dataclass, field
from typing import List
import adalflow as adal

@dataclass
class Citation(adal.DataClass):
    title: str = field(metadata={"desc": "Short cited work title."})
    url: str = field(default="", metadata={"desc": "Optional URL."})

@dataclass
class ResearchAnswer(adal.DataClass):
    question: str = field(default=None, metadata={"desc": "Original user question."})
    answer: str = field(default_factory=adal.required_field(), metadata={"desc": "Direct answer."})
    citations: List[Citation] = field(default_factory=list, metadata={"desc": "Supporting citations."})

    __input_fields__ = ["question"]
    __output_fields__ = ["answer", "citations"]
```

Guidelines:

- Always use `@dataclass` on classes that inherit `adal.DataClass`.
- Use `field(metadata={"desc": "..."})` or `metadata={"description": "..."}` so signatures are useful in prompts.
- Use `default_factory=list` / `dict` / `set` for mutable defaults.
- Use `default_factory=adal.required_field()` for required fields that appear after optional fields.
- Set `__input_fields__` and `__output_fields__` to control prompt serialization order. Fields not listed are appended after the listed fields.

## Recipe: serialize and restore

```python
item = ResearchAnswer(
    question="What is AdalFlow?",
    answer="A framework for building and optimizing LLM task pipelines.",
    citations=[Citation(title="Project documentation")],
)

as_dict = item.to_dict()
as_json = item.to_json()
as_yaml = item.to_yaml()
restored = ResearchAnswer.from_dict(as_dict)
assert restored == item
```

Class-level schema/signature helpers:

```python
json_signature = ResearchAnswer.to_json_signature(include=["answer", "citations"])
yaml_signature = ResearchAnswer.to_yaml_signature(include=["answer", "citations"])
schema_text = ResearchAnswer.to_schema_str()
```

Use signatures for concise prompt instructions and schema text when a more explicit JSON-schema-like description is needed.

## Recipe: include and exclude fields safely

`include` and `exclude` cannot be used together.

```python
# Only current-class fields.
public = item.to_dict(include=["answer", "citations"])
without_question = item.to_dict(exclude=["question"])

# Nested dataclass exclusions by class name.
redacted = item.to_dict(exclude={"ResearchAnswer": ["question"], "Citation": ["url"]})
```

Do not exclude required fields from data that you will later pass to `from_dict`, `from_json`, or `from_yaml`; reconstruction will fail because required data is missing.

## Recipe: build parser-driven prompt instructions

`DataClassParser` is the preferred parser when a response should match an AdalFlow `DataClass`.

```python
parser = adal.DataClassParser(
    data_class=ResearchAnswer,
    return_data_class=True,
    format_type="json",
)

output_format_str = parser.get_output_format_str()
input_str = parser.get_input_str(ResearchAnswer(question="What is AdalFlow?", answer="placeholder"))
```

For YAML, set `format_type="yaml"`. Use YAML for simple objects; prefer JSON for complex nested structures, escaped strings, or code-like content.

Parsing service-free strings:

```python
raw_response = '''```json
{"answer": "A task-pipeline framework.", "citations": [{"title": "Docs", "url": ""}]}
```'''
parsed = parser(raw_response)
assert parsed.answer.startswith("A task")
```

Set `return_data_class=False` if the downstream function expects a dictionary:

```python
dict_parser = adal.DataClassParser(ResearchAnswer, return_data_class=False, format_type="json")
parsed_dict = dict_parser('{"answer": "ok", "citations": []}')
```

## Recipe: use string parsers directly

Use simple string parsers when a full dataclass schema is unnecessary.

```python
json_obj = adal.JsonParser()('prefix {"ok": true, "n": 3}')
yaml_obj = adal.YamlParser()("""```yaml
ok: true
n: 3
```""")
items = adal.ListParser()('choose ["alpha", "beta"]')
flag = adal.BooleanParser()("The answer is true.")
number = adal.IntParser()("count = 42")
score = adal.FloatParser()("score: 0.875")
```

Parser behavior notes:

- `JsonParser` extracts the first JSON object or list and can patch some missing right braces and missing commas.
- Parser repair is not validation. For high-stakes outputs, parse first, then validate fields/types with a `DataClass` or pydantic-based parser owned by the relevant workflow.
- Invalid JSON/YAML raises `ValueError` or a parser-specific exception; catch it close to the parsing boundary and preserve the raw text for debugging.

## Recipe: render Jinja prompts

```python
template = """
<SYSTEM>
Return a structured answer.
{{ output_format_str }}
</SYSTEM>
<USER>{{ question }}</USER>
"""

prompt = adal.Prompt(
    template=template,
    prompt_kwargs={"output_format_str": parser.get_output_format_str()},
)
rendered = prompt(question="What is AdalFlow?")
```

Prompt safety checks:

- Call `prompt.get_prompt_variables()` to inspect detected variables.
- Keep variable names consistent between the template and call-time kwargs.
- Missing variables raise render errors because AdalFlow uses Jinja `StrictUndefined`.
- Preset `prompt_kwargs` are copied during initialization. Use `update_prompt_kwargs(...)` if they must change.

## Recipe: compose a small service-free task pipeline

```python
class Normalize(adal.Component):
    def __init__(self):
        super().__init__()

    def call(self, text: str) -> str:
        return " ".join(text.strip().split())

class WrapPrompt(adal.Component):
    def __init__(self, parser: adal.DataClassParser):
        super().__init__()
        self.prompt = adal.Prompt(
            template="Question: {{ question }}\n{{ output_format_str }}",
            prompt_kwargs={"output_format_str": parser.get_output_format_str()},
        )

    def call(self, question: str) -> str:
        return self.prompt(question=question)

pipeline = adal.Sequential(Normalize(), WrapPrompt(parser))
prompt_text = pipeline("  What is AdalFlow?  ")
```

When a later workflow connects this prompt to a live `Generator`, keep generator/model-client details in the generator sub-skill. This sub-skill's job is to make the data contract and service-free preprocessing correct first.

## Recipe: custom parsing as DataComponent

Use `DataComponent` for deterministic custom transforms.

```python
class LastLine(adal.DataComponent):
    def call(self, text: str) -> str:
        return text.strip().splitlines()[-1]
```

Or use `func_to_data_component` for a compact function wrapper:

```python
@adal.func_to_data_component
def parse_final_answer(text: str) -> str:
    return text.strip().split("Answer:")[-1].strip()
```

These components can be placed in `Sequential` or used as output processors in generator workflows, but they do not require provider calls by themselves.
