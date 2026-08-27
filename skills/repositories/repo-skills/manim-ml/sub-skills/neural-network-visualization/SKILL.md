---
name: neural-network-visualization
description: "Use this operating sub-skill to create, adapt, and troubleshoot
  ManimML neural-network scenes: NeuralNetwork containers, feed-forward and
  convolutional layers, image/embedding/vector/math/triplet/paired-query layers,
  connective layers, forward-pass animations, dropout, residual/manual
  connections, insertion/removal animations, and small safe render scripts."
disable-model-invocation: true
metadata:
  disco-role: operating
  package: manim_ml
  repo-skill: manim-ml
  sub-skill: neural-network-visualization
license: MIT
---

# Neural-Network Visualization with ManimML

## Use this sub-skill when

- The task is to draw or animate a neural-network architecture with `manim_ml.neural_network`.
- The requested scene involves `NeuralNetwork`, feed-forward layers, convolution/max-pooling/image layers, activation functions, embeddings, vector outputs, math-operation nodes, triplet or paired-query image inputs, VAE-like diagrams, dropout, forward-pass animations, or residual/skip connections.
- The user needs a small script that writes a standalone Manim scene without relying on repository assets.

Route decision-tree, MCMC, Gaussian/probability, and matplotlib/statistical workflows to the sibling statistical-visualization sub-skill. Route Manim Community installation, cairo/Pango/ffmpeg, or system-render failures to the root ManimML troubleshooting reference first, then return here for layer/API mistakes.

## Assumptions and safe operating checks

ManimML scenes require Manim Community, not the original 3Blue1Brown Manim package. Before writing task-specific code, use a small import check in the user's active environment:

```bash
python - <<'PY'
import manim
from manim_ml.neural_network import NeuralNetwork, FeedForwardLayer
print("manim", getattr(manim, "__version__", "unknown"))
print(NeuralNetwork, FeedForwardLayer)
PY
```

For a no-assets starter script, prefer the bundled helper:

```bash
python sub-skills/neural-network-visualization/scripts/render_neural_network_example.py --help
python sub-skills/neural-network-visualization/scripts/render_neural_network_example.py --mode feed-forward --scene-file nn_example.py
manim -ql -s nn_example.py ManimMLNeuralNetworkExample
```

The helper writes a scene by default and renders only when explicitly asked with `--render`.

## Reference map

- [API reference](references/api-reference.md): verified constructors, layer map, connective dispatch, animation calls, wrapper APIs, and known limitations.
- [Workflows](references/workflows.md): copyable recipes for feed-forward, CNN/image-CNN/max-pool, residual connections, dropout, embeddings, triplet/paired-query layers, VAE-style diagrams, insertion/removal, and safe render commands.
- [Troubleshooting](references/troubleshooting.md): common exceptions and fixes for activation names, layouts, connection styles, image shapes, CNN dimensions, dropout, and render mistakes.
- [Safe helper script](scripts/render_neural_network_example.py): generates standalone tiny-scene examples for `feed-forward`, `cnn`, `image-cnn`, `residual`, `dropout`, `embedding`, `triplet`, `paired-query`, `vector-math`, and `vae`.

## Core operating pattern

```python
from manim import *
from manim_ml.neural_network import NeuralNetwork, FeedForwardLayer

class MyScene(Scene):
    def construct(self):
        nn = NeuralNetwork([
            FeedForwardLayer(3),
            FeedForwardLayer(5, activation_function="ReLU"),
            FeedForwardLayer(2),
        ])
        nn.move_to(ORIGIN)
        self.add(nn)
        self.play(nn.make_forward_pass_animation(run_time=3))
```

Use `ThreeDScene` when the network includes `Convolutional2DLayer` or `MaxPooling2DLayer`, because those layers are rendered as rotated 3D-style feature-map stacks.

## Rules of thumb

1. Import most public neural-network classes directly from `manim_ml.neural_network`.
2. Use a list of layer objects for sequential networks and a dictionary of named layer objects when later manual connections should address layers by name.
3. Keep image examples self-contained by generating tiny PNGs or by converting a caller-supplied image with Pillow; do not reference repository-relative assets.
4. Use exact activation names: `"ReLU"` and `"Sigmoid"`.
5. `make_forward_pass_animation(layer_args=...)` keys are layer/connective object instances, not layer names.
6. `add_connection(...)` supports the default connection style; choose `arc_direction="straight"`, `"up"`, `"down"`, `"left"`, or `"right"` for the visual route.
7. Treat full video rendering as optional and potentially slow. For quick checks, render a still with `manim -ql -s`.

## Verification hooks for downstream Researcher tasks

- Minimal construction: build a `NeuralNetwork([FeedForwardLayer(3), FeedForwardLayer(2)])`, add it to a `Scene`, and confirm the scene imports.
- CNN construction: build a `ThreeDScene` with `Convolutional2DLayer`, `MaxPooling2DLayer`, and `FeedForwardLayer`; prefer a still render first.
- Asset-free image paths: use the bundled script's `image-cnn`, `triplet`, or `paired-query` modes to generate tiny fixtures, then render the produced scene file.
