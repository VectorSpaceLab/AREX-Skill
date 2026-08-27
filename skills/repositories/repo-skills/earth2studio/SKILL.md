---
name: earth2studio
description: "Guides Earth2Studio weather and climate inference workflows, data
  access, model and component selection, output/checkpoint handling, extension,
  and optional REST serving with backend-aware validation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Earth2Studio operating guide

Use this repo skill when a task names **Earth2Studio** or asks to build a
composable AI weather/climate workflow using its `earth2studio` Python APIs:
models, data sources, lexicons, workflows, IO, checkpoints, ensembles,
assimilation, statistics, custom components, or the optional serving client and
REST server.

This is a routing skill, not a model-weight or dataset bundle. It teaches the
public contracts and safe decision sequence; a selected model extra, checkpoint,
remote data source, credential, service, and accelerator may still be required.
Read [scope and limitations](references/scope-and-limitations.md) before
attempting a large, networked, or production workflow.

## First checks

Install the public package into the intended environment, then add only the
route-specific extra. For example, use `python -m pip install earth2studio`
(or `uv pip install earth2studio`) for the base package and
`python -m pip install "earth2studio[serve]"` only when the REST/client route
is selected. For a repository checkout, an editable install is a development
operation and should be performed in that checkout's own environment. Verify
with `python -c "import earth2studio; print(earth2studio.__version__)"` and,
for a GPU task, `python scripts/check_environment.py --require-cuda`.

1. Establish the supported Python range (`>=3.11,<3.15`) and the package
   revision in use. Read [repository provenance](references/repo-provenance.md)
   when deciding whether this graph matches a checkout or whether it needs a
   refresh.
2. Decide whether the request is installation/discovery, data preparation,
   inference composition, ensembles, output/restart, model/assimilation,
   statistics/extension, or serving. Use one focused route below; combine routes
   explicitly for cross-cutting requests.
3. Separate **package import**, **component contract**, **backend runtime**,
   **remote asset/data access**, and **service readiness**. Passing one does not
   prove the others.
4. Install only the narrow base/optional extras needed for the selected route;
   do not start with the `all` extra. Use the route's troubleshooting reference
   when compiled model dependencies, GRIB/eccodes, credentials, or CUDA fail.
5. Before a real forecast, inspect model `input_coords()` and
   `output_coords(...)`, source lexicon support, requested variables/times,
   device, lead-time spacing, and IO coordinates. Use the offline helpers in
   the relevant route before downloads or long runs.

## Route map

- **Install, compare models/data, choose extras or backends:** read
  [installation-discovery](sub-skills/installation-discovery/SKILL.md).
- **Fetch gridded, forecast, observation, tabular, satellite, or local data;
  map variables through lexicons:** read
  [data-sources](sub-skills/data-sources/SKILL.md).
- **Build deterministic or prognostic-plus-diagnostic inference:** read
  [workflows](sub-skills/workflows/SKILL.md), then data-sources and
  io-checkpointing for the concrete inputs and output.
- **Run multiple members, perturb initial conditions, batch or interpolate:**
  read [ensembles](sub-skills/ensembles/SKILL.md), then IO/checkpointing for
  member-aware storage.
- **Persist outputs, use Zarr/NetCDF/Xarray/KV, shard, or resume:** read
  [io-checkpointing](sub-skills/io-checkpointing/SKILL.md).
- **Choose/load a prognostic, diagnostic, downscaling, nowcasting, seasonal,
  or data-assimilation model:** read
  [models-and-assimilation](sub-skills/models-and-assimilation/SKILL.md).
- **Compute metrics/statistics or implement custom components:** read
  [statistics-and-extension](sub-skills/statistics-and-extension/SKILL.md).
- **Submit remote work, inspect schemas/status/results, or configure a REST
  service:** read [serving](sub-skills/serving/SKILL.md).

## Core composition order

For most forecast tasks, use this order:

1. Installation-discovery: select a model family, exact extra/backend, data
   source, variables, and license/access requirements.
2. Models-and-assimilation: load or inspect the component and record its input
   coordinate system. Do not infer a grid or history window from the class name.
3. Data-sources: verify that the source/lexicon can provide the exact variables,
   times, lead times, and units; fetch or interpolate only after validation.
4. Workflows or ensembles: call the appropriate `earth2studio.run` function
   with explicit device, step/member, output-coordinate, and checkpoint choices.
5. IO-checkpointing: initialize all output coordinates and variable names,
   choose storage/chunks/shards, and validate restart semantics.
6. Statistics-and-extension or serving: score/aggregate results, extend a
   protocol, or expose a validated workflow remotely.

The main public orchestration functions are `run.deterministic`,
`run.diagnostic`, and `run.ensemble`; the data helpers are `fetch_data` and
`fetch_dataframe`. Exact signatures and coordinate rules belong in the focused
references rather than this router.

## Validation and failure policy

Prefer a tiny, offline, deterministic fixture before a real model/data run. Keep
network, credentials, model downloads, service processes, destructive writes,
large ensembles, and long examples explicitly opt-in. When a failure occurs,
identify the first boundary—Python/package, optional dependency, API/schema,
coordinate/data, backend/device, storage/checkpoint, remote access, or service—
and follow the nearest route's troubleshooting guide. Do not turn a CPU import
into a CUDA/model success claim, or a client import into a healthy Redis/API
service claim.

Cross-cutting symptoms and recovery are in
[troubleshooting](references/troubleshooting.md). The source snapshot and
refresh trigger are in [repo provenance](references/repo-provenance.md). The
structured routing metadata is in
[repo-routing-metadata.json](references/repo-routing-metadata.json).
