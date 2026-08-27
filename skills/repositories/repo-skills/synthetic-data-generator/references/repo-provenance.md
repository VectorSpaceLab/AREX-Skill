---
schema: disco.repo-provenance.v1
skill_id: synthetic-data-generator
project_name: Synthetic Data Generator (SDGX)
distribution: sdgx
import_package: sdgx
package_version: 0.2.5.dev0
source_commit: f3684582b2f490f50f85f8ffc8d619a7777aed67
source_branch: main
source_tag: null
source_remote_url: https://github.com/hitsz-ids/synthetic-data-generator.git
source_worktree_state: clean before generated skill outputs
---

# Repo provenance

This skill was distilled from the SDGX repository state captured by the evidence paths below. The generated skill outputs may make the checkout dirty after creation; those files are part of the skill draft, not the source baseline.

## Evidence paths used

- `pyproject.toml` for distribution name, Python requirement, dependencies, extras, and `sdgx` console entry point.
- `README.md`, `README_ZH_CN.md`, and `ROADMAP.md` for project purpose, public workflows, CTGAN/LLM features, and roadmap direction.
- `docs/source/user_guides/cli.rst`, `library.rst`, `single_table.rst`, `single_table_column_combinations.rst`, `evaluation.rst`, and `multi_table.rst` for user-facing API/CLI workflows.
- `docs/source/api_reference/**` for public API surfaces documented by Sphinx.
- `sdgx/synthesizer.py`, `sdgx/cli/main.py`, `sdgx/manager.py`, `sdgx/data_loader.py`, `sdgx/data_models/**`, `sdgx/data_processors/**`, `sdgx/models/**`, `sdgx/metrics/**`, and `sdgx/utils.py` for source-verified signatures and behavior.
- `example/*.ipynb` and `example/extension/**` for notebook-level workflows and extension registration patterns.
- `tests/**` for expected behavior, error surfaces, and native verification candidates.
- `benchmarks/**` for performance benchmark intent; benchmark-scale scripts are not bundled as direct runtime checks because their defaults are large and environment-sensitive.

## Refresh signal

Refresh this skill when `sdgx/__init__.py` changes version, `pyproject.toml` dependencies or entry points change, the default processor list in `sdgx/data_processors/manager.py` changes, the CLI command set changes, or the source commit differs from the baseline above.
