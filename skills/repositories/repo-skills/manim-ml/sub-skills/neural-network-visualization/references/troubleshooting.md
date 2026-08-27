# Neural-Network Troubleshooting

Use this page after ManimML imports successfully. If `manim` itself cannot import or cannot render due to system libraries, fix the Manim Community environment first.

## Quick diagnosis checklist

1. Confirm Manim Community is installed:

   ```bash
   python - <<'PY'
   import manim
   print(getattr(manim, "__version__", "unknown"))
   PY
   ```

2. Confirm ManimML neural-network imports:

   ```bash
   python - <<'PY'
   from manim_ml.neural_network import NeuralNetwork, FeedForwardLayer, Convolutional2DLayer
   print("imports ok")
   PY
   ```

3. Check the helper script without rendering:

   ```bash
   python sub-skills/neural-network-visualization/scripts/render_neural_network_example.py --mode feed-forward --scene-file smoke_scene.py
   ```

4. If rendering is needed, start with a still frame:

   ```bash
   manim -ql -s smoke_scene.py ManimMLNeuralNetworkExample
   ```

## Common exceptions and fixes

| Symptom / exception | Likely cause | Fix |
| --- | --- | --- |
| `ModuleNotFoundError: manim_ml` | ManimML is not installed in the active environment. | Install the package (`pip install manim_ml`) or activate the environment where it is installed. Then rerun a small import check. |
| Manim APIs are missing or examples fail strangely | The original 3Blue1Brown `manim` package is installed instead of Manim Community. | Install Manim Community. The runtime import should be `from manim import *` from the Community package. |
| `AssertionError: Unrecognized activation function ...` | Activation string does not match the small registry. | Use exact names `"ReLU"` or `"Sigmoid"`, or pass a custom `ActivationFunction` instance. |
| `Uncrecognized input layers type` | `NeuralNetwork` was given a tuple, generator, raw node counts, or other unsupported container. | Pass a `list` or `dict` of layer objects. For node counts, use `FeedForwardNeuralNetwork([3, 5, 2])` or create `FeedForwardLayer` objects. |
| `Unrecognized layout direction` | Unsupported `layout_direction`. | Use `"left_to_right"` or `"top_to_bottom"`. |
| `AssertionError` from `add_connection` | Unsupported `connection_style`. | Leave `connection_style="default"`. Control the visual route with `arc_direction`. |
| Warning about unrecognized input/output class pair | Adjacent layer pair has no registered connective layer. | Reorder layers, insert a supported intermediate layer, or accept blank connective behavior and add manual arrows with `nn.add_connection(...)`. |
| `Layer object not found` in `remove_layer` | Removal was called with a new/equivalent layer rather than the exact object inside `nn`. | Keep a reference to the layer object used when constructing the network and pass that same object to `remove_layer`. |
| Middle-layer removal or insertion behaves oddly | Insertion/removal code is less mature than static construction and has incomplete reconnect logic in some cases. | Prefer building the final static network. If animation is required, test the exact small case first and avoid complex automatic reconnects. |
| `replace_layer` fails | The method is not implemented. | Compose `remove_layer` and `insert_layer` manually, or rebuild the network. |

## Image and asset problems

| Symptom | Cause | Fix |
| --- | --- | --- |
| Missing image file | Example copied from a repository-relative path or stale local asset path. | Generate tiny PNGs locally or ask the user for explicit paths. The bundled helper generates fixtures for image/triplet modes. |
| Image layer displays but image-to-CNN animation fails or looks wrong | Channel handling is limited. | Use a 2-D grayscale `uint8` array for `ImageLayer` before a `Convolutional2DLayer`. Convert with `Image.open(path).convert("L")` and `np.asarray(...)`. |
| `ImageLayer.from_path(..., grayscale=True)` does not produce grayscale data | Current method loads the image with Pillow but does not convert mode internally. | Convert explicitly before constructing `ImageLayer`, or use a 2-D array. |
| Triplet/paired-query images are huge | `ImageMobject`/grayscale wrappers may have large visual dimensions before scaling. | Call `triplet_layer.scale(0.2)` or `paired_query_layer.scale(0.25)` before building/placing the network. |
| RGB triplet or paired-query user images fail in a headless render | Image files or codecs are not available, or image dimensions are too large. | Check paths, open each with Pillow first, resize/convert to small PNGs, then pass `grayscale=True` for robust smoke tests or `grayscale=False` only when color is required. |

Safe conversion snippet:

```python
from PIL import Image
import numpy as np
image = np.asarray(Image.open(user_path).convert("L").resize((16, 16)))
layer = ImageLayer(image, height=1.3)
```

## CNN and max-pooling mistakes

- Keep feature-map sizes and filter sizes plausible across adjacent convolutional layers.
- Use `padding=1` and `padding_dashed=True` to show padded borders.
- `MaxPooling2DLayer` infers its output size from the previous convolutional layer. A kernel size that does not divide the visual feature-map size can lead to odd geometry.
- `Convolutional2DLayer` accepts `feature_map_size` and `filter_size` as integers or tuples. Passing `None` may produce incomplete visuals except in cases where a connective layer can infer what is needed.
- Use `ThreeDScene` for CNN scenes; `Scene` may still construct objects, but the examples are designed around 3D-style rotated feature maps.

## Forward-pass and `layer_args` mistakes

`layer_args` is keyed by the layer/connective objects themselves:

```python
embedding = EmbeddingLayer()
nn = NeuralNetwork([FeedForwardLayer(5), embedding, FeedForwardLayer(3)])
self.play(nn.make_forward_pass_animation(layer_args={embedding: {"dist_args": {...}}}))
```

Do not write:

```python
# Wrong: key is a string, not the EmbeddingLayer object.
layer_args={"embedding": {"dist_args": {...}}}
```

For dropout, ManimML internally creates the correct layer arguments. Prefer:

```python
self.play(make_neural_network_dropout_animation(nn, dropout_rate=0.25, seed=4))
```

rather than hand-constructing dropout node/edge indices unless you already understand the internal connective layer order.

## Residual/manual connection mistakes

- Use a dictionary when you want to refer to layers by name.
- `add_connection("a", "b")` adds an extra visual arrow; it does not alter automatic layer sequencing or computation semantics.
- Supported arc directions are `"straight"`, `"up"`, `"down"`, `"left"`, and `"right"`.
- If connecting external dots, create the dots after the network is constructed so layer positions are known.
- Move/scale the whole network after adding manual connections if you want arrows to move with the network.

## Dropout limitations

- Dropout is implemented for feed-forward layers and feed-forward connective edges.
- `dropout_rate` is random unless `seed` is supplied.
- Use `first_layer_stable=True` and `last_layer_stable=True` when input/output layers should remain visible.
- Still-frame rendering may not communicate dropout well; it is usually an animation workflow.

## VAE wrapper caveat

`VariationalAutoencoder` exposes constructor parameters such as `encoder_nodes_per_layer` and `decoder_nodes_per_layer`, but current source builds a fixed internal `NeuralNetwork([FeedForwardLayer(5), FeedForwardLayer(3), EmbeddingLayer(), FeedForwardLayer(3), FeedForwardLayer(5)])`. If exact layer sizes or image inputs/outputs matter, manually assemble a VAE-like `NeuralNetwork` instead.

## Render-time performance tips

- Use the helper script to write scenes first; render only after inspecting the generated code.
- Prefer `manim -ql -s scene.py SceneName` for a quick last-frame check.
- Avoid `-pqh` or high-quality video flags until layout and asset paths are correct.
- Use small arrays/images (`8x8` to `32x32`) for image-layer examples.
- For long animations, start with `run_time=2` to `5`, then increase only when the visual timing is confirmed.

## Known source quirks worth mentioning to users

- `NeuralNetwork` prints a representation during construction.
- Some source warnings about string identity comparison may appear; they usually do not block construction.
- `MaxPooling2DLayer` has a placeholder create override, so creation animation may be minimal even though the layer can appear in a network.
- Color-scheme changes should be made before constructing layers, because default colors are captured at object construction time.
