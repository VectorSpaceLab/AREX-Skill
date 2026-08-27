# Cross-cutting troubleshooting

## Import and dependency failures

- **`ModuleNotFoundError: nuplan`**: verify the package is installed in the
  active interpreter, then run `python -c "import nuplan; print(nuplan.__file__)"`.
  Do not rely on a checkout accidentally present on `PYTHONPATH`.
- **Hydra/OmegaConf resolver or dataclass errors**: this source version uses
  Hydra 1.1.0rc1/OmegaConf 2.1.0rc1 and Python 3.9-era dependencies. Check
  versions and `pip check`; do not fix a stale config by mixing a newer Hydra
  with the old config tree.
- **GeoPandas/Fiona/Rasterio/Shapely import errors**: check the compiled
  package variant and platform before debugging map files. A DB-only task can
  omit map rendering dependencies.
- **Torch or torchvision mismatch**: compare Torch, torchvision, torch-scatter,
  and the CUDA tag. A successful CPU import does not prove CUDA or model
  execution.

## Data and map failures

- **No DBs / missing split**: run the bundled data-root validator with the
  exact `--split` and inspect `NUPLAN_DATA_ROOT/nuplan-v1.1`. Do not download or
  substitute another split automatically.
- **Missing GeoPackage or map version**: confirm `NUPLAN_MAPS_ROOT`,
  `NUPLAN_MAP_VERSION`, the metadata JSON, each declared location/version, and
  `map.gpkg`. A DB's location field and package map-version basename are not
  interchangeable.
- **Missing image/point-cloud blob**: the DB stores relative filenames; check
  the sensor root and the referenced key. Keep DB, map, and sensor roots
  separate.
- **Zero scenarios**: first remove optional filters, use a known local split,
  then add scenario type/map/log/route/speed filters one at a time. Check
  `limit_total_scenarios`, timestamp spacing, `remove_invalid_goals`, and the
  available scenario tags before blaming the builder.
- **S3/HTTP failure**: classify it as an external credential/network issue.
  The local validator and local query path do not establish remote access.

## Hydra and workflow failures

- **`MissingMandatoryValue` or unresolved `${...}`**: materialize the full
  config, inspect the saved Hydra config, and add the missing group/key with
  the correct `+group=value` versus `key=value` syntax.
- **Worker hang or opaque Ray error**: reproduce with `worker=sequential`, a
  one-scenario filter, and zero data-loader workers. Only then scale workers.
- **No experiment output / permission error**: verify `NUPLAN_EXP_ROOT` is
  writable and that the output directory is not the read-only dataset root.
- **Metric or nuBoard files missing**: distinguish fresh simulation output,
  serialized logs, metric-only input, aggregated parquet, and the `.nuboard`
  descriptor. Do not point nuBoard at an incomplete or mismatched experiment.

## Model and numeric failures

- **NaN/Inf gradients or outputs**: begin with trainer precision 32, inspect
  the first non-finite feature/target/loss/gradient, and reduce the filter to a
  tiny deterministic case. Re-enable FP16 only after the data path is finite.
- **Feature/target key or shape mismatch**: compare each model wrapper's
  required feature builders and computed target builders with the objective and
  data-loader config. Do not invent feature names from a model class name.
- **CUDA unavailable**: inspect `torch.cuda.is_available()`, device count, the
  wheel CUDA tag, and driver support. Keep the task explicitly CPU-only when
  CUDA is optional; do not claim GPU verification.

## Submission and safety failures

- **CLI help tries to use a DB**: use `nuplan_cli --help` or a subcommand's
  `--help` and avoid the default DB argument. Real DB commands may invoke a
  download helper when a path is absent.
- **Planner output rejected**: preflight finite global rear-axle x/y/heading,
  integer-microsecond strictly increasing timestamps, at least two points, and
  an eight-second minimum horizon. Check observation type and controller match.
- **Protocol mismatch**: do not edit organizer-owned proto or generated gRPC
  files, the submission container, or the submission planner server. Compare
  protected-file digests and fix only the planner/config/dependency/assets
  boundary.
- **Docker/EvalAI failure**: separate local image/container errors from remote
  credential, phase, quota, and hidden-test behavior. Never upload or start a
  remote action as a diagnostic without explicit user intent.
