# Runtime Setup Workflows

## Choose the smallest install

Use Python `>=3.12`. Prefer `python -m pip ...` so the command targets the
intended interpreter.

```bash
python -m pip install --upgrade pip
python -m pip install "giskard"
```

Base `giskard` installs the default evaluation stack (`giskard.checks` plus its
agent, LLM, and core dependencies). Add only the extras needed by the task:

| Need | Minimal install |
| --- | --- |
| Deterministic scenarios, suites, built-in checks, mocked checks/generators | `python -m pip install "giskard"` |
| Vulnerability scan or RAG/quality scan APIs | `python -m pip install "giskard[scan]"` |
| OpenAI-backed judges, generators, providers, embeddings, or responses | `python -m pip install "giskard[openai]"` |
| Google/Gemini-backed providers | `python -m pip install "giskard[google]"` |
| Anthropic-backed providers | `python -m pip install "giskard[anthropic]"` |
| Azure OpenAI / Azure AI Foundry providers | `python -m pip install "giskard[azure]"` |
| LiteLLM-backed agent generator | `python -m pip install "giskard[litellm]"` |
| Rego-policy checks | `python -m pip install "giskard[regorus]"` |
| Garak or DeepTeam scanner bridge | `python -m pip install "giskard[garak]"` or `python -m pip install "giskard[deepteam]"` |
| All native provider SDKs without scan/check extras | `python -m pip install "giskard[all-llms]"` |
| All optional check dependencies | `python -m pip install "giskard[all-checks]"` |
| Everything for broad local exploration | `python -m pip install "giskard[full]"` |

Extras can be combined, for example:

```bash
python -m pip install "giskard[scan,openai]"
```

Avoid `full` by default: it pulls broad provider, optional-check, scan, and
LiteLLM dependencies. For scan workflows that will use OpenAI-backed generation,
`giskard[scan,openai]` is usually enough; for deterministic checks, base
`giskard` is enough.

## Provider environment variables

Provider extras install SDKs; credentials are still supplied separately. Common
variables used by Giskard providers are:

| Provider prefix | Common credential/config variables |
| --- | --- |
| `openai/` and bare OpenAI-default model names | `OPENAI_API_KEY` |
| `google/` or `gemini/` | `GOOGLE_API_KEY` or `GEMINI_API_KEY` |
| `anthropic/` | `ANTHROPIC_API_KEY` |
| `azure/` | `AZURE_API_KEY`, `AZURE_API_BASE`, optional `AZURE_API_VERSION` |
| `azure_ai/` | `AZURE_AI_API_KEY`, `AZURE_AI_ENDPOINT`, optional `AZURE_AI_API_VERSION` |

Provider call configuration belongs in [llm-providers](../../llm-providers/SKILL.md).
This setup sub-skill only decides which extra and credential variables are
needed before those workflows run.

## Privacy-first import smoke

Set telemetry opt-out variables before the first `giskard.*` import. This smoke
check imports installed packages only, makes no network calls, and reports
optional modules as missing instead of failing the whole run.

```bash
DO_NOT_TRACK=1 GISKARD_TELEMETRY_DISABLED=1 python - <<'PY'
import importlib
import sys

if sys.version_info < (3, 12):
    raise SystemExit(f"Python >=3.12 required, got {sys.version.split()[0]}")

core = importlib.import_module("giskard.core")
core.disable_telemetry()
print("giskard-core", core.get_lib_version("giskard-core"))
print("known libs", core.GISKARD_LIBS_VERSIONS)

required = ["giskard.core", "giskard.llm", "giskard.agents", "giskard.checks"]
optional = ["giskard.scan"]
for module in required + optional:
    try:
        imported = importlib.import_module(module)
    except ModuleNotFoundError as exc:
        status = "optional-missing" if module in optional else "missing"
        print(f"{module}: {status}: {exc.name}")
        if module in required:
            raise
    else:
        version = getattr(imported, "__version__", "unknown")
        print(f"{module}: ok ({version})")
PY
```

If the integrated root skill provides `../../scripts/check_giskard_imports.py`,
it should perform the same style of no-network, telemetry-disabled installed
package check. This sub-skill does not create that root-owned helper.

## Disable telemetry in code

Put environment opt-out at the top of the process, before importing any
`giskard.*` module:

```python
import os

os.environ.setdefault("DO_NOT_TRACK", "1")
os.environ.setdefault("GISKARD_TELEMETRY_DISABLED", "1")

from giskard.core import disable_telemetry

disable_telemetry()
```

If Giskard has already been imported, call `disable_telemetry()` immediately to
stop further sends in that process, then restart with env-var opt-out when the
user needs to avoid first-import side effects.

## Inspect versions and import namespaces

Use `get_lib_version` for one distribution and `GISKARD_LIBS_VERSIONS` for the
known split libraries:

```python
from giskard.core import GISKARD_LIBS_VERSIONS, get_lib_version

print(get_lib_version("giskard"))
print(get_lib_version("giskard-scan", default="not installed"))
for distribution, version in sorted(GISKARD_LIBS_VERSIONS.items()):
    print(distribution, version)
```

Use dotted imports:

```python
from giskard.checks import Scenario, Suite
from giskard.llm import LLMClient
from giskard.agents import Generator
from giskard.scan import KnowledgeBase, quality_scan, vulnerability_scan
```

Do not use underscore imports such as `giskard_checks`, and do not assume v2
objects are available at top-level `giskard`.

## Use a shared rate limiter

`MinIntervalRateLimiter` is an async context manager. Reuse a stable id only for
call paths that should share throttling state.

```python
import asyncio
from giskard.core import MinIntervalRateLimiter

limiter = MinIntervalRateLimiter.from_rpm(
    rpm=60,
    max_concurrent=3,
    id="provider-openai-shared",
)

async def guarded_call(name: str) -> None:
    async with limiter.throttle() as waited:
        print(f"{name}: waited {waited:.3f}s before starting")
        # Make the actual API or workflow call here.

async def main() -> None:
    await asyncio.gather(*(guarded_call(str(i)) for i in range(3)))

asyncio.run(main())
```

Agent workflow generators can receive a rate limiter; route those examples to
[agents-workflows](../../agents-workflows/SKILL.md).

## Define a small discriminated union

Use this pattern when a Giskard-compatible config needs to serialize and recover
concrete subclasses by `kind`:

```python
from giskard.core import Discriminated, discriminated_base

@discriminated_base
class ExportFormat(Discriminated):
    pass

@ExportFormat.register("json")
class JsonFormat(ExportFormat):
    indent: int = 2

obj = ExportFormat.model_validate({"kind": "json", "indent": 4})
assert isinstance(obj, JsonFormat)
assert obj.kind == "json"
print(obj.model_dump())
```

For custom eval checks that also use discriminated registration, route to
[checks-evals](../../checks-evals/SKILL.md).

## Use serializable errors

`Error` is a small Pydantic model for returning consistent error payloads from
helpers or workflow wrappers:

```python
from giskard.core import Error

err = Error(message="provider SDK is not installed")
print(str(err))
print(err.model_dump())
```

Keep user prompts, model outputs, credentials, and local paths out of error
messages if they may be logged or reported.
