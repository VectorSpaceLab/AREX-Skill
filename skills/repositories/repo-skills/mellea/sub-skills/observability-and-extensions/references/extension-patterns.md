# Extension patterns and contribution-safe integration

This reference targets Mellea 0.8.0.dev0. Prefer the narrowest public protocol
that solves the problem, keep optional integrations optional, and make every
extension testable without a model or exporter.

## Choose the extension layer

| Requirement | Extension point | Boundary |
| --- | --- | --- |
| Domain-specific prompt plus typed parsing | `Component[S]` | No registry; pass the instance directly to an owning Mellea workflow. |
| Request/result policy or observation | standalone `@hook` | Requires `mellea[hooks]` only when activated. |
| Several lifecycle hooks with shared state | named `Plugin` subclass | Register in application setup, not package import. |
| Reusable hook bundle | `PluginSet` | Composition and priority container; still process-global while active. |
| Custom application metric | public telemetry instrument factory | Returns no-op when metrics are disabled. Application owns dimensions. |
| New provider | `Backend` subclass | Implement underscore methods; public final wrappers own hook firing. |
| New verifier or sampling algorithm | `Requirement` or `SamplingStrategy` | Route the algorithmic workflow to `generative-programming`; instrument it through lifecycle hooks. |
| Model-specific rendering | `TemplateRepresentation` plus package resources | Ship templates in the extension wheel and test lookup after installation. |

Do not add a class merely to wrap a primitive. Do not create a global component
registry: `Component` is a runtime-checkable protocol and direct composition is
the intended mechanism.

## Custom component contract

A reusable component implements `parts()`, `format_for_llm()`, and `_parse()`.
The inherited public `parse()` wraps any `_parse()` failure in
`ComponentParseError`; do not override it merely to bypass that contract.

```python
from mellea.core import CBlock, Component, ModelOutputThunk, Span


class TaggedAnswer(Component[str]):
    """Request and parse an answer enclosed in a stable tag."""

    def __init__(self, prompt: str, tag: str = "answer") -> None:
        """Store the prompt and output tag."""
        self.prompt = prompt
        self.tag = tag

    def parts(self) -> list[Span]:
        """Return constituent content used by dependency walks."""
        return [CBlock(self.prompt)]

    def format_for_llm(self) -> str:
        """Render the prompt as plain text for a formatter."""
        return f"{self.prompt}\nRespond inside <{self.tag}></{self.tag}>."

    def _parse(self, computed: ModelOutputThunk) -> str:
        """Extract the tagged value or raise on an invalid contract."""
        text = computed.value or ""
        opening = f"<{self.tag}>"
        closing = f"</{self.tag}>"
        start = text.find(opening)
        end = text.find(closing, start + len(opening))
        if start < 0 or end < 0:
            raise ValueError(f"missing {opening}...{closing}")
        return text[start + len(opening) : end].strip()
```

Use the precise generic output type: `Component[str]`,
`Component[list[str]]`, `Component[dict[str, object]]`, and so on. The return
annotation on `_parse()` must agree. Keep `_parse()` deterministic and free of
network, file, model, registry, and telemetry side effects.

Unit-test a component without a backend:

```python
from mellea.core import CBlock, ComponentParseError, ModelOutputThunk

component = TaggedAnswer("State the result")
assert component.format_for_llm().endswith("<answer></answer>.")
assert isinstance(component.parts()[0], CBlock)
assert component.parse(ModelOutputThunk(value="<answer>42</answer>")) == "42"

try:
    component.parse(ModelOutputThunk(value="untagged"))
except ComponentParseError:
    pass
else:
    raise AssertionError("parse() must normalize parser failures")
```

Route actual use of the component in `act`, `aact`, requirements, or sampling
through `generative-programming`.

## Template-backed components

Return `TemplateRepresentation` when model-specific Jinja rendering is needed:

```python
from mellea.core import TemplateRepresentation


def format_for_llm(self) -> TemplateRepresentation:
    return TemplateRepresentation(
        obj=self,
        args={"prompt": self.prompt, "tag": self.tag},
        template_order=["*"],
    )
```

`"*"` resolves from the component class name. Use an inline `template=` for a
small self-contained template or ship package-owned templates under the
extension's prompt-template resource tree. Keep `args` serializable, keep names
aligned with template variables, and test exact rendering plus missing-template
behavior from an installed-wheel-like layout. Editable-checkout success alone
is not packaging proof.

No component registration is needed. A formatter discovers resources from the
component's package and can fall back to Mellea defaults.

## Focused plugin extension

Use a standalone hook for one lifecycle action. Use a named `Plugin` subclass
when hooks share state or correlation. Keep signal imports local so importing
the extension does not import optional providers or create cycles.

```python
from typing import TYPE_CHECKING, Any

from mellea.plugins import HookType, Plugin, PluginMode, hook

if TYPE_CHECKING:
    from mellea.plugins.hooks.generation import GenerationPostCallPayload


class CompletionCounter(Plugin, name="acme-completion-counter", priority=80):
    """Count completed generations through an application-owned metric."""

    @hook(HookType.GENERATION_POST_CALL, mode=PluginMode.FIRE_AND_FORGET)
    async def on_complete(
        self, payload: "GenerationPostCallPayload", context: Any
    ) -> None:
        """Record one completed generation without blocking the caller."""
        from mellea.telemetry import create_counter

        counter = create_counter(
            "acme.generations", description="Completed generations", unit="{generation}"
        )
        generation = payload.model_output.generation
        counter.add(
            1,
            {
                "provider": generation.provider or "unknown",
                "model": generation.model or "unknown",
            },
        )
```

For a high-volume plugin, cache its instrument after telemetry configuration
rather than recreating it on every hook. Do that lazily in activation/setup,
not at module import. Keep labels bounded and register the plugin from
application setup or a scope. A reusable library must not call `register()` as
an import side effect.

For spans, use a stateful plugin with a pre/start and post/error/end pair. Store
only the correlation id to span mapping needed for closure, handle duplicate or
missing ids defensively, and close all in-flight spans during plugin shutdown.
A completion-only hook is a metric boundary, not a span boundary.

## Custom backend contract

Subclass `mellea.core.Backend`, set `_model_id` and `_provider`, and implement:

- `_generate_from_context(...)` for one context-aware action;
- `_generate_from_raw(...)` for raw batch generation.

Do not override the public `generate_from_context()` or `generate_from_raw()`
wrappers: they are final lifecycle owners for generation hooks. A
context-generation implementation should normally return an uncomputed
`ModelOutputThunk` whose asynchronous completion runs backend post-processing;
an already-computed thunk can bypass `generation_post_call` and break paired
tracing/metrics.

At the provider normalization boundary:

```text
mot.generation.model       = requested model id
mot.generation.provider    = stable provider id
mot.generation.usage       = None, or an OpenAI-shaped usage mapping
mot.generation.response_*  = provider response facts when available
```

When usage exists, require `prompt_tokens`, `completion_tokens`, and
`total_tokens`; preserve optional cache/reasoning details. Let thunk streaming
logic set `streaming` and `ttfb_ms`. Do not manually call built-in token,
latency, or error metric helpers from the backend: the completion/error hooks
already feed those plugins.

Test a backend first with a fake provider response and no credentials:

- normal uncomputed completion fires pre and post with the same generation id;
- dispatch failure and materialization failure each reach the correct error
  boundary;
- missing usage remains `None` without fabricated counts;
- complete usage, model, provider, response id/model, and finish reason survive
  post-processing;
- streaming sets TTFB only after a first chunk and closes on cancellation;
- raw batch reports defensible aggregate and per-output usage.

## Requirements and sampling strategies

A deterministic `Requirement` supplies a typed validation function returning a
`ValidationResult` with a bounded reason. Omitting the function invokes
LLM-as-judge behavior. A custom `SamplingStrategy` implements its typed async
`sample` contract and returns a `SamplingResult` whose generations, actions,
contexts, and validation arrays stay index-aligned.

These are generative-algorithm extensions, so use `generative-programming` for
implementation details. Their observability contract remains here: fire or
preserve validation/sampling lifecycle hooks rather than calling tracing or
metrics from the algorithm body.

## Ownership and packaging

Choose one contribution path deliberately:

| Path | Suitable when | Expectations |
| --- | --- | --- |
| Core Mellea | General capability belongs in an existing abstraction and benefits most users | Discuss placement first; preserve public API, hook, telemetry, typing, and optional-dependency contracts. |
| Independent `mellea-*` package | Domain/application behavior has its own release cycle | Depend on a supported Mellea range, ship templates/resources, and import only public APIs. |
| Community contribution package | Specialized or experimental behavior needs broader reuse but is not core-ready | Keep experimental status visible and plan a migration path before promotion. |

Optional packages such as `cpex`, OpenTelemetry, LiteLLM, provider SDKs, and
model runtimes belong in optional dependency groups. Importing the extension's
base module must not require them. Raise a friendly install message only when
the optional capability is used.

Avoid public import cycles:

```text
core protocols -> no optional integration imports
plugin definitions -> TYPE_CHECKING payload imports
hook body/setup -> lazy telemetry/provider imports
application entry point -> registration and exporter configuration
```

Do not import an application module from telemetry or a core protocol from an
integration via a re-export loop. Add a clean-subprocess import test with all
signals and sinks disabled.

## Contribution-safe checks

Use `uv` for Python commands and project tools. Before contribution:

```bash
uv run ruff format .
uv run ruff check .
uv run mypy .
uv run pytest -m "not qualitative"
```

Narrower unit checks are appropriate during development, but a final change
must include the project-required fast suite. Mark tests by actual granularity:
unit tests are self-contained; integration tests need multi-component wiring;
e2e tests need a real service/provider; qualitative tests inspect model output;
slow tests take more than one minute. Do not mark a trivial deterministic test
qualitative.

For plugin/telemetry work, add deterministic cases for:

- optional dependencies absent and signals disabled;
- mode-phase order, priority, writable-policy acceptance/rejection, and block
  semantics;
- scoped deregistration, manager shutdown, and background-task draining;
- paired span success/error/cancellation closure and correlation-id collision;
- no-op metric factories and in-memory recording with bounded labels;
- generation metadata with complete and unavailable usage;
- Python 3.11-compatible behavior without requiring nested span shape;
- import with no network, webhook, exporter, file, credential, or model access.

All core functions require types and concise Google-style docstrings. Docstrings
are consumed as prompts: use Markdown code fences, single-backtick inline code,
and plain `Args:`, `Returns:`, and `Raises:` sections rather than RST directives
or doctest prompts. If library code adds a `raise` path or promotes a symbol
through `__all__`, run the project's generated-API documentation quality gate
and ensure every public return/exception contract is exact.

## API-drift guard

Before supporting a Mellea version outside 0.8.0.dev0, inspect public signatures
and enum/dataclass fields in the installed package. In particular re-check:

- `HookType`, `PluginMode`, mode ordering, and writable policies;
- registration and session plugin semantics;
- hook payload fields and lifecycle correlation ids;
- `GenerationMetadata` and `ModelOutputThunk` completion behavior;
- `Component`/`TemplateRepresentation` fields and parser wrapping;
- telemetry flags, signal initialization timing, and exporter protocols.

Feature-detect public attributes where compatibility is required. Do not copy a
private registry/provider reset recipe into production extension code.
