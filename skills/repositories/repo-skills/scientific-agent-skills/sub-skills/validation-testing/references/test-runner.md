# Test Runner and Isolated Environments

## One process per skill

Do not collect multiple per-skill suites with one pytest invocation. Many skills ship scripts with top-level names such as `_common.py`, `validate_manifest.py`, or `cluster.py`. Per-skill tests often put their skill's `scripts/` directory on `sys.path`; collecting two skills together can import the wrong helper silently. `tests/conftest.py` blocks that session.

Correct:

```bash
uv run --with pytest python -m pytest tests/<name> -q
python tests/run_all.py <name>
```

Wrong:

```bash
python -m pytest tests/scanpy tests/qiskit
```

## `tests/run_all.py`

- With no skill names, it first runs `tests/_meta`, then every per-skill suite in a separate process.
- With named skills, it skips `_meta` and runs only those suites.
- Arguments after `--` are passed to pytest.
- The script does not implement `--help`; read its docstring for usage.

Examples:

```bash
python tests/run_all.py scanpy
python tests/run_all.py -- -x --tb=long
python tests/run_all.py --isolated scanpy qiskit
```

## `--isolated`

`--isolated` builds a throwaway `uv` environment for each skill from `tests/skill-requirements.toml`. This is required because scientific package pins conflict across the collection.

A script-bearing skill needs a manifest block:

```toml
[skills.<name>]
packages = []
```

Use `packages = []` when all bundled scripts use only the Python standard library. Add `python = "3.11"` or similar only when that skill's documented packages require an older interpreter.

## Choosing scope

- Run a named suite for focused script changes.
- Run `tests/_meta` for structural, link, frontmatter, or manifest changes.
- Run full `tests/run_all.py` only when shared contract/runner changes justify the cost.
- Run full `--isolated` sweep before releases or broad dependency/test-contract changes, not for every small skill prose edit.
