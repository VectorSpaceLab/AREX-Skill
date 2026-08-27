# Source Evidence Map

This reference records the evidence that informed the Vaex repo skill and the source-script decisions made during construction. It is public provenance for future refresh work, not a request for runtime agents to open the source checkout.

## Included evidence

| Evidence source | Why it matters | Skill use |
| --- | --- | --- |
| `README.md` | Public project purpose, install routes, core out-of-core DataFrame features | Root overview, install guidance, route signals |
| `setup.py`, `packages/*/setup.py`, `packages/vaex-core/pyproject.toml` | Distribution names, versions, dependencies, entry points, Python support, source-build hints | Package split, optional dependency notes, environment checks |
| `packages/vaex-core/vaex/` | Core DataFrame, expressions, IO dispatch, CLI dispatcher, settings, caching, file schemes | `dataframe-core`, `io-conversion`, `expressions-analytics`, `cli-settings`, root troubleshooting |
| `packages/vaex-core/src/` | Compiled extension sources for fast strings/hash/aggregation | Source-build and compiled-extension troubleshooting context |
| `packages/vaex-hdf5/vaex/hdf5/` | HDF5 readers/writers/openers | `io-conversion` format guidance |
| `packages/vaex-viz/vaex/viz/` | Matplotlib plotting accessors and visualization helpers | `visualization-jupyter` plotting references and smoke helper |
| `packages/vaex-ml/vaex/ml/` | Transformers, pipeline, sklearn wrappers, KMeans, optional model integrations | `ml-pipelines` workflows and API notes |
| `packages/vaex-server/vaex/server/` | FastAPI/Tornado server, REST routes, client/service code, settings | `serving-remote` server and REST guidance |
| `packages/vaex-jupyter/vaex/jupyter/` | Widget models/accessors and frontend integrations | `visualization-jupyter` Jupyter widget guidance |
| `packages/vaex-astro/vaex/astro/` | FITS/VOTable/TAP and astronomy/geospatial transformations | `io-conversion` optional astro/cloud guidance and expression cross-links |
| `packages/vaex-graphql/vaex/graphql/` | Optional GraphQL accessor and dependency constraints | `serving-remote` optional GraphQL notes |
| `docs/source/api.rst`, tutorials, and guides | Public task intent, examples, configuration and server docs | Workflow references across sub-skills |
| `docs/source/data/io/*` | Tiny documentation data fixtures | Inspired bundled IO smoke cases; not linked as runtime dependency |
| `tests/` | Behavior, edge cases, optional dependency boundaries, final native candidates | Native candidate map, troubleshooting, scripts, verification cases |
| `bin/`, `ci/`, `Makefile`, `dodo.py` | CLI/installer/build/test/benchmark automation | Source-script inventory and root build/troubleshooting notes |

## Excluded or de-prioritized evidence

| Path or surface | Reason |
| --- | --- |
| VCS and CI infrastructure | Useful only for install/test hints; not runtime operating guidance |
| `packages/vaex-core/vendor/` | Vendored C++ submodules/build dependencies; not user-facing except source-build troubleshooting |
| `benchmarks/` and benchmark scripts | Expensive maintainer workflows; excluded from ordinary runtime skill |
| `misc/`, release scripts, desktop packaging | Maintainer-only and platform-specific |
| `packages/vaex-ui/` and GUI entry points | PyQt/OpenGL desktop GUI is dependency-heavy and not selected for this user-facing operating graph |
| `packages/vaex-distributed/` | README-only placeholder in this checkout |
| Cloud/TAP/GraphQL/TensorFlow/Jupyter frontend services | Optional or environment/service-dependent; documented but not required for core verification |
| `skills/tests/` and production logs | Review/test artifacts and construction logs, not runtime skill evidence |

## Native candidate map summary

| Candidate family | Backend | Criticality | Skill owner | Verification expectation |
| --- | --- | --- | --- | --- |
| DataFrame constructors, evaluation, selections, virtual columns | CPU | required | `dataframe-core` | Focused safe pytest/native or bundled smoke |
| Expressions, groupby/binby, joins, strings/datetimes | CPU | required | `expressions-analytics` | Focused safe pytest/native or bundled smoke |
| HDF5/Arrow/Parquet/CSV export/open/conversion | CPU | required | `io-conversion` | Tiny roundtrip helper plus selected native IO tests |
| CLI help, settings YAML/schema, open/stat checks | CPU | required | `cli-settings` | Help/probe scripts and selected CLI/native checks |
| Vaex ML sklearn/Pipeline/PCA/KMeans | CPU | required for selected ML scope | `ml-pipelines` | Tiny ML smoke plus selected native ML tests |
| Matplotlib plotting and Jupyter model/accessor basics | CPU | required for plotting; frontend optional | `visualization-jupyter` | Agg plot smoke; widget frontend docs/tests optional |
| FastAPI REST/WebSocket server | CPU/service | required for selected server scope | `serving-remote` | Safe import/help/default smoke; route checks opt-in because app import can initialize example data/cache |
| TensorFlow, GraphQL, cloud/TAP/S3/GCS, GUI, benchmarks | CPU/network/service or optional deps | optional/excluded | nearest owner | Documented optional/skip conditions, not required gates |

## Source script inventory decisions

| Source artifact | Decision | Bundled replacement | Rationale |
| --- | --- | --- | --- |
| `bin/vaex` | Wrap | `sub-skills/cli-settings/scripts/vaex_cli_smoke.py` | Installed console entry point is authoritative; wrapper runs safe help/settings/open checks. |
| `packages/vaex-core/vaex/__main__.py` | Distill/wrap | `sub-skills/cli-settings/references/cli-reference.md` and CLI smoke helper | Command map and risk flags are preserved without depending on source files. |
| `packages/vaex-core/vaex/convert.py` | Adapt/wrap | `sub-skills/io-conversion/scripts/convert_csv_hdf5.py`, `io_roundtrip_smoke.py` | Provides safer local-only conversion/roundtrip helpers with explicit cleanup and validation. |
| `packages/vaex-core/vaex/settings.py` and configuration docs | Adapt/wrap | `sub-skills/cli-settings/scripts/vaex_settings_probe.py`, configuration reference | Read-only probe and explicit opt-in persistence avoid accidental user config mutation. |
| `packages/vaex-server/vaex/server/fastapi.py` | Wrap | `sub-skills/serving-remote/scripts/server_smoke.py` | Default helper avoids listeners and avoids app import unless explicitly requested; references describe TestClient route patterns. |
| `bin/webveax` | Reference-only/exclude | `sub-skills/serving-remote/references/troubleshooting.md` note | Legacy web script, browser/server side effects, overlaps modern server route. |
| `bin/get_vaex.sh` | Exclude | none | Legacy installer with network and host mutations. |
| `bin/install_pcre.sh` | Reference-only | root troubleshooting/source-build notes | Build dependency evidence only; future agents should use package managers deliberately. |
| `bin/build_binary_osx.sh`, `py2app.py`, release/packaging scripts | Exclude | none | Platform-specific maintainer packaging, not ordinary Vaex operation. |
| Benchmark scripts | Exclude/reference-only | CLI cautions | Expensive maintainer workflows. |
| Documentation notebooks/examples | Distill | sub-skill references and smoke scripts | Runtime skill provides self-contained recipes instead of requiring notebook access. |

## Backend plan

Required backend set is CPU only. Selected Vaex workflows are CPU-bound lazy DataFrame, IO, analytics, ML, visualization, CLI, and local service operations. CUDA/ROCm/MPS/vendor accelerators are not required by the selected Vaex repo evidence. Optional services/extras are documented but do not block the CPU skill.
