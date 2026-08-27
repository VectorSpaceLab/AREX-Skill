# Builders and gzip-pickle caches

## Builder contracts

A learned `AbstractAgent` exposes two lists:

- `get_feature_builders()` returns `AbstractFeatureBuilder` instances. Each
  builder receives only an `AgentInput` and returns a dictionary of tensor
  features. It must implement `get_unique_name()` and
  `compute_features(agent_input)`.
- `get_target_builders()` returns `AbstractTargetBuilder` instances. Each
  builder receives a `Scene`, so it can use ground truth, and returns a
  dictionary of tensor targets. It must implement `get_unique_name()` and
  `compute_targets(scene)`.

The model receives merged dictionaries. A learned agent must return a
`prediction` dictionary containing `trajectory` with shape `[B, T, 3]`, and its
loss must be one scalar tensor. The feature builder and target builder may each
return multiple dictionary entries, but all dictionary keys should be unique
within the merged feature/target namespaces.

The built-in baseline names are cache-critical:

| Agent/config | Builder kind | `get_unique_name()` | Payload keys |
|---|---|---|---|
| EgoStatusMLP | feature | `ego_status_feature` | `ego_status` |
| EgoStatusMLP | target | `trajectory_target` | `trajectory` |
| TransFuser | feature | `transfuser_feature` | `camera_feature`, `lidar_feature` unless latent, `status_feature` |
| TransFuser | target | `transfuser_target` | `trajectory`, `agent_states`, `agent_labels`, `bev_semantic_map` |

TransFuser's `latent=true` feature payload intentionally omits
`lidar_feature`. Keep latent and non-latent caches in separate roots and verify
the model's expected feature keys; the shared builder name does not protect
against this semantic mismatch.

## On-disk layout and serialization

For each scene, the dataset uses the scene metadata log name and initial token:

```text
<cache-root>/
  <log_name>/
    <initial_token>/
      ego_status_feature.gz
      trajectory_target.gz
```

A `.gz` file is gzip-compressed pickle containing a dictionary of
`str -> torch.Tensor`. NAVSIM writes it with gzip compression level 1 for a
fast size/read trade-off. Load the complete dictionary, then merge it into the
feature or target dictionary; do not expect one tensor per file.

`get_unique_name()` is directly concatenated with `.gz`. Therefore:

- names must be stable, filesystem-safe, and unique across the builders used in
  one dataset;
- renaming a builder invalidates old files until the cache is regenerated;
- a missing one of *any* requested feature or target files makes a token
  invalid for `CacheOnlyDataset`;
- use separate cache roots for changes to builder code, sensor history,
  trajectory sampling, split, agent configuration, and preprocessing versions;
- never infer cache validity from file count alone: inspect the required stems
  and, when possible, load a tiny sample and check tensor keys/shapes.

The dataset indexes by token. The cache path's log directory is used to filter
cache-only logs, while the token path and builder stems are used to load data.
Keep log names and tokens from one selected split together to avoid accidental
train/validation leakage.

## `Dataset` versus `CacheOnlyDataset`

`Dataset` always has a `SceneLoader`. Without a cache root, it computes builders
on `__getitem__`. With a cache root, construction scans existing files and
`cache_dataset()` creates missing entries (or all scene-loader entries when
`force_cache_computation=true`); `__getitem__` then requires the token to be in
the valid cache map.

`CacheOnlyDataset` requires an existing directory and never builds a
`SceneLoader`. It scans requested log directories, retains only tokens for
which every requested builder stem exists, and loads features/targets from
those files. A missing directory raises immediately; an empty valid-token set
usually means the cache's log names, stems, agent settings, or split do not
match.

When `use_cache_without_dataset=true`, the training runner asserts both:

```text
force_cache_computation == false
cache_path is not None
```

This is a deliberate safety boundary: cache-only mode has no scene loader from
which it could recompute missing data. Do not “fix” the assertion by enabling
force computation; either prepare the cache first or use the SceneLoader path.

## Cache creation versus metric caching

Training feature/target caches contain model inputs and supervision. They are
not the metric caches used by scoring/evaluation. Keep roots, naming, and
lifecycle separate. Training cache creation may need camera/LiDAR/map access
because target builders can rasterize maps and annotations; a cache-only run
still needs only the already serialized tensors, but it must have all required
logs and builder files.

## Tiny-fixture inspection

A safe fixture can use one synthetic `AgentInput`/`Scene` pair and trivial
builders whose names are `fixture_feature` and `fixture_target`. Verify that:

1. both dictionaries serialize and deserialize through gzip pickle;
2. the expected `<log>/<token>/<name>.gz` files are found;
3. removing either file excludes the token from cache-only indexing;
4. a cache-only configuration rejects `force_cache_computation=true` before
   any scene or data construction.

This checks file semantics without reading a dataset, downloading anything, or
starting a Lightning trainer.
