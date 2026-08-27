# API Reference

## Purpose

Read this when you need the live Python surface for Darkflow rather than only the CLI flags. The API was verified by installing the package and inspecting the runtime signatures in a Python 3.6 environment.

## Public entry points

### `darkflow.defaults.argHandler`

A dict-like flag container with these key methods:

- `setDefaults()` populates the full CLI flag set.
- `parseArgs(args)` parses a `sys.argv`-style list.
- `help()` prints the built-in command help and exits.

`argHandler` is used by the CLI, but it is also convenient for scripted inspection of default values.

### `darkflow.net.build.TFNet`

Verified signature:

```python
TFNet(FLAGS, darknet=None)
```

Important behavior:

- `FLAGS` may be an `argHandler`-style object or a plain dictionary.
- If `FLAGS` is a dictionary, Darkflow wraps it in `argHandler` and applies defaults.
- `darknet=None` is the common case; the class parses the config and loads weights itself.
- If `pbLoad` and `metaLoad` are both present, the class loads the frozen graph path instead of building from a `.cfg` / `.weights` pair.
- `gpu=0.0` keeps the session on CPU; positive values set a TensorFlow GPU memory fraction.

### Useful `TFNet` methods

```python
TFNet.return_predict(self, im)
TFNet.predict(self)
TFNet.train(self)
TFNet.camera(self)
TFNet.savepb(self)
```

Behavior summary:

- `return_predict()` expects a `numpy.ndarray`, not a file path string.
- `predict()` scans `FLAGS.imgdir` for image files and writes results under `imgdir/out/`.
- `train()` consumes parsed Pascal VOC annotations and the selected dataset path.
- `camera()` handles webcam or video-file demos via `FLAGS.demo`.
- `savepb()` writes `built_graph/<model-name>.pb` plus a matching `.meta` JSON file.

## Prediction return shape

`return_predict()` returns a list of dictionaries shaped like:

```python
{
    "label": "person",
    "confidence": 0.82,
    "topleft": {"x": 189, "y": 96},
    "bottomright": {"x": 271, "y": 380}
}
```

The CLI JSON mode uses the same shape.

## Runtime notes worth remembering

- `darkflow.version.__version__` is the package version source.
- `darkflow.__init__` is intentionally minimal; do not expect the version to be re-exported there.
- The installed package was inspected with `inspect.signature()` and a live `flow --help` run, so the signatures above are not guesses.
- The class emits TensorFlow 1.x warnings under Python 3.6 in the verified environment; they were benign during inspection.

## When to read next

- Use `cli-reference.md` for the full flag table.
- Use `model-overview.md` for bundled model families and label selection rules.
- Use `../sub-skills/inference/SKILL.md` for end-user prediction and export workflows.
- Use `../sub-skills/training/SKILL.md` for training-specific API and data preparation details.
