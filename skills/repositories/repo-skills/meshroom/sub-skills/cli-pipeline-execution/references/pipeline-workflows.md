# CLI Pipeline Workflows

## Configure Without Computing

Use this pattern when validating paths, overrides, or output routing:

```bash
meshroom_batch \
  --pipeline photogrammetry \
  --input /data/images \
  --output /data/results \
  --save /work/project.mg \
  --compute no
```

If the template name is unavailable, pass a `.mg` template path and inspect `meshroom_info pipelines` first. A saved scene stores its cache association.

## Compute a Saved Scene

```bash
meshroom_compute /work/project.mg
meshroom_status /work/project.mg
meshroom_statistics /work/project.mg --graph FinalNode
```

Use `--toNode` when only a target and its dependencies are needed. Use `--node` only when dependencies are already successful. If a node runs in a plugin-specific environment, omit `--inCurrentEnv` unless intentionally debugging the parent environment.

## Parameter Overrides

`--paramOverrides` accepts either a node instance form (`Node_1.attribute=value`) or a node type form (`NodeType:attribute=value`). `MeshroomSceneParameter` produces these strings so a graph can build an override list dynamically.

`--overrides JSON_FILE` applies a JSON graph parameter override file. Preserve the original `.mg` and record the override source when reproducing a result.

## Output Routing

To configure multiple export nodes, give targeted forms first and a global folder last. The graph applies targeted output-folder settings and uses the global path as fallback for remaining output nodes. If a target attribute is not exposed, use the descriptor's `outputAttributes` or change the node design rather than forcing an internal attribute.

## Status Recovery

1. Run `meshroom_status` and inspect the node/chunk log paths printed at higher verbosity.
2. Check whether `Status.RUNNING`/`SUBMITTED` corresponds to a live local process or submitter job.
3. Inspect `nodeStatus` and chunk status files under the node cache.
4. Use `--forceStatus` only after ruling out a live job.
5. Use `--forceCompute` only when recomputation should invalidate cached success.

## External Binary Boundary

Framework-level commands can parse and save graphs without AliceVision. Actual photogrammetry nodes fail if their executable is absent from `PATH`, `ALICEVISION_ROOT`, or plugin process environment. Report that as an external-binary failure and preserve the command/log rather than treating it as a graph serialization bug.
