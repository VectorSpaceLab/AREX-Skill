# Core Graph Troubleshooting

## Compatibility and Upgrades

- **Symptom:** graph loads with `CompatibilityNode` or `UnknownNodeType`. **Cause:** the provider/plugin that defined the saved node is not loaded. **Action:** load the plugin and retry; do not compute the compatibility node.
- **Symptom:** `VersionConflict` or `DescriptionConflict`. **Cause:** saved node major version or nested attribute shape differs from the current descriptor. **Action:** compare descriptor versions and list/group structure; upgrade only after preserving required attributes.
- **Symptom:** `GraphCompatibilityError` from `loadGraph(..., strictCompatibility=True)`. **Action:** use non-strict load to inspect `graph.compatibilityNodes`, repair providers/versions, then strict-load again.

## Cache, Status, and Chunks

- **Symptom:** node appears `RUNNING`/`SUBMITTED` after a crash. **Action:** inspect status files and submitter job state; use `--forceStatus` only after confirming no process is active.
- **Symptom:** parallel node has no chunks or wrong chunk count. **Cause:** dynamic size input was not updated or `createChunks()` was not called after input change. **Action:** update graph/node internals, call `evaluateSize()`/`createChunks()`, and verify the descriptor's `size` and `parallelization`.
- **Symptom:** preprocess succeeds but global status is `ERROR`. **Action:** inspect separate preprocess/postprocess status/log files; a successful standard chunk does not erase a failed preprocess.
- **Symptom:** output path points into an unexpected folder. **Action:** inspect expression variables such as `{nodeCacheFolder}`, graph cache settings, and saved `header.cacheDir`.

## Topology and Attributes

- **Symptom:** `InvalidEdgeError`. **Cause:** source/destination attributes belong to different graphs or their base types are incompatible. **Action:** connect compatible output/input descriptors from the same graph; inspect nested list/group child attributes.
- **Symptom:** downstream nodes are not invalidated. **Cause:** descriptor set `invalidate=False`, attribute is internal/non-invalidating, or graph update was suppressed. **Action:** verify descriptor invalidation flags, leave `GraphModification`, and call `graph.update()`.
- **Symptom:** `findNode` reports multiple candidates. **Action:** use the exact instance name or a more specific expression; prefix lookup is intentionally strict when ambiguous.
