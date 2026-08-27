# General Utility Nodes

Meshroom's built-in general nodes are useful examples and small graph utilities. They are available after built-in node initialization; external AliceVision nodes are not required for these patterns.

| Node family | Use | Important behavior |
| --- | --- | --- |
| `InputString`, `InputInt`, `InputFile` | Feed values into a graph from CLI/UI | `InputFile` validates direct/recursive paths and uses only the first valid input. |
| `CopyFiles` | Copy files/folders to an output folder | Dynamic size follows `inputFiles`; it is an `OutputNode` and creates the destination when needed. |
| `FlattenFiles` | Flatten list-of-lists into one file list | Output is dynamic and preserves input order. |
| `GetParentFolder`, `PathJoin` | Path manipulation | Validate empty/nonexistent paths before using them downstream. |
| `ReadEnvironmentVariable` | Read an environment variable into a graph value | Empty variable names produce an empty output. |
| `MeshroomSceneParameter` | Build input/parameter override strings | `node_instance` uses `.`; `node_type` uses `:`. Empty name/value produces no override. |
| `GenerateMeshroomScene`, `ComputeMeshroomScene` | Generate/save/compute or submit a scene from a graph | They invoke Meshroom CLIs and therefore need a valid Python environment and any selected submitter. |
| `GetMeshroomSceneParams`, `UnwrapMeshroomSceneParam` | Extract and reuse values from another scene | Parameter paths may include group/list traversal; missing scene/params can be configured to fail or return empty values. |
| `Backdrop` | Visual grouping | No computation; it groups nodes in the graph editor. |

When using these nodes in a template, keep external binary dependencies explicit and test the template with a tiny fixture graph before connecting a full photogrammetry pipeline.
