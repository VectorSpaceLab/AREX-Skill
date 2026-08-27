# Example models, serialization, plotting, and CLI routes

## Example-model helpers

### `fetch_example_list()`

Prints the public example-model catalog for the current frontend family. It uses network access and prints the data to stdout.

### `fetch_example_model(model_name, backend='Vivado')`

Downloads one example model into the current working directory and returns a config dictionary for it.

Side effects:

- model files are written into the current directory
- data and config files are downloaded when the catalog says they exist
- Keras `.json` models also download the matching weights file

Safe rule:

- run it in a scratch directory or temp directory
- do not treat it as an offline helper

## Serialization and reload

Converted hls4ml models can be saved and loaded later without the original frontend model.

### Save / load

```python
model.save('my_model.fml')
loaded = hls4ml.converters.load_saved_model('my_model.fml')
```

The `.fml` file is a compressed archive that carries the model graph, config, internal state, version data, and any bundled testbench arrays.

### Existing project link

If a project has already been written to disk, re-open it with:

```python
linked = hls4ml.converters.link_existing_project('project_dir')
```

The linked model only allows `compile()`, `predict()`, and `build()`.

## Plotting

`plot_model()` renders a ModelGraph through pydot and Graphviz.

Useful options:

- `show_shapes=True`
- `show_layer_names=True`
- `show_precision=True`
- `rankdir='TB'` or `rankdir='LR'`

If pydot or Graphviz is missing, the helper fails early instead of silently producing a bad image.

## Deprecated CLI routes

The legacy `hls4ml` CLI still exposes these commands:

- `config`
- `convert`
- `build`
- `report`

For frontend work, use the Python API first. The CLI is only a compatibility layer.

Practical notes:

- legacy `config` is mainly a configuration generator for old-style model files
- `convert` is a thin wrapper around config-driven conversion
- build and report belong to the backend workflow, not this sub-skill

## Modern config file pattern

If you need a file-based config, prefer a config that carries an actual model object and then call the Python converter.

```yaml
KerasModel: !keras_model path/to/model.keras
OutputDir: out
ProjectName: demo
Backend: Vitis
HLSConfig:
  Model:
    Precision: fixed<16,6>
    ReuseFactor: 1
```
