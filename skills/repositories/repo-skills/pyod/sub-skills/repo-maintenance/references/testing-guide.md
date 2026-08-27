# Focused Testing Guide for PyOD Maintainers

Read this after identifying the edited area. Commands are non-destructive by
default and assume they are run from a PyOD checkout with an environment where
PyOD is importable. Use `python -m ...` forms to bind checks to the active
Python environment.

## General policy

- Start with the smallest test slice that covers the changed surface.
- Add optional-extra tests only when the edit changes that extra's code path or
  public contract.
- Prefer generator `--check` and CLI help/info checks before full suites.
- If a command requires network, browser installation, credentials, GPU-only
  backends, or publishing access, stop and ask before running it.
- When optional dependencies are absent, record the skip reason and select a
  CPU/base test or a synthetic verification case instead of installing `all` by
  default.

## Edited area to focused checks

| Edited area | Primary focused checks | Add when relevant |
|---|---|---|
| Package metadata, entry points, installer map | `python -m pytest pyod/test/test_cli.py -q` | `python -m pyod.cli --help`; `python -m pyod.cli info`; isolated install tests from `test_cli.py` if touching install messages or target paths. |
| `pyod/cli.py` | `python -m pytest pyod/test/test_cli.py -q` | `python -m pyod.cli install skill --list`; subprocess parity checks if console scripts are available. |
| `pyod/mcp_server.py` import safety | `python -m pytest pyod/test/test_mcp_server_import.py -q` | Install `pyod[mcp]` only if testing positive server runtime registration outside the existing fake-MCP tests. |
| Packaged `od-expert` Markdown | `python scripts/regen_skill.py --check`; `python -m pytest pyod/test/test_skill_kb_consistency.py pyod/test/test_skill_api_refs.py -q` | `python -m pytest pyod/test/test_cli.py::test_pyod_install_skill_copies_references_tree -q` after packaging/copy behavior changes. |
| `scripts/regen_skill.py` | `python -m pytest pyod/test/test_regen_skill.py -q`; `python scripts/regen_skill.py --check` | Skill consistency/API tests if renderer output changes. |
| Knowledge base detector metadata | `python scripts/regen_skill.py --check` before edits; `python scripts/regen_skill.py`; then `python -m pytest pyod/test/test_regen_skill.py pyod/test/test_skill_kb_consistency.py -q` | Detector-specific tests if KB change reflects a model implementation change. |
| ADEngine/investigation state | `python -m pytest pyod/test/test_ad_engine.py pyod/test/test_ad_engine_v3.py pyod/test/test_ad_engine_compare.py -q` | `python -m pytest pyod/test/test_skill_api_refs.py -q` if skill prose references state or engine fields. |
| Classic detector implementation | The detector's focused test, e.g. `python -m pytest pyod/test/test_iforest.py -q` | `pyod/test/test_base.py`, data utility tests, and README/docs tests if the common API or examples changed. |
| Data generation/evaluation utilities | `python -m pytest pyod/test/test_data.py -q` | Detector tests that consume the changed helper. |
| Persistence | `python -m pytest pyod/test/test_persistence.py pyod/test/test_save_load_clone.py -q` | Model-operation docs/examples if behavior or warnings change. |
| Thresholding/combination | `python -m pytest pyod/test/test_thresholds.py pyod/test/test_combination.py -q` | Optional `pythresh` or `combo` installation only when those integration paths changed. |
| Time-series modules | Focused `pyod/test/test_ts_*.py` slice for the edited model | Optional torch time-series tests only when deep TS models changed. |
| Graph detector modules | Matching `pyod/test/test_pyg_*.py` | Requires `pyod[graph]`; otherwise mark optional-backend skipped. |
| Embedding/audio modules | `pyod/test/test_embedding.py`, `pyod/test/test_audio.py` as applicable | Requires relevant extras and possibly model/audio dependencies; avoid network-backed service calls without approval. |
| Docs examples only | Syntax/doc build checks if already configured; otherwise run the code snippet's closest focused API/CLI test | `scripts/render_agentic_demo.py` only when the HTML demo figure changed and browser prerequisites are authorized. |

## Packaged skill test stack

Use this stack for `od-expert` edits:

```bash
python scripts/regen_skill.py --check
python -m pytest pyod/test/test_regen_skill.py -q
python -m pytest pyod/test/test_skill_kb_consistency.py -q
python -m pytest pyod/test/test_skill_api_refs.py -q
```

What each check catches:

- `regen_skill.py --check`: KB-derived blocks are byte-identical to generator
  output and no file would be modified.
- `test_regen_skill.py`: generator imports, known section names render,
  marker replacement preserves hand-written prose, and raw KB tokens map to
  exposed extras.
- `test_skill_kb_consistency.py`: detector-like backtick tokens in skill prose
  exist in the live KB, KB-derived markers are well-formed, and hand-written
  detector count claims match the live buildable count.
- `test_skill_api_refs.py`: `state.X`, nested `state.X['key']`, and
  `engine.method(...)` references in skill Markdown match live ADEngine and
  InvestigationState behavior.

## CLI/installer checks

Useful non-destructive commands:

```bash
python -m pyod.cli --help
python -m pyod.cli info
python -m pytest pyod/test/test_cli.py::test_pyod_cli_help -q
python -m pytest pyod/test/test_cli.py::test_pyod_info_runs -q
python -m pytest pyod/test/test_cli.py::test_pyod_install_skill_to_target -q
```

The install-to-target tests use temporary directories and should not write to a
real user skill directory. Avoid manually running `pyod install skill` without a
throwaway `--target` unless the user explicitly wants to install the skill.

## Optional-extra skip policy

Optional-backend tests are valid ground truth only when their dependencies are
present or intentionally installed for the change. Do not treat missing optional
packages as a base-regression failure.

- Missing `mcp`: `pyod.mcp_server` must still import safely and `pyod info`
  must not crash. Positive MCP serving requires `pyod[mcp]`.
- Missing `torch`: skip neural/deep detector runtime checks unless the edited
  code path requires torch.
- Missing `torch_geometric`: skip PyG graph detector tests or install
  `pyod[graph]` only for graph changes.
- Missing `xgboost`, `suod`, `combo`, or `pythresh`: run only when the edit
  affects those integrations.
- Missing embedding/OpenAI/HuggingFace/audio packages or credentials: prefer
  import/availability probes and documented fallback guidance unless the user
  authorizes those external/runtime dependencies.

## When a full suite is justified

Run a broader `python -m pytest pyod/test -q` only after a cross-cutting change
such as package metadata, BaseDetector contract, broad dependency upgrades,
ADEngine planner rewrite, or knowledge-base schema change. Even then, classify
optional-extra failures separately from base failures before requesting new
installs.
