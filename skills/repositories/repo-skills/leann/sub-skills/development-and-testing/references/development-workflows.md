# Development Workflows

## Safe checkout setup

Run development commands from the repository root unless a command explicitly
uses `--repo-root` or another path. Do not use this workflow for a normal
published-package install.

1. Confirm the interpreter and manager:

   ```bash
   python --version
   uv --version
   git status --short --branch
   git submodule status
   ```

   LEANN requires Python 3.10+. A leading `-` in `git submodule status` means the
   submodule is recorded but not initialized; a leading `+` means its checkout
   differs from the recorded commit.

2. Initialize the checkout's pinned submodules before a native build:

   ```bash
   git submodule update --init --recursive
   ```

   This checks out recorded commits; it does not update submodules to arbitrary
   upstream heads. If only HNSW is in scope, its Faiss, msgpack-c, and cppzmq
   submodules are the minimum source set, but a normal contributor setup uses
   the recursive command to avoid partial-checkout surprises.

3. Install the host prerequisites summarized in
   [architecture and packages](architecture-and-packages.md), then create the
   `uv` environment:

   ```bash
   uv sync
   uv sync --group lint
   uv sync --group test
   ```

   `uv sync` can compile native packages and download dependencies. Review the
   lockfile and requested groups before running it in a restricted or expensive
   environment. The `lint` group is intentionally small. The `test` group adds
   pytest tooling but does not make every app, service, model, GPU, or native
   backend available.

4. Verify environment identity before testing:

   ```bash
   uv run python -c "import sys; print(sys.executable); print(sys.version)"
   uv run python -m pip check
   uv run python -c "import leann; print(leann.__file__)"
   ```

## Change scoping

Before editing, map each changed file to an owner:

| Changed area | Primary impact | Add-on impact to inspect |
|---|---|---|
| `packages/leann-core/src/leann/api.py` or public exports | Public API and all backends | CLI, README imports, index compatibility, backend-specific build/search tests |
| `cli.py`, `sync.py`, watch/rebuild code | CLI parser and file/index state | incremental HNSW/IVF behavior, registry, daemon/watch tests |
| embedding/chat/settings/provider modules | Model/provider behavior | optional credentials, live-service markers, token/batch limits |
| HNSW CMake/native/Python wrapper | HNSW wheel and binding | core exact version pin, ZeroMQ, BLAS/LAPACK, OpenMP, platform wheel repair |
| DiskANN CMake/native/Python wrapper | DiskANN wheel and binding | submodule, Protobuf/math libraries, memory/resource-heavy tests |
| IVF package | `faiss-cpu` IVF behavior | incremental add/remove, direct map, optional HNSW query server |
| FlashLib packages | CUDA backend | CUDA torch/FlashLib compatibility; no CPU substitute |
| `apps/` or MCP integrations | App-specific imports/protocol | optional data-source SDKs, credentials, live services |
| package metadata or lockfile | Resolver/install/release behavior | CPU-only metadata tests, all internal constraints, clean-wheel install |
| docs/roadmap/changelog | Contributor/user contract | link check, examples, current behavior and dates |

Use [testing-guide.md](testing-guide.md) to select the minimum useful evidence.

## Lint and pre-commit

Start with checks that do not intentionally edit files:

```bash
uv run ruff format --check .
uv run ruff check .
```

The continuous-integration lint job runs the pinned lint environment and the
full pre-commit configuration:

```bash
uv run --frozen --only-group lint pre-commit run --all-files --show-diff-on-failure
```

Pre-commit includes whitespace/end-of-file fixers and Ruff with `--fix`, so it
may modify files before returning nonzero. Run it only when a working-tree diff
is acceptable, then inspect `git diff`. To apply formatting or safe lint fixes
intentionally:

```bash
uv run ruff format .
uv run ruff check --fix .
git diff --check
git diff
```

Do not hide generated changes with a broad `git add .`. Stage only reviewed
files when the user has authorized a commit.

## Focused test loop

A maintainable loop is:

1. metadata/parser/unit tests that cover the changed branch;
2. one public-import or CLI smoke when public surfaces changed;
3. one native backend case for every changed native backend that is prepared;
4. optional app/service/GPU cases only when their dependencies and runtime are
   intentionally available;
5. broader non-live suite after focused cases pass.

Commands and caveats are in [testing-guide.md](testing-guide.md). Do not run an
all-test command merely because it is shorter: unmarked model tests and app
imports may be expensive or unavailable locally.

## Contributor documentation contract

### Public changelog

`docs/CHANGELOG.md` is append-only and currently places newest entries at the
bottom. Add an entry for a feature, breaking change, or important fix, using:

```text
## YYYY-MM-DD: short summary

- What changed, including the affected package/backend/API.
- Why it changed and any migration or compatibility consequence.
- Relevant measured result with its baseline and workload, when applicable.
```

Do not add a changelog entry for formatting-only or invisible maintenance unless
it changes contributor or release behavior.

### Roadmap and vision

The public roadmap tracks completed work and P0/P1 priorities and is intended to
stay synchronized with GitHub issue 237. The long-term vision is the north star,
not a record of completed implementation. When a feature moves state:

- update roadmap completion/priority accurately;
- preserve unresolved items rather than declaring aspirational behavior shipped;
- change the long-term vision only when product direction changes, not for every
  implementation detail.

### Self-contained development notes

Private development notes under `docs/dev/` remain repository policy even when
the directory is absent or gitignored:

- `TODO.md`: incomplete/in-progress/next steps only; remove completed items;
- `PROGRESS.md`: completed work only, with reproducible script/log/config paths;
- `STATES.md`: current useful state, deleting stale entries; top glossary defines
  backends, index files, chunking strategies, and embedding models;
- `EXPERIMENTS.md`: benchmarks, A/B comparisons, parameter sweeps, recall,
  latency, and storage results.

`TODO.md` and `PROGRESS.md` are chronological and append-only. Every note must
stand alone: expand abbreviations on first use, explain techniques, include the
causal chain, and give numbers a baseline, workload, configuration, and metric.
“Fixed the bug” or “improved quality” is not sufficient.

### User-facing docs

Update affected API/CLI examples and package requirements in the same change.
The active root pytest configuration and current CI workflow outrank stale prose.
For example, tests live under `tests/`, the configured timeout is 300 seconds,
and the active Python floor is 3.10 even though older contributor/test text says
otherwise.

## Commit policy

Use Conventional Commits after a complete tested feature or before an unavoidable
destructive transition, and only with explicit commit authorization. Common
prefixes are `feat:`, `fix:`, `docs:`, `test:`, `refactor:`, and `perf:`. A
release metadata change commonly uses `chore:`.

Before a commit:

```bash
git status --short
git diff --check
git diff --staged
```

Do not commit partial failing work, unrelated files, generated build trees,
credentials, or local environments. Never push automatically.
