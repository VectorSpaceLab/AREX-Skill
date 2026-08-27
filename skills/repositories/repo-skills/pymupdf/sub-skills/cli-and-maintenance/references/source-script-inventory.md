# Source Script Inventory

| Source item | Classification | Runtime decision |
| --- | --- | --- |
| `src/__main__.py` | Wrapped behavior | The installed CLI is exercised by bundled `scripts/pymupdf_cli_smoke.py`; source dispatcher is not copied. |
| `scripts/test.py` | Reference-only / excluded | Developer build/test orchestrator that creates/mutates environments and runs broad tests. |
| `scripts/autovenv.py` | Excluded | Internal automatic venv/re-exec helper. |
| `scripts/sysinstall.py` | Excluded | Sudo/system package and system MuPDF install helper. |
| `scripts/gh_release.py` | Excluded/reference-only | Release/cibuildwheel automation with Docker/network/build-output implications. |

Use the bundled CLI smoke for safe runtime verification. Use maintainer scripts only in an explicitly authorized checkout-maintenance workflow.
