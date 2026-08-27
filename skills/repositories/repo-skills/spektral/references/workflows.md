# Root Workflow Map

Use this map to choose the right route before reading detailed references.

## End-to-end Spektral workflow

1. **Represent graph data** with `Graph(x, a, e, y)` objects.
2. **Group graphs** in a `Dataset` subclass or built-in dataset class.
3. **Choose a data mode**: single, disjoint, batch, or mixed.
4. **Select a loader** that matches the mode and label shape.
5. **Apply transforms** such as `GCNFilter`, `LayerPreprocess`, `Degree`, or `OneHotLabels`.
6. **Build a model** from `spektral.layers` or `spektral.models`.
7. **Run a quick smoke check** using the bundled scripts before adapting to real data.

## Route decision table

| User intent | Start here | Why |
| --- | --- | --- |
| Build or inspect `Graph` objects | `sub-skills/graph-data/` | Owns graph schemas, attributes, and shape assumptions |
| Choose between `SingleLoader`, `DisjointLoader`, `BatchLoader`, `MixedLoader` | `sub-skills/graph-data/` | Loader output shapes are data-mode decisions |
| Configure dataset cache or built-in datasets | `sub-skills/graph-data/` | Dataset downloads and `~/.spektral/config.json` are data concerns |
| Apply transforms before a layer | `sub-skills/graph-data/`, then `sub-skills/gnn-models/` | The transform mutates graph data; layer-specific preprocessing belongs to the model route |
| Pick a GNN layer, pooling layer, or ready-made model | `sub-skills/gnn-models/` | Owns mode support, layer signatures, and architecture choices |
| Write a custom message-passing layer | `sub-skills/gnn-models/` | `MessagePassing` has sparse adjacency and single/disjoint constraints |
| Explain a graph or node prediction | `sub-skills/gnn-models/` | `GNNExplainer` is model/explanation behavior |
| Diagnose TensorFlow import, CUDA warnings, or mode/mask errors | `references/troubleshooting.md`, then the owning sub-skill troubleshooting page | Cross-cutting symptoms often need a route-specific fix |

## Bundled checks

- `scripts/check_install.py` checks package imports, versions, and key public signatures.
- `sub-skills/graph-data/scripts/smoke_data_modes.py` exercises tiny in-memory graph datasets through all four loader modes and common transforms.
- `sub-skills/gnn-models/scripts/smoke_models.py` exercises tiny GNN model/layer paths without downloading data or training.

These checks are not replacements for repo-native tests, but they are safe sanity checks for future agents working from a normal installed Spektral package.
