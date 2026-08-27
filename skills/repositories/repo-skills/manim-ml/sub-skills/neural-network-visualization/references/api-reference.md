# ManimML Neural-Network API Reference

This reference summarizes public neural-network APIs verified from package source, examples, tests, and signature probes. Import most classes from `manim_ml.neural_network` unless a deeper module is explicitly needed.

```python
from manim_ml.neural_network import (
    NeuralNetwork,
    FeedForwardLayer,
    Convolutional2DLayer,
    MaxPooling2DLayer,
    ImageLayer,
    EmbeddingLayer,
    PairedQueryLayer,
    TripletLayer,
    VectorLayer,
    MathOperationLayer,
)
from manim_ml.neural_network.animations.dropout import make_neural_network_dropout_animation
from manim_ml.neural_network.architectures.feed_forward import FeedForwardNeuralNetwork
from manim_ml.neural_network.architectures.variational_autoencoder import VariationalAutoencoder
```

## `NeuralNetwork` container

Signature:

```python
NeuralNetwork(
    input_layers,
    layer_spacing=0.2,
    animation_dot_color=..., edge_width=2.5, dot_radius=0.03,
    title=" ", layout="linear", layout_direction="left_to_right",
    debug_mode=False,
)
```

Accepted `input_layers`:

- `list`: sequential layer order; ManimML creates internal names like `layer0`, `layer1`, ...
- `dict`: preserves user keys in `nn.input_layers_dict`; use this form for residual/manual connections.

Important methods:

```python
nn.make_forward_pass_animation(
    run_time=None,
    passing_flash=True,
    layer_args={},
    per_layer_animations=False,
    **kwargs,
)
nn.add_connection(start_mobject_or_name, end_mobject_or_name,
                  connection_style="default",
                  connection_position="bottom",
                  arc_direction="down")
nn.insert_layer(layer, insert_index)
nn.remove_layer(layer)
nn.filter_layers(lambda layer: ...)
```

Notes:

- `layout_direction` is implemented for `"left_to_right"` and `"top_to_bottom"`.
- `layout` is currently a linear-layout placeholder; do not promise graph/auto-layout behavior.
- `make_forward_pass_animation(per_layer_animations=True)` returns a map from each layer/connective object to its animation.
- `layer_args` keys are object instances already in the network, not string names.
- `add_connection` supports only `connection_style="default"`; valid `arc_direction` values are `"straight"`, `"up"`, `"down"`, `"left"`, and `"right"`.
- `replace_layer` is not implemented.
- Construction prints a textual network representation by design; this is noisy but not normally fatal.

## Layer constructor map

| Layer | Signature / key parameters | Use |
| --- | --- | --- |
| `FeedForwardLayer` | `FeedForwardLayer(num_nodes, layer_buffer=..., node_radius=0.08, node_spacing=0.3, activation_function=None, **kwargs)` | Dense node columns. Pass `activation_function="ReLU"` or `"Sigmoid"` to draw/evaluate an activation plot. |
| `Convolutional2DLayer` | `Convolutional2DLayer(num_feature_maps, feature_map_size=None, filter_size=None, cell_width=0.2, filter_spacing=0.1, stride=1, activation_function=None, padding=0, padding_dashed=True, **kwargs)` | 3D-style feature-map stacks. `feature_map_size`, `filter_size`, and `padding` can be ints; padding may also be a two-tuple. |
| `MaxPooling2DLayer` | `MaxPooling2DLayer(kernel_size=2, stride=1, cell_width=0.2, filter_spacing=0.1, **kwargs)` | Max-pool layer after a convolutional layer. Output feature-map size is inferred from the previous convolutional layer. |
| `ImageLayer` | `ImageLayer(numpy_image, height=1.5, show_image_on_create=True, **kwargs)` and `ImageLayer.from_path(image_path, grayscale=True, **kwargs)` | Image input/output layer. 2-D arrays are grayscale; 3-D arrays are treated as RGB image data. |
| `EmbeddingLayer` | `EmbeddingLayer(point_radius=0.02, mean=np.array([0, 0]), covariance=np.eye(2), dist_theme="gaussian", paired_query_mode=False, **kwargs)` | 2-D latent space with Gaussian point cloud and optional distribution animation. Set `paired_query_mode=True` for paired-query distributions. |
| `PairedQueryLayer` | `PairedQueryLayer(positive, negative, stroke_width=5, font_size=18, spacing=0.5, **kwargs)` and `PairedQueryLayer.from_paths(positive_path, negative_path, grayscale=True, **kwargs)` | Two labeled images, usually positive/negative query images feeding a dense network. |
| `TripletLayer` | `TripletLayer(anchor, positive, negative, stroke_width=5, font_size=22, buff=0.2, **kwargs)` and `TripletLayer.from_paths(anchor_path, positive_path, negative_path, grayscale=True, ...)` | Anchor/positive/negative image stack feeding a dense network. |
| `VectorLayer` | `VectorLayer(num_values, value_func=lambda: random.uniform(0, 1), **kwargs)` | Compact vector/probability display, used in GAN-style diagrams. Current display shows a single formatted sampled value. |
| `MathOperationLayer` | `MathOperationLayer(operation_type, node_radius=0.5, activation_function=None, font_size=20, **kwargs)` | Operation node for residual/addition diagrams. Valid operations are `+`, `-`, `*`, and `/`. |

Layer titles: all neural-network layers inherit optional `title="..."` support from the parent layer class.

## Activation functions

Only these activation string names are registered:

```python
FeedForwardLayer(3, activation_function="ReLU")
Convolutional2DLayer(3, 5, 3, activation_function="Sigmoid")
MathOperationLayer("+", activation_function="ReLU")
```

Any other string triggers `AssertionError: Unrecognized activation function ...`. For custom activations, pass an `ActivationFunction` subclass instance rather than a string.

## Automatic connective layers

`NeuralNetwork` inserts connective layers between adjacent input layers using pair dispatch. Supported pairs include:

| Input layer | Output layer | Connective behavior |
| --- | --- | --- |
| `FeedForwardLayer` | `FeedForwardLayer` | Fully connected edge set with passing-flash or dot animation. |
| `FeedForwardLayer` | `EmbeddingLayer` | Dense-to-embedding connective. |
| `EmbeddingLayer` | `FeedForwardLayer` | Embedding-to-dense connective. |
| `FeedForwardLayer` | `ImageLayer` | Dense-to-image connective. |
| `ImageLayer` | `FeedForwardLayer` | Image-to-dense connective. |
| `PairedQueryLayer` | `FeedForwardLayer` | Query image stack to dense connective. |
| `TripletLayer` | `FeedForwardLayer` | Triplet image stack to dense connective. |
| `FeedForwardLayer` | `VectorLayer` | Dense-to-vector connective. |
| `FeedForwardLayer` | `MathOperationLayer` | Dense-to-operation connective. |
| `Convolutional2DLayer` | `Convolutional2DLayer` | Convolution filter/path animation. |
| `ImageLayer` | `Convolutional2DLayer` | Image-to-convolution animation; safest with 2-D grayscale image arrays. |
| `Convolutional2DLayer` | `FeedForwardLayer` | Flatten-style convolution-to-dense connective. |
| `Convolutional2DLayer` | `MaxPooling2DLayer` | Convolution-to-max-pool connective. |
| `MaxPooling2DLayer` | `Convolutional2DLayer` | Max-pool-to-convolution connective. |
| `MaxPooling2DLayer` | `FeedForwardLayer` | Max-pool-to-dense connective. |

Unsupported adjacent pairs fall back to a blank connective and issue a warning. If a visual edge is required for an unsupported pair, use `nn.add_connection(...)` manually and test a still render.

## Forward-pass animation details

Basic call:

```python
forward_pass = nn.make_forward_pass_animation(run_time=5)
self.play(forward_pass)
```

Embedding distribution arguments:

```python
embedding = EmbeddingLayer(dist_theme="ellipse")
nn = NeuralNetwork([FeedForwardLayer(5), embedding, FeedForwardLayer(3)])
self.play(nn.make_forward_pass_animation(layer_args={
    embedding: {
        "dist_args": {
            "mean": np.array([0.5, 0.5]),
            "cov": np.array([[0.4, 0.0], [0.0, 0.2]]),
            "dist_theme": "ellipse",
            "color": BLUE,
        },
        "scale_factor": 1.0,
    }
}))
```

Triplet embedding arguments use `"triplet_args"` with `"anchor_dist"`, `"positive_dist"`, and `"negative_dist"`. Paired-query embedding mode requires `"positive_dist_args"` and `"negative_dist_args"`.

## Dropout animation

Signature:

```python
make_neural_network_dropout_animation(
    neural_network,
    dropout_rate=0.5,
    do_forward_pass=True,
    last_layer_stable=False,
    first_layer_stable=False,
    seed=None,
)
```

Dropout operates on `FeedForwardLayer` objects and `FeedForwardToFeedForward` edges. Use `seed` for deterministic visuals, and set `first_layer_stable=True` or `last_layer_stable=True` when input/output nodes should not be crossed out.

## Architecture wrappers

```python
FeedForwardNeuralNetwork(layer_node_count, node_radius=0.08, node_color=..., **kwargs)
```

This is a convenience wrapper that converts a node-count list into `FeedForwardLayer` objects and calls `NeuralNetwork`.

```python
VariationalAutoencoder(
    encoder_nodes_per_layer=[5, 3],
    decoder_nodes_per_layer=[3, 5],
    point_color=..., dot_radius=0.05,
    ellipse_stroke_width=1.0,
    layer_spacing=0.5,
)
```

Current source constructs a fixed visual network `[5, 3, EmbeddingLayer(), 3, 5]` internally; the constructor node-count parameters are stored but not used to build the layer sizes. For production scenes, prefer a manually assembled `NeuralNetwork([ImageLayer(...), FeedForwardLayer(...), EmbeddingLayer(...), ...])` when exact architecture sizes matter.

## Image and fixture behavior

- `ImageLayer(numpy_image)` accepts a NumPy array. Use 2-D `uint8` arrays for robust grayscale workflows.
- `ImageLayer.from_path(path)` loads with Pillow and returns an `ImageLayer`; the current method accepts a `grayscale` argument but does not convert the image to grayscale internally.
- `TripletLayer.from_paths(...)` and `PairedQueryLayer.from_paths(...)` accept `grayscale=True` to wrap images in `GrayscaleImageMobject`; set `grayscale=False` for color `ImageMobject` inputs.
- Keep generated examples asset-free by creating tiny fixtures at runtime or asking the user for explicit image paths.

## Insertion and removal animations

```python
hidden = FeedForwardLayer(4)
self.play(nn.insert_layer(hidden, insert_index=2))
self.play(nn.remove_layer(hidden))
```

These APIs return Manim animations. Test them in a small scene before using them in a long video; current source has incomplete reconnect logic in some edge cases, especially when removing middle layers with automatic connective replacement.
