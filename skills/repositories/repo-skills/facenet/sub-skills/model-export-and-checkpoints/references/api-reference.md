# Model export API reference

## Loading models

```python
facenet.load_model(model, input_map=None)
```

- `model` may be a checkpoint directory or a `.pb` file.
- `input_map` can substitute tensors when importing a frozen graph or checkpoint graph into an existing graph.

```python
facenet.get_model_filenames(model_dir)
```

Returns `(meta_file, ckpt_file)`.

```python
facenet.list_variables(filename)
```

Returns sorted variable names from a checkpoint file.

## Freeze graph script

`src/freeze_graph.py`:

- loads a checkpoint directory,
- restores variables,
- converts selected variables to constants,
- writes the resulting GraphDef to an output file.

The exported graph keeps nodes related to `InceptionResnet*`, `embeddings`, `image_batch`, `label_batch`, `phase_train`, and `Logits`.
