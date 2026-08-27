# SDV root troubleshooting

Use this page for cross-cutting installation, import, backend, and routing issues. Workflow-specific errors live in each sub-skill's `references/troubleshooting.md`.

## Install/import

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'sdv'` | SDV is not installed in the active Python runtime. | Run `python -m pip install sdv` in the target environment, then `python -c "import sdv; print(sdv.__version__)"`. |
| `pip check` reports conflicts involving pandas, numpy, torch, or sdmetrics. | The runtime has incompatible package versions. | Use a fresh virtual environment or conda prefix and install SDV once. Avoid mixing system packages, user site packages, and editable installs. |
| Import works in a checkout but fails from another directory. | The source checkout, not the installed distribution, supplied the import. | Install the package and verify with `python -I -c "import sdv; print(sdv.__version__)"` from outside the checkout. |
| User asks for an `sdv` CLI command. | This repository snapshot does not provide a visible `sdv.cli` module even though package metadata has an entry-point group. | Treat SDV as a Python API package unless the target installed distribution independently verifies a command and help output. |
| Excel local I/O fails with missing engine errors. | `sdv[excel]` or pandas Excel backends are missing. | Install `python -m pip install "sdv[excel]"` or use CSV handlers instead. |

## Optional system and backend checks

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `metadata.visualize(..., output_filepath='graph.png')` fails but graph object creation works. | Python `graphviz` package exists but Graphviz `dot` executable is missing. | Install Graphviz in the runtime or system image and verify `dot -V`; use `python scripts/check_import.py --require-dot` from this skill directory. |
| CTGAN/TVAE/CopulaGAN or PAR complains about torch. | Deep-model dependencies are missing or incompatible. | Install a runtime that can import torch, or use `GaussianCopulaSynthesizer` / CPU workflows when deep models are not required. |
| GPU expected but torch reports no CUDA. | CPU-only torch, incompatible driver/wheel, or no visible GPU. | Use `python scripts/check_import.py --check-cuda`; set `enable_gpu=False` for single-table deep models or `cuda=False` for PAR unless GPU execution is required. |
| Saved deep model fails to load on CPU-only hardware. | The model was saved with CUDA-backed torch state. | Load/sample on a compatible GPU runtime or refit/save with CPU settings for portability. |

## Routing mistakes

| Symptom | Better route |
| --- | --- |
| The task is mostly about reading files, metadata sdtypes, keys, relationships, or visualization of metadata itself. | [data-preparation](../sub-skills/data-preparation/SKILL.md) |
| The task is mostly about business rules, custom constraint functions, JSON constraint files, or constraint errors. | [constraints](../sub-skills/constraints/SKILL.md) |
| The task has one DataFrame and asks to synthesize rows. | [single-table](../sub-skills/single-table/SKILL.md) |
| The task has several related tables and foreign keys. | [multi-table](../sub-skills/multi-table/SKILL.md) |
| The task has repeated sequence IDs and wants time-series/sequential rows. | [sequential](../sub-skills/sequential/SKILL.md) |
| The task already has synthetic data and asks to score, diagnose, or plot it. | [evaluation](../sub-skills/evaluation/SKILL.md) |

## Staleness and provenance

Read [repo-provenance.md](repo-provenance.md) before using this skill against a newer SDV checkout. Refresh the skill when:

- The current repo commit differs from the provenance commit.
- Package version, public import modules, synthesizer constructor signatures, or metadata schemas changed.
- The checkout gains/removes a real CLI module.
- Major dependency or backend requirements changed, especially torch/CUDA, Graphviz, pandas, or sdmetrics.

## When generated guidance is not enough

Stop and gather more evidence when:

- A task requires SDV Enterprise-only behavior such as actual DayZ synthesis beyond public parameter creation/validation.
- A user asks for privacy, disclosure-risk, fairness, compliance, or downstream model utility guarantees. SDV quality/diagnostic reports do not prove those properties.
- A task depends on private demo buckets, DataCebo credentials, or private datasets. Community SDV rejects private demo buckets and the skill cannot invent credentials.
- A task requires long training, large downloads, or production-scale benchmarks. Use small smoke runs first and get explicit approval before expensive runs.
