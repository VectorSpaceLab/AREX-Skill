# Pipeline assembly and analysis

Validated against spaCy 3.8.15 on the installed CPU environment.

Evidence provenance: `spacy/language.py`, `spacy/pipe_analysis.py`, `spacy/schemas.py`, `website/docs/api/language.mdx`, `website/docs/usage/processing-pipelines.mdx`, and `spacy/tests/pipeline/test_pipe_factories.py`.

## Installed signatures

```python
Language.add_pipe(self, factory_name: str, name: Optional[str] = None, *, before: Union[str, int, NoneType] = None, after: Union[str, int, NoneType] = None, first: Optional[bool] = None, last: Optional[bool] = None, source: Optional[ForwardRef('Language')] = None, config: Dict[str, Any] = {}, raw_config: Optional[confection._config.Config] = None, validate: bool = True) -> Callable[[spacy.tokens.doc.Doc], spacy.tokens.doc.Doc]
Language.pipe(self, texts: Union[Iterable[Union[str, spacy.tokens.doc.Doc]], Iterable[Tuple[Union[str, spacy.tokens.doc.Doc], ~_AnyContext]]], *, as_tuples: bool = False, batch_size: Optional[int] = None, disable: Iterable[str] = [], component_cfg: Optional[Dict[str, Dict[str, Any]]] = None, n_process: int = 1) -> Union[Iterator[spacy.tokens.doc.Doc], Iterator[Tuple[spacy.tokens.doc.Doc, ~_AnyContext]]]
Language.select_pipes(self, *, disable: Union[str, Iterable[str], NoneType] = None, enable: Union[str, Iterable[str], NoneType] = None) -> 'DisabledPipes'
Language.analyze_pipes(self, *, keys: List[str] = ['assigns', 'requires', 'scores', 'retokenizes'], pretty: bool = False) -> Optional[Dict[str, Any]]
Language.from_config(config: Union[Dict[str, Any], confection._config.Config] = {}, *, vocab: Union[spacy.vocab.Vocab, bool] = True, disable: Union[str, Iterable[str]] = [], enable: Union[str, Iterable[str]] = [], exclude: Union[str, Iterable[str]] = [], meta: Dict[str, Any] = {}, auto_fill: bool = True, validate: bool = True) -> 'Language'
Language.initialize(self, get_examples: Optional[Callable[[], Iterable[spacy.training.example.Example]]] = None, *, sgd: Optional[thinc.optimizers.Optimizer] = None) -> thinc.optimizers.Optimizer
```

## Assembly rules

- `nlp.add_pipe` accepts the string name of a registered factory, not a callable component.
- Exactly one of `before`, `after`, `first`, or `last` should be set. If none is set, spaCy inserts the component last.
- `before` and `after` can be either a component name or a numeric index.
- `name=` changes the pipeline instance name only. The factory name stays the same.
- If `source=` is provided, the first positional argument is treated as a source pipeline component name, not a factory name.
- `create_pipe` creates a component without adding it; it is mostly an internal helper.

## Pipeline state and ordering

- `nlp.pipeline` is the active ordered list of `(name, component)` pairs.
- `nlp.components` includes disabled components too.
- `nlp.pipe_names` shows only active component names.
- `nlp.component_names` shows active and disabled component names.
- `nlp.pipe_factories` maps each component instance name to its registered factory name.

## Source components vs factories

Use a factory when you are creating a new component from code or config. Use `source` when you are copying an already-trained component from another pipeline.

```python
import spacy

source = spacy.blank("en")
source.add_pipe("sentencizer", name="sentences")

target = spacy.blank("en")
target.add_pipe("sentences", source=source, name="copied_sentences")
print(target.pipe_names)
print(target.get_pipe_meta("copied_sentences").factory)
```

In config files, the same distinction applies:

- `factory` means create the component from the registered factory.
- `source` means copy the component from a loadable model or pipeline.
- If neither key is present, `Language.from_config` raises the invalid-component-config error.

## Config-driven assembly

`Language.from_config` builds the `Language` object, creates the tokenizer, then adds pipeline components in config order.

```python
from spacy.lang.en import English

config = {
    "nlp": {"lang": "en", "pipeline": ["sentences"]},
    "components": {
        "sentences": {"factory": "sentencizer"},
    },
}

nlp = English.from_config(config)
print(nlp.pipe_names)
print(nlp.get_pipe_config("sentences"))
```

Use `disable`, `enable`, and `exclude` to control what is loaded and what runs:

- `disable` loads the component but keeps it out of the active pipeline.
- `enable` keeps only the listed pipes active.
- `exclude` prevents the component from being loaded at all.

Use `select_pipes` when the change is temporary. `disable_pipes` is the deprecated alias.

```python
with nlp.select_pipes(disable=["tagger", "parser"]):
    # temporary inference or inspection block
    pass
```

## `nlp.pipe` batching and component kwargs

`nlp.pipe` runs the current active pipeline over a stream of texts or docs.

- `batch_size` defaults to `nlp.batch_size`.
- `component_cfg` passes per-component keyword arguments during processing.
- `as_tuples=True` preserves caller context alongside each `Doc`.
- `n_process=-1` maps to the CPU count; multi-process behavior and GPU caveats are not tuned here and should be handed off to `install-and-inspect`.

```python
for doc in nlp.pipe(texts, batch_size=32, component_cfg={"tagger": {}}):
    print(doc.text)
```

## Pipe analysis

`nlp.analyze_pipes` is a static check. It does not execute the pipeline.

- `summary` lists each component and its declared metadata.
- `problems` lists unmet requirements for each component.
- `attrs` shows which components assign and require each attribute.
- `pretty=True` prints a table and warning summary.

A missing producer usually means the pipeline order is wrong or the declared metadata is incomplete.

```python
import spacy

nlp = spacy.blank("en")
nlp.add_pipe("tagger")
nlp.add_pipe("entity_linker")
analysis = nlp.analyze_pipes(pretty=True)
print(analysis["problems"]["entity_linker"])
```

For `entity_linker`, the common missing prerequisites are `doc.ents`, `doc.sents`, `token.ent_iob`, and `token.ent_type`. Put the producer components earlier in the pipeline, or temporarily disable the consumer while debugging.

## Inspection helpers

- Use `nlp.get_pipe_meta(name)` to inspect the registered metadata for a component instance.
- Use `nlp.get_pipe_config(name)` to inspect the resolved config actually stored for that component.
- Use `Language.has_factory(name)` before calling `add_pipe` if you need a quick availability check.

## Handoff to other sub-skills

- For custom registration and registry lookup details, read `component-factories-and-registry.md`.
- For the built-in factory catalog, read `built-in-components.md`.
- For common failure symptoms and recoveries, read `troubleshooting.md`.
