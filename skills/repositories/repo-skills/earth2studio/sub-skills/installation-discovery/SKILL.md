---
name: installation-discovery
description: "Route Earth2Studio installation, optional dependency selection,
  environment validation, and task-driven discovery of model families, data
  sources, lexicons, examples, and output backends without running inference or
  downloading data."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Installation and discovery

Use this sub-skill when a user needs to prepare an Earth2Studio environment or
narrow a weather/climate task to a small, defensible set of model, data-source,
lexicon, example, and output-backend candidates. The verified source snapshot is
`0.18.0a0`; treat package metadata and the user's installed version as the
authority when they differ from this snapshot.

## Boundaries

- Give commands and validation steps; do not run package managers, install
  packages, fetch remote data, download checkpoints, run inference, or serve a
  workflow.
- Do not present the catalog as exhaustive. Optional model/data packages,
  credentials, licenses, remote availability, and GPU compatibility remain
  candidate-specific.
- Do not infer compatibility from a model name alone. Check the model's
  `input_coords()` requirements against a source lexicon and then check grid,
  time, region, access, and hardware constraints.
- Route serving requests elsewhere. This sub-skill may identify an output
  backend for a later workflow, but it does not configure `Earth2StudioClient`,
  `RemoteEarth2Workflow`, or a server.

Read the detailed [installation reference](references/install-reference.md),
[model and data overview](references/model-overview.md), and
[troubleshooting guide](references/troubleshooting.md) as needed. Use the safe,
offline [environment checker](scripts/check_environment.py) for a local preflight.

## 1. Normalize the request

Collect only the facts needed for routing:

1. **Install target:** released package, approved source revision, or an
   existing project; package manager (`uv`, `pip`, or Conda-managed Python).
2. **Runtime:** Python version, operating system/build tools, PyTorch version,
   CUDA runtime/driver, GPU model/VRAM/count, and whether CPU-only inspection
   is intended.
3. **Task:** prognostic forecast, diagnostic/downscaling/derived product,
   data assimilation (beta), observations/data preparation, or a combination;
   region, forecast horizon, variables/levels, deterministic versus ensemble,
   and latency/storage needs.
4. **Access constraints:** network/credential policy, checkpoint/data licensing,
   cache location and disk budget, and whether remote availability may be
   inspected later by the user.

If Python or CUDA facts are missing, ask for them rather than promising that an
extra will work. Run only read-only checks supplied by the user, for example:

```bash
python --version
python -c "import torch; print(torch.__version__, torch.version.cuda, torch.cuda.is_available())"
python scripts/check_environment.py --json
```

Use `uv run` instead of bare `python` when the project is managed by uv. The
checker itself is standard-library-only and is safe from an arbitrary cwd.

## 2. Route installation

1. Prefer a fresh Python 3.13 environment. The package declares
   `>=3.11,<3.15`; Python 3.10 and Python 3.15 are unsupported for this
   snapshot. PyTorch must be installed for the selected CUDA/CPU target before
   GPU-sensitive extras.
2. Start with the smallest useful dependency set. The base package supplies
   core APIs and IO interfaces, not most model or data-source dependencies.
   Select one model family plus `data`, `perturbation`, `statistics`, or
   `utils` only when the task needs it. Do not install `all` merely to avoid
   deciding: it is broad, expensive, and does not make every model combination
   semantically compatible.
3. Give, but do not execute, an appropriate command. Released-package forms
   are `uv add "earth2studio[<extra>,...]"` or
   `pip install "earth2studio[<extra>,...]"`. With Conda, create/activate the
   Python 3.13 environment and use standard Python tooling for Earth2Studio;
   do not mix a second dependency resolver without a reason. Approved source
   revisions use the same extra syntax with the project's VCS requirement.
4. Resolve known build-sensitive extras in isolation. AIFS variants use
   `flash-attn`; Atlas and some StormCast variants use `natten`; FCN3/SFNO
   and perturbation use `torch-harmonics`; some packages are configured for
   no-build-isolation. Build tools and Python headers may be required.
5. Explain targeted prerequisites before the command: GraphCast/GenCast use
   WeatherNext and require Python >=3.12; FengWu/FuXi/Pangu use ONNX Runtime
   GPU; CUDA data-assimilation extras use CUDA-13 CuPy and, for most variants,
   cuDF. Avoid combining mutually conflicting uv extras; see the reference.
6. Ask the user to run the command, then validate without downloading assets:

```bash
python -c "import earth2studio; print(earth2studio.__version__)"
python scripts/check_environment.py --require-cuda  # only for GPU tasks
```

A successful core import proves neither optional model imports nor checkpoint
access. Validate each selected optional class with a targeted import after the
user installs its extra; do not import every model namespace as a proxy.

## 3. Route discovery

Build a short list, not a catalog dump:

1. Classify the task as PX (time-stepping forecast), DX (diagnostic,
   downscaling, derived, or tracking), DA (beta assimilation), or data-only.
2. Filter candidates by region, temporal scale, variables/levels, deterministic
   or ensemble requirement, GPU/VRAM, and release/version. Record the extra and
   any access or license prerequisite for each candidate.
3. Identify a data-source family: analysis/reanalysis, forecast, satellite or
   observations, local arrays, or tabular/forecast-frame observations. A data
   source uses `(time, variable)` and returns an xarray `DataArray`; a forecast
   source adds `lead_time`; dataframe variants return pandas dataframes.
4. Compare the model's `input_coords()` variable coordinate with the candidate
   lexicon's `VOCAB` keys. This is a necessary screen, not proof of fit: also
   compare pressure/height conventions, latitude/longitude grid, time/lead-time
   coverage, source availability, and any authentication.
5. Recommend one to three relevant gallery patterns, such as getting started,
   medium range, downscaling, nowcasting, seasonal, data assimilation, IO, or
   extension. Examples are patterns, not a promise that their checkpoints or
   remote inputs are available in the user's environment.
6. Select an output backend only by storage need: `ZarrBackend` is the default
   datetime-friendly choice; `AsyncZarrBackend` is for asynchronous/sharded
   writes with filesystem/inode trade-offs; `NetCDF4Backend`, `XarrayBackend`,
   and `KVBackend` cover other file, in-memory, or key/value needs. This is
   discovery guidance only; no workflow is executed here.

For AutoModel-backed classes, `load_default_package()` only creates a package
reference. Asset access occurs later when model loading resolves package files.
`from_pretrained(path_or_uri)` accepts a local package or supported fsspec-style
URI, including NGC, Hugging Face, and S3 forms. Explain cache and licensing
boundaries before any later load: Earth2Studio's Apache-2.0 license does not
license third-party checkpoints or datasets, and public access does not remove
provider terms or credential requirements.

## 4. Return a handoff

Return:

- normalized task and runtime facts, including unknowns;
- selected package source, exact extras, and why broader extras were rejected;
- a small model/data shortlist with API class names, required variables,
  lexicon evidence, hardware fit, and unresolved access/license limits;
- one to three examples/patterns and the candidate IO backend;
- import/environment check results and the next user-run command;
- explicit omissions: no inference, remote data fetch, checkpoint download,
  serving, or exhaustive catalog claim.

When an import, Python, CUDA, extra conflict, source lexicon, grid, or access
condition cannot be proven locally, label it as an unresolved gap and give the
smallest read-only check that would resolve it.
