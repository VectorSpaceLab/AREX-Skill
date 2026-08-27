# Contributor Guidance

Use this reference when the user is editing ModelScope itself or wants a custom
extension to follow ModelScope's repository conventions. Keep contribution
checks focused and safe; do not run full model-zoo, GPU, network, upload, or
training jobs unless the user explicitly asks and has the required environment.

## Style and formatting

ModelScope's contributor documentation states that the repository follows PEP8
and uses these tools:

- `flake8` for linting.
- `yapf` for formatting.
- `isort` for import ordering.
- `pre-commit` hooks for flake8, yapf, seed-isort-config/isort, trailing
  whitespace, end-of-file fixes, requirement sorting, quote fixes, merge
  conflict checks, encoding pragma removal, and line ending normalization.

Inspected repository style settings include:

- yapf style based on PEP8.
- isort line length 79, first-party package `modelscope`, and third-party hints
  for `json`/`yaml`.
- flake8 max line length 120 with selected B/C/E/F/P/T4/W/B9 codes and several
  repository-specific ignores/excludes.

Safe commands for a ModelScope checkout:

```bash
pre-commit run --all-files
make linter
```

Both can modify or scan many files. Prefer focused pre-commit paths during
iteration, for example:

```bash
pre-commit run flake8 --files path/to/changed_file.py
pre-commit run yapf --files path/to/changed_file.py
pre-commit run isort --files path/to/changed_file.py
```

If pre-commit dependencies are not installed, do not install broad development
requirements without user approval. Report the missing tool and suggest a local
isolated environment.

## Test levels

ModelScope test levels are selected with the `TEST_LEVEL` environment variable:

| Level | Purpose | Typical use |
| --- | --- | --- |
| 0 | Basic interface and framework function tests. This is the default. | Local core validation before review. |
| 1 | Important end-to-end functional tests. CI after code review may run this level. | Broader workflow checks if dependencies/data are available. |
| 2 | Scenario tests across implemented modules and algorithm fields. | Full regression; can be slow and dependency-heavy. |

Commands:

```bash
# Default level 0 core tests
make tests

# Important functional tests
TEST_LEVEL=1 make test

# Broad scenario tests
TEST_LEVEL=2 make test
```

Contributor guidance may mention both `make tests` and `make test`; the
inspected build targets expose `make test`. If `make tests` is unavailable in a
checkout, use `make test` or run focused Python test files directly.

Tests can gate higher-level cases with:

```python
from modelscope.utils.test_utils import test_level

@unittest.skipUnless(test_level() >= 1, 'skip test in current test level')
def test_run_by_direct_model_download(self):
    ...
```

## Focused tests for customization work

Use focused local tests before broad commands:

| Change area | First focused checks | Broader checks |
| --- | --- | --- |
| Pipeline subclass behavior | A synthetic test that builds a local custom pipeline and calls it on no-network input | Relevant custom pipeline tests; then level 0 test suite. |
| Registry changes | Unit test for duplicate registration, group key, `module_name`, and `build_from_cfg` failure message | Pipeline/model/preprocessor builder tests. |
| CLI pipeline scaffold | Help-only check and planner output; if running real CLI, write to a temporary directory | CLI custom pipeline tests if present and safe. |
| Config trust checks | JSON/YAML passive config tests and `.py` config refusal/opt-in tests | Dataset/pipeline tests that pass `trust_remote_code`. |
| Plugin import behavior | Import-only tests in isolated temporary modules | Plugin manager tests only when they avoid package installation/network. |

Recommended no-network custom pipeline smoke shape:

1. Create a temporary directory and write `configuration.json`.
2. Define/register a tiny pipeline class inside the test or import a local test
   module.
3. Assert the registry contains the alias.
4. Build through `pipeline(task=..., pipeline_name=..., model=temp_dir)`.
5. Call with a string/dict/list and assert deterministic output.

Avoid LFS fixture data, hub downloads, model uploads, or GPU-specific fixtures
for initial customization validation.

## Git LFS and submodule data

ModelScope stores many test assets such as images, videos, and models with
Git LFS in a `data/test` submodule. Contributor guidance notes that a recursive
clone is needed to populate submodule data, and that new test data should be
tracked and committed in the data submodule before committing the submodule
update in the main repository.

Agent guardrails:

- Do not assume `data/test` exists or that LFS objects are present.
- Prefer synthetic fixtures for custom pipeline tests.
- If a failing test references missing `data/test/...`, identify it as an LFS or
  submodule setup issue before changing product code.
- Do not run `git lfs pull`, update submodules, or push test data unless the
  user explicitly requests repository maintenance and accepts network effects.
- When adding tests, choose tiny generated fixtures unless the test genuinely
  needs canonical media/model data.

## Development and review workflow

Typical human workflow in the contributor docs:

1. Pull latest master with rebase.
2. Create a feature branch.
3. Make changes.
4. Commit with a meaningful message.
5. Push and open a pull request.

For agents, do not perform branch, commit, push, or PR operations unless the
user explicitly asks. When only editing code in a local checkout:

- Keep changes small and tied to the ModelScope extension point.
- Run focused tests first.
- Record skipped network/GPU/LFS checks.
- Avoid broad refactors or package-wide formatting unrelated to the requested
  change.

## Build and package checks

Inspected build targets include:

- `make linter`: runs the repository linter script.
- `make test`: runs the CI test script.
- `make whl`: regenerates the AST template and builds source/wheel artifacts.
- `make docs`: builds documentation.
- `make clean`: removes package and docs build directories.

`make whl` and docs builds can be slower and may create many artifacts. Use them
only when packaging or documentation changes require it.

## Optional backend policy

Many ModelScope domains require optional packages, CUDA, vendor runtimes, or
large model/data caches. For customization work in this production scope:

- Treat CUDA/domain execution as optional and unverified.
- Do not use a CPU import as proof of a GPU extension.
- If a custom component claims GPU support, include a CPU-safe test plus a
  separately documented optional GPU check.
- If a native test would download a model, access the network, or require LFS,
  classify it as optional and explain the prerequisite.
