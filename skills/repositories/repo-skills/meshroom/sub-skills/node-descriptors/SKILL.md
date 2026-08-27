---
name: node-descriptors
description: "Guides Meshroom node descriptor authoring, attribute schemas,
  command-line nodes, init/input/output nodes, dynamic sizes, and reusable
  general utility nodes."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Meshroom Node Descriptors

Use this route when creating or reviewing a Python node type, exposing inputs/outputs, wrapping an external executable, initializing inputs from CLI/UI, or diagnosing descriptor validation errors.

## Read First

- [Descriptor API reference](references/descriptor-api-reference.md)
- [Node authoring workflows](references/node-authoring-workflows.md)
- [General utility nodes](references/general-nodes.md)
- [Troubleshooting](references/troubleshooting.md)
- Run [scripts/validate_node_descriptor.py](scripts/validate_node_descriptor.py) for a safe descriptor validation/import check.

## Choose the Base Class

| Need | Descriptor base |
| --- | --- |
| Python computation in the current Meshroom environment | `desc.Node`, implement `process(self, node)` or `processChunk(self, chunk)` |
| Wrap an external executable | `desc.CommandLineNode`, define `commandLine` and inputs/outputs |
| Placeholder/input-only node | `desc.InitNode`, optionally mix in `desc.InputNode` and implement `initialize` |
| Export destination configurable from templates/CLI | mix in `desc.OutputNode` and expose `outputAttributes` |
| Visual grouping only | `desc.BackdropNode` |

## Authoring Loop

1. Define a descriptor module with a stable class name and optional `__version__`.
2. Declare `inputs`, `outputs`, `category`, `documentation`, resource levels, `size`, and `parallelization`.
3. Validate defaults and nested attributes before loading the plugin.
4. For a Python node, write outputs under `node.internalFolder` or descriptor expression paths such as `{nodeCacheFolder}/result.txt`.
5. For a command-line node, verify placeholders with a tiny fixture and inspect the generated command before running an external binary.
6. Register the node through a plugin or `MESHROOM_NODES_PATH`; do not mutate the core registry ad hoc in production.
7. Add focused tests for descriptor validation, command-line formatting, dynamic outputs, and serialization.

## Important Boundary

Descriptor classes define static schema. Live values, links, UIDs, status, and cache belong to the core graph/node objects. If a question is about graph serialization or compatibility, route to [core-graph-engine](../core-graph-engine/SKILL.md).
