# Core Graph Workflows

## Building and Mutating Graphs

```python
import meshroom
meshroom.setupEnvironment()
import meshroom.core
from meshroom.core.graph import Graph

meshroom.core.initNodes()
graph = Graph("example")
source = graph.addNewNode("InputString", name="Source_1")
source.string.value = "hello"
copyNode = graph.addNewNode("CopyFiles", name="Export_1")
# For custom descriptors, connect compatible attributes explicitly:
# source.output.connectTo(copyNode.inputFiles.at(0))
graph.update()
```

Use `GraphModification(graph)` when several topology/attribute operations should trigger one final update. After adding/removing edges, call `graph.update()` before asking for depths, DFS order, or compute eligibility.

Common graph operations:

- `graph.findNode("Prefix")` accepts a prefix but raises when several candidates remain and none is an exact name.
- `graph.addNewNode("Type", name="Name_1", **kwargs)` forwards initial attribute values to the node constructor.
- `src.output.connectTo(dst.input)` is convenient for a single input; nested lists/groups use the target child attribute.
- `graph.configureOutputNodes(["/results"])` sets all exposed output-folder attributes; targeted forms are described in the CLI sub-skill.

## Serialization and Templates

```python
from meshroom.core.graph import Graph, loadGraph

path = "scene.mg"
graph.save(path)
loaded = loadGraph(path, strictCompatibility=False)
loaded.save(template=True)
```

Use a template when the file should retain only non-default configuration and graph topology. A template should not be treated as a computed cache: outputs, UIDs, and runtime chunk state are deliberately removed.

`saveAsNewVersion()` increments an existing scene filename without overwriting the current version. `saveAsTemp(tmpFolder)` is useful for UI or short-lived graph generation.

## Compatibility and Upgrade Workflow

1. Load with `strictCompatibility=False` if you want to inspect the graph even when a node type is missing or changed.
2. Inspect `graph.compatibilityNodes`, each node's `issue`, `issueDetails`, and `canUpgrade`.
3. Load the missing plugin or current descriptor first.
4. Call `graph.upgradeNode(name)` only for a node that is known to map safely to the current descriptor. Use `upgradeAllNodes()` only when the whole graph has been reviewed.
5. Save to a new version and re-open with `strictCompatibility=True` to turn remaining issues into an explicit error.

Do not silently replace an unknown node type with a guessed descriptor: saved list/group values and output expressions may not be compatible.

## Execution Order and Local Compute

For a graph with a selected leaf or output node:

```python
nodes, edges = graph.dfsToProcess(startNodes=[targetNode])
print([node.name for node in nodes])
```

`dfsToProcess` walks dependency edges and excludes successful branches. `executeGraph(graph, toNodes=[targetNode])` then saves the graph, initializes statuses, runs preprocess, creates chunks, processes chunks, and runs postprocess.

Use `forceCompute=True` only when cached success must be discarded. Use `forceStatus=True` only when a status file says RUNNING/SUBMITTED but you have independently confirmed that no valid job is active.

## Cache Directory Workflow

- Default cache is a `MeshroomCache` folder associated with the saved project file.
- `graph.setExplicitCacheDir(path)` persists absolute and relative cache metadata in the graph header.
- CLI `--overrideCacheDir` requires a saved scene because the relative cache location is serialized relative to the scene path.
- After moving a scene and cache together, load and inspect `graph.cacheDir` before computing.

## Minimal Synthetic Graph Check

A safe framework-only check can use `InputString`/`InputInt` or a custom test descriptor that writes a small text file. Avoid AliceVision nodes unless the external binaries and plugin paths are present. Validate:

1. graph save/load preserves node names and descriptor versions;
2. connected inputs read upstream values;
3. changing an invalidating input resets downstream status;
4. a computed node creates a status file under its cache folder;
5. a missing descriptor becomes a compatibility node rather than crashing load.
