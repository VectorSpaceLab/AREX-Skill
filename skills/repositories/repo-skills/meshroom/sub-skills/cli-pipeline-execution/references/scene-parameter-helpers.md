# Scene Parameter Helpers

## `extract_scene_params.py`

The bundled helper is adapted from Meshroom's general scene-parameter script. It reads a `.mg` scene and writes JSON entries with:

```json
[
  {"node": "Node_1", "parameter": "group.value", "value": "..."}
]
```

Run:

```bash
python scripts/extract_scene_params.py \
  --scene input.mg \
  --request 'Node_1:param;Node_2:group.value' \
  --output values.json \
  --fail-on-missing-params
```

Requests are semicolon-separated `nodeInstance:paramPath` pairs. Parameter paths can address nested group fields and list elements using the Meshroom attribute path syntax. Use `--fail-on-missing-scene` when a missing scene is an error; otherwise the helper can write an empty JSON list/object according to its mode.

## Node-Based Composition

- `GetMeshroomSceneParams` runs the same extraction behavior as a command-line node and writes a cache-local `values.json`.
- `UnwrapMeshroomSceneParam` links to a `GetMeshroomSceneParams` node, builds choices from its requested parameters, and exposes a selected string value.
- `MeshroomSceneParameter` generates the override syntax consumed by `GenerateMeshroomScene` or `--paramOverrides`.
- `GenerateMeshroomScene` configures a template, saves a new scene, and sets `--compute no`; it does not run the generated scene.

## Validation

Before extracting:

1. confirm the scene file exists and is a Meshroom `.mg` JSON file;
2. use exact node instance names unless the helper explicitly supports types;
3. check nested attribute paths against the saved graph;
4. decide whether missing scene/parameter should fail or produce an empty result;
5. keep the generated JSON beside the scene or in a controlled output folder.
