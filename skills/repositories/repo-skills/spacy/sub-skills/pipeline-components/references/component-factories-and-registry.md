# Component factories and registry

Validated against spaCy 3.8.15 on the installed CPU environment.

Evidence provenance: `spacy/language.py`, `spacy/registrations.py`, `spacy/schemas.py`, `spacy/tests/pipeline/test_pipe_factories.py`, and `website/docs/usage/processing-pipelines.mdx`.

## Installed API surface

```python
Language.component(name: str, *, assigns: Iterable[str] = [], requires: Iterable[str] = [], retokenizes: bool = False, func: Optional[Callable[[spacy.tokens.doc.Doc], spacy.tokens.doc.Doc]] = None) -> Callable[..., Any]
Language.factory(name: str, *, default_config: Dict[str, Any] = {}, assigns: Iterable[str] = [], requires: Iterable[str] = [], retokenizes: bool = False, default_score_weights: Dict[str, Optional[float]] = {}, func: Optional[Callable] = None) -> Callable
Language.has_factory(name: str) -> bool
Language.get_factory_meta(name: str) -> 'FactoryMeta'
Language.get_pipe_meta(self, name: str) -> 'FactoryMeta'
Language.get_pipe_config(self, name: str) -> Config
```

`FactoryMeta` carries `factory`, `default_config`, `assigns`, `requires`, `retokenizes`, `default_score_weights`, and `scores`.

## When to use which decorator

- Use `@Language.component` for a stateless function component that takes a `Doc` and returns the same `Doc`.
- Use `@Language.factory` when the component needs settings, shared `nlp` access, or returns a stateful object.
- Both decorators can also be called directly with `func=...` instead of used as decorators.
- `@Language.component` is for functions. If you try to put it on a class, spaCy raises the class-vs-function error and you should switch to `@Language.factory`.
- Factory names must be strings and may not contain dots.
- Re-registering the same implementation is reload-safe; registering a different function under the same factory name is a duplicate-factory error.

## Registry and metadata model

`Language.has_factory(name)` checks the active subclass first and then the base registry. Prefer it over direct registry inspection when you need a boolean answer.

`Language.get_factory_meta(name)` expects the factory name. `Language.get_pipe_meta(name)` expects the pipeline instance name. `Language.get_pipe_config(name)` returns the stored config for that pipeline instance after defaults and sourcing are resolved.

Use `spacy.util.registry.factories.get_all()` only when you need to inspect the full registry table. Built-ins are populated by spaCy; custom factories appear only after the module that registers them has been imported.

## What the metadata controls

- `assigns` and `requires` feed static pipe analysis.
- `retokenizes=True` tells pipe analysis that token boundaries can change.
- `default_score_weights` becomes the score list on `FactoryMeta` and drives the training score aggregation.
- `default_config` is merged into the component config before resolution.
- Config values must be JSON-serializable. Use registry references such as `{"@misc": ...}` or `{"@scorers": ...}` for callables and resources.

## Minimal custom component example

```python
import spacy
from spacy.language import Language
from spacy.tokens import Doc

if not Doc.has_extension("flagged"):
    Doc.set_extension("flagged", default=False)

@Language.component("flag_doc", assigns=["doc._.flagged"])
def flag_doc(doc: Doc) -> Doc:
    doc._.flagged = True
    return doc

nlp = spacy.blank("en")
nlp.add_pipe("flag_doc")
```

## Minimal custom factory example

```python
import spacy
from pydantic import StrictInt
from spacy.language import Language
from spacy.tokens import Doc

if not Doc.has_extension("too_long"):
    Doc.set_extension("too_long", default=False)

class LengthGate:
    def __init__(self, max_tokens: int):
        self.max_tokens = max_tokens

    def __call__(self, doc: Doc) -> Doc:
        doc._.too_long = len(doc) > self.max_tokens
        return doc

@Language.factory(
    "length_gate",
    default_config={"max_tokens": 10},
    assigns=["doc._.too_long"],
    default_score_weights={"length_gate_score": 1.0},
)
def make_length_gate(nlp, name, max_tokens: StrictInt):
    return LengthGate(max_tokens)

nlp = spacy.blank("en")
nlp.add_pipe("length_gate", config={"max_tokens": 12})
```

## Validation notes

- A missing `nlp` or `name` argument on a factory is a registration error.
- A bad default-config type or non-serializable config value is a validation error.
- `assigns` / `requires` strings are only metadata; they do not enforce runtime behavior.
- If the registry lookup looks wrong, check whether the module defining the decorator has actually been imported.

## Handoff to other sub-skills

- For ordering, source copying, and `from_config` assembly, read `pipeline-assembly-and-analysis.md`.
- For factory names and the installed built-in catalog, read `built-in-components.md`.
- For symptom-to-fix mappings, read `troubleshooting.md`.
