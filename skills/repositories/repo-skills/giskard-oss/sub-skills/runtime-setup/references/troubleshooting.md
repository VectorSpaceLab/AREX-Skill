# Runtime Setup Troubleshooting

## Quick diagnosis order

1. Confirm Python is `>=3.12`.
2. Set `DO_NOT_TRACK=1` and `GISKARD_TELEMETRY_DISABLED=1` before smoke imports
   when telemetry is a concern.
3. Import dotted v3 namespaces (`giskard.core`, `giskard.checks`,
   `giskard.llm`, `giskard.agents`, optional `giskard.scan`).
4. Check whether the selected optional extra is installed.
5. If working near an editable checkout, repeat the smoke from a neutral working
   directory to prove the installed package, not local files, is being imported.

## Legacy `giskard` package conflict

Symptom:

```text
ImportError: Package conflict detected: The legacy package 'giskard' is installed
and conflicts with the new namespace structure provided by 'giskard-core'.
```

Meaning: a monolithic legacy top-level `giskard` package is shadowing the v3
namespace layout. The v3 packages expect `giskard` to behave as a namespace
containing split subpackages, not as a single legacy module.

Diagnose without importing `giskard.core`:

```bash
python - <<'PY'
import importlib.util
spec = importlib.util.find_spec("giskard")
print("spec:", spec)
print("has_location:", getattr(spec, "has_location", None))
print("origin:", getattr(spec, "origin", None))
print("submodule_search_locations:", getattr(spec, "submodule_search_locations", None))
PY
```

Fix options:

- Use a fresh Python `>=3.12` environment for Giskard v3.
- Or remove the conflicting install and reinstall the needed v3 extras:

```bash
python -m pip uninstall giskard
python -m pip install "giskard"
# Add extras only if needed, for example:
python -m pip install "giskard[scan,openai]"
```

Do not keep legacy v2 top-level APIs and v3 split packages in one environment
unless the user explicitly accepts the risk and knows which import surface each
workflow uses.

## Wrong import names such as `giskard_checks`

Symptom:

```text
ModuleNotFoundError: No module named 'giskard_checks'
```

Fix: import from the shared namespace, not distribution-style names:

```python
from giskard.checks import Scenario, Suite
from giskard.core import MinIntervalRateLimiter
from giskard.llm import LLMClient
from giskard.agents import Generator
# Requires the scan extra:
from giskard.scan import vulnerability_scan
```

Distribution names use hyphens (`giskard-checks`) and install names use extras
(`giskard[scan]`), but Python imports use dots (`giskard.checks`).

## Python version is too old

Symptoms:

- `pip` refuses to install because `Requires-Python >=3.12` is not satisfied.
- Syntax errors appear in package code on Python 3.11 or older.

Diagnose:

```bash
python - <<'PY'
import sys
print(sys.version)
raise SystemExit(0 if sys.version_info >= (3, 12) else 1)
PY
```

Fix: create or select a Python 3.12+ environment, then reinstall the smallest
needed Giskard extras with that interpreter, for example:

```bash
python3.12 -m pip install "giskard[scan,openai]"
```

## Missing optional extra

Symptoms and fixes:

| Symptom | Likely cause | Minimal fix |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'giskard.scan'` | Scan package was not installed. | `python -m pip install "giskard[scan]"` |
| Provider unavailable or provider SDK import error | Provider SDK extra is missing. | Install one of `giskard[openai]`, `giskard[google]`, `giskard[anthropic]`, or `giskard[azure]`. |
| OpenAI, Google, Anthropic, or Azure auth error | SDK is installed but credential/config env vars are missing or invalid. | Set the provider variables listed in [workflows](workflows.md#provider-environment-variables). |
| Rego policy check cannot run | Optional `regorus` dependency is missing or unsupported on the platform. | `python -m pip install "giskard[regorus]"`, or choose a deterministic check that does not require Rego. |
| Garak or DeepTeam scan bridge is unavailable | Heavy optional scanner extra is missing. | Install `giskard[garak]` or `giskard[deepteam]` only for that bridge. |
| Anthropic embeddings fail | Anthropic provider supports completions but not embeddings. | Choose an embedding-capable provider such as OpenAI, Google, Azure, or Azure AI. |

Do not install `giskard[full]` as the first response unless the user really
needs all provider SDKs, optional checks, scan, and LiteLLM support.

## Telemetry concerns

Giskard core supports env-var opt-out and runtime disabling. For privacy-first
runs, set both full-disable variables before the first Giskard import:

```bash
export DO_NOT_TRACK=1
export GISKARD_TELEMETRY_DISABLED=1
python your_script.py
```

Inside Python:

```python
import os
os.environ.setdefault("DO_NOT_TRACK", "1")
os.environ.setdefault("GISKARD_TELEMETRY_DISABLED", "1")

from giskard.core import disable_telemetry

disable_telemetry()
```

If Giskard was already imported before opt-out variables were set,
`disable_telemetry()` stops further sends for the current process. Restart with
env-var opt-out before import when the user wants to avoid first-import side
effects such as creating a local anonymous identifier.

Telemetry payloads should never include prompts, model outputs, secrets, user
content, or local file paths. If adding telemetry tags or events in user code,
only use non-sensitive dimensions.

## Source checkout versus installed package confusion

Symptoms:

- Imports work only when the current directory is a repository checkout.
- A local editable checkout shadows the package the user thinks is installed.
- Version output does not match the package selected by `pip`.

Diagnose from a neutral directory with telemetry disabled:

```bash
TMPDIR=$(mktemp -d)
cd "$TMPDIR"
DO_NOT_TRACK=1 GISKARD_TELEMETRY_DISABLED=1 python - <<'PY'
from giskard.core import GISKARD_LIBS_VERSIONS, get_lib_version, disable_telemetry

disable_telemetry()
print("giskard", get_lib_version("giskard"))
print(GISKARD_LIBS_VERSIONS)
import giskard.core, giskard.llm, giskard.agents, giskard.checks
print("required imports ok")
try:
    import giskard.scan
except ModuleNotFoundError:
    print("giskard.scan missing: install giskard[scan] if scan workflows are needed")
else:
    print("giskard.scan ok")
PY
```

Fix: run package-use workflows against an installed environment, not against
local files that happen to be importable. If intentionally developing from an
editable checkout, keep that separate from end-user smoke checks and report both
the distribution versions and the import namespaces being exercised.

## Top-level v2 API confusion

Symptoms:

- `AttributeError` for `giskard.Model`, `giskard.Dataset`, or top-level
  `giskard.scan` behavior expected from older examples.
- Code imports plain `import giskard` and expects all features to hang off that
  object.

Fix: use v3 subpackages for v3 workflows:

- `giskard.checks` for scenarios, suites, checks, judges, and generators.
- `giskard.scan` for vulnerability and quality scans.
- `giskard.llm` for provider routing.
- `giskard.agents` for workflow orchestration.
- `giskard.core` for shared runtime utilities.

If the user must run legacy v2 tabular/ML scan APIs, use a separate environment
and do not treat that as part of this v3 split-package runtime setup.
