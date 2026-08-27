# Repository Development and Validation

This reference is for agents editing the DeePMD-kit checkout, especially integration-facing code under LAMMPS, i-PI, C/C++ APIs, Node.js, CLI wiring, or docs.

## Development Principles

- Start with a narrow subsystem impact map before running commands.
- Prefer targeted tests and smoke checks; do not run the full test suite during normal iteration.
- Respect long build durations and set timeouts high enough that expected builds are not canceled.
- Keep training examples as validation smoke tests only; real training can take hours or days.
- When Python files changed, run `ruff check .` and `ruff format .` before final handoff when practical.
- Use conventional commit format when drafting a commit message or PR title.

## Environment Bootstrap

Recommended local bootstrap:

```bash
uv venv venv
source venv/bin/activate
uv pip install tensorflow-cpu
uv pip install torch --index-url https://download.pytorch.org/whl/cpu
uv pip install -e .[cpu,test]
```

Expected timing:

| Step | Typical time | Timeout guidance |
| --- | ---: | --- |
| Virtual environment creation | about 5 seconds | short timeout is fine |
| TensorFlow CPU install | about 8 seconds | allow dependency resolution time |
| PyTorch CPU install | about 5 seconds | allow dependency resolution time |
| Editable package build | about 67 seconds | use at least 120 seconds |

Do not leak the local environment prefix into public docs, examples, or skill content.

## C++ Component Build

Before building C++ components, make sure TensorFlow and PyTorch are importable in the active environment, then set backend roots dynamically:

```bash
export TENSORFLOW_ROOT=$(python -c 'import importlib.util,pathlib; print(pathlib.Path(importlib.util.find_spec("tensorflow").origin).parent)')
export PYTORCH_ROOT=$(python -c 'import torch; print(torch.__path__[0])')
# Run the repository C++ component build helper from the checkout root.
```

Expected timing:

- C++ component build takes about 164 seconds.
- Use a timeout of at least 300 seconds.
- Never cancel this build just because it runs for a few minutes.

Run this only when the changed code requires C++/LAMMPS/native component validation or the user explicitly asks for it.

## Targeted Validation Commands

| Change area | First validation | Broader follow-up |
| --- | --- | --- |
| Core TensorFlow CLI or `dp test` behavior | Run the project's fast single-case TensorFlow `dp test` pytest target | Run the containing TensorFlow `dp test` pytest file |
| Python CLI routing or parser edits | `dp --version` and `dp -h` | Backend help: `dp --tf -h`, `dp --pt -h`, `dp --jax -h`, `dp --pd -h` |
| Python import or backend package wiring | `python -c "import deepmd; import deepmd.tf; print('Both interfaces work')"` | Add backend-specific import checks as needed |
| LAMMPS integration code | A local LAMMPS test only when a DeePMD-enabled `lmp` is available | C++ build plus LAMMPS plugin/built-in smoke test |
| i-PI driver code | Import/build check plus a small driver-focused test if available | Short client/server smoke only with user-approved runtime |
| C/C++ API code | Relevant C++ API unit test or compile smoke | C++ component build and selected native tests |
| Node.js wrapper | `node` package test when wrapper is built | Rebuild Node wrapper if generated binding files changed |
| Formatting-only Python docs/code | `ruff check .` and `ruff format .` | No full suite needed unless behavior changed |

Known useful checks include the project's fast single-case TensorFlow `dp test` pytest target and the containing TensorFlow `dp test` pytest file.

The single test typically runs in 8-13 seconds. The containing file typically runs in about 15 seconds and should use a timeout of at least 60 seconds.

## Training Smoke Tests

Use only when training behavior must be validated and the user accepts a bounded run:

```bash
# From the repository's small water training example directory:
timeout 60 dp train input.json --skip-neighbor-stat
```

```bash
# From the repository's small water training example directory:
timeout 60 dp --pt train input_torch.json --skip-neighbor-stat
```

Expected signal: training starts and prints batch/RMSE progress. Do not expect convergence in a 60-second smoke.

## Lint and Formatting

Install ruff if it is unavailable:

```bash
uv pip install ruff
```

Run:

```bash
ruff check .
ruff format .
```

`ruff check .` and `ruff format .` are expected to complete quickly. If formatting changes files unrelated to the task, inspect before final handoff and avoid mixing unrelated changes into the patch.

## Maintainer Patch Planning

For a patch touching CLI dispatch:

1. Inspect the parser/backend selection impact.
2. Run a focused CLI help/version check if the package is installed.
3. Run the most relevant single Python test, usually a `dp test` or parser-specific test if one exists.
4. Run `ruff check .` and `ruff format .` if Python changed.
5. Avoid full-suite execution unless the user explicitly asks for release-level validation.

For a patch touching LAMMPS plugin code:

1. Inspect C++ compile impact and LAMMPS API changes.
2. Decide whether plugin-only compile is enough or whether the whole C++ build is needed.
3. If a local DeePMD-enabled `lmp` is available, run a minimal input smoke with a tiny model/data fixture.
4. If no `lmp` is available, report compile/static checks and the exact native candidate that should be run later.

For a patch touching C/C++ APIs:

1. Identify whether the C ABI, C++ API, HPP wrapper, or backend implementation changed.
2. Select the smallest matching native test.
3. Rebuild C++ components only when headers, library symbols, or backend integration changed.
4. Watch for ABI-sensitive changes in exported signatures.

For a patch touching Node.js:

1. Decide whether JS wrapper code, generated SWIG output, package metadata, or CMake Node options changed.
2. Run Node tests only when the wrapper is built locally.
3. If wrapper generation is required, confirm Node.js, SWIG, and node-gyp availability before attempting a build.

## Conventional Commits

Use conventional commit style for commit messages and PR titles:

```text
fix(lmp): correct deepmd plugin load handling
feat(api): add charge-spin native overload coverage
docs: clarify i-PI client configuration
test(cli): add backend alias parser coverage
```

Common types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`, and `ci`.

## Avoid

- Full test suite by default; it has hundreds of files and can take over an hour.
- Unbounded training runs as validation.
- Unapproved dependency upgrades in a user-provided environment.
- Broad rebuilds when a narrow targeted test covers the edit.
- Guessing missing native tools such as `lmp`, MPI launchers, or cluster modules.
