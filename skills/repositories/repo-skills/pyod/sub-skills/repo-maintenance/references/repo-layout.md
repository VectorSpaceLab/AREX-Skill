# PyOD Repository Layout for Maintainers

Read this when you need to locate the files that own a PyOD behavior, package
surface, CLI entry point, or packaged skill artifact. Paths below are relative
to a PyOD checkout and are included as maintainer navigation facts, not as
runtime links to this generated skill's original source checkout.

## Package identity and metadata

- Distribution name: `pyod`.
- Python requirement from package metadata: `>=3.9`.
- Version source: `pyod/version.py` exposes `__version__`.
- Build backend: setuptools via `setuptools.build_meta`.
- Dynamic project fields: package version from `pyod.version.__version__` and
  dependencies from `requirements.txt`.
- Base runtime requirements observed in `requirements.txt`: `joblib`,
  `matplotlib`, `numpy`, `numba`, `scipy`, and `scikit-learn`.
- Package discovery includes `pyod*` and excludes `test`, `test.*`, `pyod.test`,
  and `pyod.test.*`; tests are source-tree evidence, not package runtime data.
- Source distribution manifest prunes examples, notebooks, and `pyod/test`, and
  includes README, requirements, knowledge JSON, and model analysis JSON data.

## Public source roots

| Root | Maintainer role | Notes |
|---|---|---|
| `pyod/models/` | Detector implementations, time-series/graph/embedding/audio wrappers, thresholding and score combination modules | Detector API changes usually need focused detector tests plus docs/skill impact review. |
| `pyod/utils/` | Data generation/evaluation, ADEngine, investigation state, persistence, knowledge base, encoders, model selection | ADEngine and knowledge changes can affect the packaged skill and generator tests. |
| `pyod/cli.py` | Unified `pyod` CLI entry point | Owns `pyod info`, `pyod install skill`, and `pyod mcp serve` routing. |
| `pyod/mcp_server.py` | Optional MCP server implementation | Must remain import-safe when the `mcp` extra is absent. |
| `pyod/skills/` | Packaged agent skill data and installer helpers | Contains `od_expert` subpackage and install utilities. |
| `docs/` | Sphinx docs and maintainer docs | Docs examples are evidence for user workflows and need synchronized figures/snippets. |
| `examples/` | Example scripts and demo assets | Useful as behavioral evidence; most runtime recipes belong in user-facing sub-skills, not here. |
| `pyod/test/` | Native behavior and regression tests | Use focused selections from `references/testing-guide.md`. |
| `scripts/` | Maintainer helper scripts | Only `regen_skill.py` and `render_agentic_demo.py` are repo scripts in the inspected tree. |

## Optional dependency groups

Package metadata exposes these extras: `torch`, `suod`, `xgboost`, `combo`,
`pythresh`, `embedding`, `openai`, `huggingface`, `graph`, `mcp`, `audio`, and
`all`. Treat them as opt-in. Base import, classic detectors, ADEngine core,
CLI info/help, persistence, and CPU time-series checks do not require installing
all extras.

Common ownership mapping:

- `torch`: neural/deep detectors and some time-series deep models.
- `graph`: PyTorch Geometric graph detectors.
- `embedding`, `openai`, `huggingface`, `audio`: embedding/multimodal/audio
  workflows and external model/service surfaces.
- `mcp`: MCP server runtime; import safety should still work without it.
- `suod`, `xgboost`, `combo`, `pythresh`: optional classic/model-operations
  accelerators or thresholding integrations.

## CLI and entry points

`pyproject.toml` declares two console scripts:

| Entry point | Target | Maintainer notes |
|---|---|---|
| `pyod` | `pyod.cli:main` | Unified CLI with `install`, `info`, and `mcp` subcommands. |
| `pyod-install-skill` | `pyod.skills:install_cli` | Legacy alias for installing packaged skills; output parity with `pyod install skill` is tested. |

When editing CLI behavior, keep the command available both as a console script
and as `python -m pyod.cli ...` for focused tests.

## Packaged skill data

`pyod.skills.od_expert` ships as package data with `*.md` and `references/*.md`.
The installer in `pyod/skills/__init__.py` maps Python package name
`od_expert` to the agent-facing directory name `od-expert`, accepts both forms
as input, copies the whole skill tree, and ignores Python package artifacts such
as `__init__.py`, `__pycache__`, and `*.pyc`.

If a new packaged skill is added, maintain all of these together:

1. Create a data-only subpackage under `pyod/skills/<python_package_name>/`.
2. Add the package-data rule in `pyproject.toml`.
3. Add the underscore-to-hyphen mapping in `pyod/skills/__init__.py`.
4. Add CI safety coverage appropriate for that skill.
5. Document the skill maintenance policy in the bundled `references/skill-maintenance.md` guidance.

## Documentation/example maintenance surfaces

- `docs/examples/agentic.rst` describes the agentic investigation docs page and
  embeds the generated demo figure.
- `examples/agentic_demo.html` is the interactive demo source used by the docs
  figure.
- `scripts/render_agentic_demo.py` captures the HTML demo to a PNG, but it
  requires Playwright plus a Chromium browser. Treat it as an explicitly
  authorized docs-rendering step rather than a default focused test.

## Release and publishing boundary

This sub-skill does not authorize PyPI builds, credential use, tag pushes,
deletions, or publication commands. If an edit touches release material, first
separate safe metadata/test changes from release actions, then ask an authorized
maintainer for explicit approval before any command with external side effects.
