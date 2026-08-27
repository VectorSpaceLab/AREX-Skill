# ManimML Neural-Network Workflows

Use these recipes as safe starting points for new ManimML neural-network scenes. They assume `manim_ml` and Manim Community are installed in the active Python environment.

## 1. Minimal feed-forward scene

```python
from manim import *
from manim_ml.neural_network import NeuralNetwork, FeedForwardLayer

config.pixel_height = 720
config.pixel_width = 1280
config.frame_height = 5.0
config.frame_width = 5.0

class FeedForwardScene(Scene):
    def construct(self):
        nn = NeuralNetwork([
            FeedForwardLayer(3),
            FeedForwardLayer(5, activation_function="ReLU"),
            FeedForwardLayer(2, activation_function="Sigmoid"),
        ])
        nn.move_to(ORIGIN)
        self.add(nn)
        self.play(nn.make_forward_pass_animation(run_time=3))
```

Fast still render:

```bash
manim -ql -s my_scene.py FeedForwardScene
```

Full low-quality animation:

```bash
manim -ql my_scene.py FeedForwardScene
```

Convenience wrapper alternative:

```python
from manim_ml.neural_network.architectures.feed_forward import FeedForwardNeuralNetwork
nn = FeedForwardNeuralNetwork([3, 5, 2], layer_spacing=0.25)
```

## 2. CNN, padding, max pooling, and activation functions

Use `ThreeDScene` for convolutional feature-map stacks.

```python
from manim import *
from manim_ml.neural_network import (
    NeuralNetwork, Convolutional2DLayer, MaxPooling2DLayer, FeedForwardLayer,
)

class CNNScene(ThreeDScene):
    def construct(self):
        nn = NeuralNetwork([
            Convolutional2DLayer(1, 8, 3, padding=1, padding_dashed=True, filter_spacing=0.32),
            Convolutional2DLayer(3, 6, 3, activation_function="ReLU", filter_spacing=0.25),
            MaxPooling2DLayer(kernel_size=2),
            Convolutional2DLayer(5, 3, 2, filter_spacing=0.18),
            FeedForwardLayer(4, activation_function="Sigmoid"),
            FeedForwardLayer(2),
        ], layer_spacing=0.25)
        nn.move_to(ORIGIN)
        self.add(nn)
        self.play(nn.make_forward_pass_animation(run_time=6))
```

Sizing rule: keep adjacent convolution/max-pooling feature-map sizes coherent. For example, a `Convolutional2DLayer(..., feature_map_size=6)` followed by `MaxPooling2DLayer(kernel_size=2)` creates a visual output size of `3`, so the next convolution should be sized around that result.

## 3. Image-to-CNN without external assets

Generate a tiny grayscale array or a tiny local PNG. Grayscale is the safest mode for the image-to-convolution animation path.

```python
import numpy as np
from manim import *
from manim_ml.neural_network import NeuralNetwork, ImageLayer, Convolutional2DLayer, FeedForwardLayer

class ImageCNNScene(ThreeDScene):
    def construct(self):
        image = np.array([
            [0, 0, 30, 80, 80, 30, 0, 0],
            [0, 60, 180, 255, 255, 180, 60, 0],
            [30, 180, 255, 180, 180, 255, 180, 30],
            [80, 255, 180, 40, 40, 180, 255, 80],
            [80, 255, 180, 40, 40, 180, 255, 80],
            [30, 180, 255, 180, 180, 255, 180, 30],
            [0, 60, 180, 255, 255, 180, 60, 0],
            [0, 0, 30, 80, 80, 30, 0, 0],
        ], dtype=np.uint8)
        nn = NeuralNetwork([
            ImageLayer(image, height=1.3),
            Convolutional2DLayer(1, 8, 3, filter_spacing=0.32),
            Convolutional2DLayer(3, 6, 3, filter_spacing=0.25),
            FeedForwardLayer(3),
        ], layer_spacing=0.25)
        nn.move_to(ORIGIN)
        self.add(nn)
        self.play(nn.make_forward_pass_animation(run_time=5))
```

If the user gives an image path, convert it explicitly:

```python
from PIL import Image
image = np.asarray(Image.open(user_image_path).convert("L"))
layer = ImageLayer(image, height=1.5)
```

## 4. Residual and skip connections

Use a dictionary when layer names need to be referenced later. Manual connections draw extra arrows; they do not change the automatically inserted connective layers.

```python
from manim import *
from manim_ml.neural_network import NeuralNetwork, FeedForwardLayer, MathOperationLayer

class ResidualScene(Scene):
    def construct(self):
        nn = NeuralNetwork({
            "input": FeedForwardLayer(3),
            "hidden": FeedForwardLayer(3, activation_function="ReLU"),
            "main": FeedForwardLayer(3),
            "sum": MathOperationLayer("+", activation_function="ReLU"),
        }, layer_spacing=0.38)
        nn.add_connection("input", "sum", arc_direction="down")

        # Optional external input/output arrows.
        left_dot = Dot(nn.input_layers_dict["input"].get_left() + LEFT * 0.6)
        right_dot = Dot(nn.input_layers_dict["sum"].get_right() + RIGHT * 0.6)
        nn.add_connection(left_dot, "input", arc_direction="straight")
        nn.add_connection("sum", right_dot, arc_direction="straight")

        nn.move_to(ORIGIN)
        self.add(nn)
        self.play(nn.make_forward_pass_animation(run_time=5))
```

For convolutional residual blocks, keep feature-map dimensions consistent:

```python
nn = NeuralNetwork({
    "conv1": Convolutional2DLayer(1, 5, padding=1),
    "conv2": Convolutional2DLayer(1, 5, 3, padding=1),
    "conv3": Convolutional2DLayer(1, 5, 3, padding=1),
}, layer_spacing=0.25)
nn.add_connection("conv1", "conv3", arc_direction="down")
```

## 5. Dropout animation

```python
from manim import *
from manim_ml.neural_network import NeuralNetwork, FeedForwardLayer
from manim_ml.neural_network.animations.dropout import make_neural_network_dropout_animation

class DropoutScene(Scene):
    def construct(self):
        nn = NeuralNetwork([
            FeedForwardLayer(3),
            FeedForwardLayer(5),
            FeedForwardLayer(3),
            FeedForwardLayer(5),
            FeedForwardLayer(4),
        ], layer_spacing=0.4)
        nn.move_to(ORIGIN)
        self.add(nn)
        self.play(make_neural_network_dropout_animation(
            nn,
            dropout_rate=0.25,
            do_forward_pass=True,
            first_layer_stable=True,
            last_layer_stable=True,
            seed=4,
        ))
```

Dropout only targets feed-forward layers and feed-forward-to-feed-forward edges. It is not a CNN dropout visualizer.

## 6. Embedding and latent-distribution animation

```python
from manim import *
import numpy as np
from manim_ml.neural_network import NeuralNetwork, FeedForwardLayer, EmbeddingLayer

class EmbeddingScene(Scene):
    def construct(self):
        embedding = EmbeddingLayer(dist_theme="ellipse")
        nn = NeuralNetwork([
            FeedForwardLayer(5),
            FeedForwardLayer(3),
            embedding,
            FeedForwardLayer(3),
        ])
        self.add(nn)
        self.play(nn.make_forward_pass_animation(layer_args={
            embedding: {
                "dist_args": {
                    "mean": np.array([0.6, -0.2]),
                    "cov": np.array([[0.5, 0.0], [0.0, 0.25]]),
                    "dist_theme": "ellipse",
                    "color": BLUE,
                },
                "scale_factor": 1.0,
            }
        }, run_time=5))
```

Triplet embedding animation arguments:

```python
self.play(nn.make_forward_pass_animation(layer_args={
    embedding: {
        "triplet_args": {
            "anchor_dist": {"mean": np.array([0.7, 1.2]), "cov": np.eye(2) * 0.2, "dist_theme": "ellipse", "color": BLUE},
            "positive_dist": {"mean": np.array([0.8, -0.4]), "cov": np.eye(2) * 0.2, "dist_theme": "ellipse", "color": GREEN},
            "negative_dist": {"mean": np.array([-1.0, -1.2]), "cov": np.eye(2) * 0.3, "dist_theme": "ellipse", "color": RED},
        }
    }
}))
```

Paired-query embedding mode:

```python
embedding = EmbeddingLayer(paired_query_mode=True)
# later in make_forward_pass_animation(layer_args={embedding: {...}})
{
    "positive_dist_args": {"mean": np.array([1, 1]), "cov": np.eye(2), "color": GREEN},
    "negative_dist_args": {"mean": np.array([-1, -1]), "cov": np.eye(2), "color": RED},
}
```

## 7. Triplet and paired-query image workflows

Use generated tiny fixture images or user-provided paths. Scale image-stack layers down before adding dense layers.

```python
from manim import *
from manim_ml.neural_network import NeuralNetwork, FeedForwardLayer, TripletLayer

class TripletScene(Scene):
    def construct(self):
        triplet = TripletLayer.from_paths(
            "anchor.png", "positive.png", "negative.png",
            grayscale=True,
            font_size=18,
        )
        triplet.scale(0.22)
        nn = NeuralNetwork([triplet, FeedForwardLayer(5), FeedForwardLayer(3)])
        nn.move_to(ORIGIN)
        self.add(nn)
        self.play(nn.make_forward_pass_animation(run_time=4))
```

Paired-query variant:

```python
from manim_ml.neural_network import PairedQueryLayer
query = PairedQueryLayer.from_paths("positive.png", "negative.png", grayscale=True)
query.scale(0.25)
nn = NeuralNetwork([query, FeedForwardLayer(5), FeedForwardLayer(3)])
```

## 8. Vector, math, GAN-style, and VAE-style compositions

Vector/probability ending:

```python
from manim_ml.neural_network import VectorLayer
nn = NeuralNetwork([FeedForwardLayer(5), FeedForwardLayer(1), VectorLayer(1)])
```

Math-operation node:

```python
nn = NeuralNetwork([FeedForwardLayer(3), MathOperationLayer("+", activation_function="ReLU")])
```

VAE-style visual network with exact layer sizes:

```python
nn = NeuralNetwork([
    ImageLayer(input_image, height=1.2),
    FeedForwardLayer(5),
    FeedForwardLayer(3),
    EmbeddingLayer(dist_theme="ellipse"),
    FeedForwardLayer(3),
    FeedForwardLayer(5),
    ImageLayer(output_image, height=1.2),
], layer_spacing=0.1)
```

Use the `VariationalAutoencoder` wrapper only when its fixed internal `[5, 3, embedding, 3, 5]` visual structure is acceptable.

## 9. Layer insertion and removal

Keep direct references to layers that may be inserted or removed.

```python
middle = FeedForwardLayer(5)
nn = NeuralNetwork([
    FeedForwardLayer(3),
    middle,
    FeedForwardLayer(2),
])
self.play(Create(nn))
self.play(nn.remove_layer(middle))

new_middle = FeedForwardLayer(4)
self.play(nn.insert_layer(new_middle, insert_index=2))
```

Caution: insertion/removal APIs are animation helpers and are less mature than static network construction. Test the exact case with a low-quality still or short render before building a long scene around it.

## 10. Bundled helper script workflows

Write a standalone scene without rendering:

```bash
python sub-skills/neural-network-visualization/scripts/render_neural_network_example.py \
  --mode residual \
  --scene-file residual_scene.py
```

Render a still frame after writing:

```bash
python sub-skills/neural-network-visualization/scripts/render_neural_network_example.py \
  --mode image-cnn \
  --scene-file image_cnn_scene.py \
  --render \
  --still
```

Generate assets for triplet or paired-query examples:

```bash
python sub-skills/neural-network-visualization/scripts/render_neural_network_example.py \
  --mode triplet \
  --scene-file triplet_scene.py \
  --assets-dir ./tiny_triplet_assets
```

Available helper modes:

```text
feed-forward, cnn, image-cnn, residual, dropout, embedding, triplet, paired-query, vector-math, vae
```

By default the generated scenes draw the network only. Add `--animate-scene` if the generated scene should include `self.play(...)` calls. Add `--render` only when the active environment has a working Manim render stack.
