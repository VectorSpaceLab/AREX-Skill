# Core Graph API Reference

## When to Read

Use this for Meshroom core objects and signatures that are stable enough for agents to reason about graph construction, serialization, compatibility, and execution.

## Package Initialization

```python
import meshroom
meshroom.setupEnvironment()  # standalone backend by default
import meshroom.core
meshroom.core.initNodes()
```

`meshroom.setupEnvironment(backend=Backend.STANDALONE)` selects the headless common-object backend. `Backend.PYSIDE` is used by the UI.

## Graph Objects

Verified signatures:

```text
Graph(name: str = '', parent=None)
loadGraph(filepath, strictCompatibility: bool = False) -> Graph
executeGraph(graph, toNodes=None, forceCompute=False, forceStatus=False)
submit(graphFile, submitter, toNode=None, submitLabel='{projectName}')
```

Useful `Graph` methods:

| API | Purpose |
| --- | --- |
| `addNewNode(nodeType, name=None, position=None, **kwargs)` | Instantiate a registered node type and initialize attributes from keyword values. Duplicate explicit names are uniquified. |
| `node(name)` | Return the exact node instance or `None`. |
| `findNode(expr)` / `findNodes(exprs)` | Find by prefix expression; raises on no match or ambiguous non-exact match. |
| `nodesOfType(nodeType, sortedByIndex=True)` | Return instances of a node type, sorted by suffix index by default. |
| `addEdge(srcAttr, dstAttr)` | Connect an output to an input after type validation; replaces an existing input edge. |
| `removeEdge(dstAttr)` | Remove the incoming edge to an input attribute. |
| `findInputNodes()` / `findOutputNodes()` | Return nodes whose descriptors mix in `InputNode` or `OutputNode`. |
| `configureOutputNodes(outputValues)` | Apply `meshroom_batch --output` forms to all or targeted output nodes. |
| `dfsOnFinish(...)` / `dfsOnDiscover(...)` | Inspect dependencies or downstream nodes in deterministic traversal order. |
| `dfsToProcess(startNodes=None)` | Return nodes/edges that still need computation, skipping successful branches. |
| `save(filepath=None, setupProjectFile=True, template=False)` | Write a `.mg` graph or template. |
| `saveAsTemp(tmpFolder=None)` | Save a graph to a generated temporary `.mg` path. |
| `saveAsNewVersion()` | Save next numbered version beside the current graph file. |
| `load(path)` / `loadGraph(path, strictCompatibility=False)` | Load `.mg` data and update graph topology/status. |
| `importGraphContent(otherGraph)` / `importGraphContentFromFile(path)` | Copy nodes/edges into another graph, remapping names and compatibility nodes as needed. |
| `setExplicitCacheDir(path)` | Store and persist an explicit cache directory. |
| `upgradeNode(nodeName)` / `upgradeAllNodes()` | Replace upgradable `CompatibilityNode` instances with current descriptors. |

## Attributes and Edges

- Edges connect a source output `Attribute` to a destination input `Attribute`.
- The graph uses the destination attribute as the unique edge key because each input can have only one incoming edge.
- `Attribute.value` on a linked input resolves through the input link.
- File/string expression values may use environment substitution and node variables such as `{nodeCacheFolder}`.
- `AnySet`, `ListAttribute`, and `GroupAttribute` preserve nested values and links during serialization when possible.

Common attribute access:

```python
node.attribute("param")
node.hasAttribute("param")
graph.attribute("Node_1.param")
graph.anyAttribute("Node_1.internalFolder")
node.output.connectTo(other.input)
```

## Node Status and Chunks

Relevant enums:

```text
Status: NONE, SUBMITTED, RUNNING, ERROR, STOPPED, KILLED, SUCCESS, INIT
ExecMode: NONE, LOCAL, EXTERN
ChunkIndex: NONE=-3, PREPROCESS=-2, POSTPROCESS=-1, standard chunks >= 0
```

Useful node methods:

| API | Purpose |
| --- | --- |
| `evaluateSize()` | Resolve static/dynamic/callable descriptor size. |
| `createChunks()` | Create chunk objects based on size and `parallelization`. |
| `preprocess(forceCompute=False, inCurrentEnv=False)` | Run descriptor preprocess and update status. |
| `process(forceCompute=False, inCurrentEnv=False)` | Run one or more chunks. |
| `postprocess(forceCompute=False, inCurrentEnv=False)` | Run descriptor postprocess and update global status. |
| `updateStatusFromCache()` | Refresh node/chunk status from cache status files. |
| `initStatusOnCompute(forceCompute=False)` | Reset status before local compute. |
| `initStatusOnSubmit(forceCompute=False)` | Mark status for submitter-managed compute. |
| `getGlobalStatus()` | Return combined node status across chunks. |

`Node.processChunkInEnvironment()` wraps a `meshroom_compute` invocation to run Python node logic in a plugin-specific runtime environment. `CommandLineNode` descriptors instead build and execute their command-line template.

## Graph Serialization

`.mg` files contain:

- `header.releaseVersion`: Meshroom version used to save.
- `header.fileVersion`: graph file format version.
- `header.nodesVersions`: registered node type versions used in the graph.
- `header.template`: present and true for template saves.
- `header.cacheDir`: explicit cache metadata when configured.
- `graph`: node payload keyed by node instance name.

Serializer types:

| Serializer | Use |
| --- | --- |
| `GraphSerializer` | Full graph save with inputs, outputs, UIDs, internal attributes, and cache metadata. |
| `TemplateGraphSerializer` | Template save; drops default inputs/internal values plus runtime outputs, UIDs, and parallelization data. |
| `PartialGraphSerializer` | Serialize a subset of nodes and remove links to nodes outside the subset. |

## Compatibility Nodes

When loading old or incomplete graph data, `nodeFactory` may create `CompatibilityNode` instead of a normal `Node`. Typical issues:

- unknown node type because the plugin is missing;
- major node descriptor version conflict;
- descriptor shape conflict because a saved attribute no longer matches current descriptor schema;
- UID conflict after descriptor/output defaults changed.

Do not compute compatibility nodes. Load missing plugins or upgrade only when the current descriptor can safely accept saved data.
