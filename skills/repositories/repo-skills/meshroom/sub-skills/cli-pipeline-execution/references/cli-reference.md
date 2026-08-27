# Meshroom CLI Reference

## `meshroom_batch`

Purpose: initialize a pipeline template or custom `.mg`, apply inputs/output/parameter overrides, optionally save, compute locally, or submit.

Important options:

```text
-p, --pipeline FILE.mg / PIPELINE
-i, --input FILE FOLDER [NODEINSTANCE=FILE,FOLDER,...]
-I, --inputRecursive FOLDER [NODEINSTANCE=FOLDER,...]
-o, --output FOLDER [OUTPUT_NODE_INSTANCE=FOLDER | INSTANCE.ATTRIBUTE=VALUE | TYPE:ATTRIBUTE=VALUE]
-s, --save FILE
--submit
--submitter NAME
--submitLabel LABEL
--compute yes/no
--toNode NODE [...]
--forceStatus
--forceCompute
--overrides JSON_FILE
--overrideCacheDir FOLDER
--paramOverrides NODETYPE:param=value NODEINSTANCE.param=value
--setInvalidationString STRING
-v/--verbose fatal|error|warning|info|debug|trace
```

`--input` applies values to all input nodes by default. Target one input node with `NodeName=value`; comma-separated values are parsed as a group for that node. `--inputRecursive` scans directories recursively.

Output forms are processed by `Graph.configureOutputNodes()`:

- `/results`: set remaining output-folder attributes on all output nodes.
- `Export_1=/results`: set one output node's folder.
- `Export_1.exportLabel=final`: set one exposed attribute on one instance.
- `ExportResults:exportLabel=final`: set one exposed attribute on every node of that type.

Only `OutputNode.outputAttributes` can be targeted by attribute form. A graph passed to `--output` must contain at least one output node.

## `meshroom_compute`

Purpose: compute a saved graph or selected node.

```text
meshroom_compute GRAPHFILE.mg
  --node NODE_NAME
  --toNode NODE_NAME
  --inCurrentEnv
  --extern
  --forceStatus
  --forceCompute
  --cache FOLDER
  --iteration N
  --preprocess / --postprocess
  -v/--verbose ...
```

- `--node` computes only that node and expects dependencies to be ready.
- `--toNode` computes the node and dependencies.
- `--extern` is used by submitter-created jobs; it changes status/log behavior.
- `--iteration` selects one chunk; `--preprocess` and `--postprocess` select lifecycle chunks.
- `--inCurrentEnv` skips a dedicated plugin runtime environment.

## Inspection Commands

- `meshroom_info version [-p]`: print version and optionally package path.
- `meshroom_info nodeinfo [-n NAME] [--default_value]`: list or inspect registered node descriptors.
- `meshroom_info pipelines [-n NAME]`: list templates or show template metadata/versions.
- `meshroom_status GRAPHFILE.mg [--node NAME | --toNode NAME]`: print chunk/node statuses.
- `meshroom_statistics GRAPHFILE.mg [--node NAME | --graph NAME] [--exportHtml FILE]`: print statistics; HTML export requires plotting dependencies.

## Submission Commands

`meshroom_submit GRAPHFILE.mg --submitter NAME [--toNode NODE] [--submitLabel LABEL]` loads the graph and delegates to a registered submitter. The submitter must be discoverable and the graph must be saved.

`meshroom_createChunks` is an integration helper used by submitters to create per-chunk tasks. It is not the normal first command for a user; use `meshroom_batch --submit` or `meshroom_submit` instead.

## Logging

Use `MESHROOM_VERBOSE` or `-v` to control logs. For hidden QML failures, use `MESHROOM_OUTPUT_QML_WARNINGS=1` in the UI process, not in a compute-only command.
