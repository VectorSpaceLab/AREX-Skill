#!/usr/bin/env python3
"""Generate small, asset-safe ManimML neural-network example scenes.

The helper writes a standalone Python scene file by default. It does not render
unless --render is supplied. Modes that need images generate tiny local PNG
fixtures so examples do not depend on repository assets.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from textwrap import dedent
from typing import Dict, Iterable

MODES = (
    "feed-forward",
    "cnn",
    "image-cnn",
    "residual",
    "dropout",
    "embedding",
    "triplet",
    "paired-query",
    "vector-math",
    "vae",
)


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Write compact ManimML neural-network example scenes with no repository asset dependency.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python scripts/render_neural_network_example.py --mode feed-forward --scene-file nn_scene.py\n"
            "  python scripts/render_neural_network_example.py --mode image-cnn --scene-file image_scene.py --animate-scene\n"
            "  python scripts/render_neural_network_example.py --mode triplet --scene-file triplet_scene.py --assets-dir ./tiny_assets\n"
            "  python scripts/render_neural_network_example.py --mode residual --scene-file residual_scene.py --render --still"
        ),
    )
    parser.add_argument("--mode", choices=MODES, default="feed-forward", help="example scene to write")
    parser.add_argument("--scene-file", default="manimml_neural_network_example.py", help="output Python scene file")
    parser.add_argument("--scene-name", default="ManimMLNeuralNetworkExample", help="class name to write/render")
    parser.add_argument("--assets-dir", default="manimml_tiny_assets", help="directory for generated tiny PNG fixtures")
    parser.add_argument("--animate-scene", action="store_true", help="include self.play(...) animation calls in the generated scene")
    parser.add_argument("--render", action="store_true", help="run manim after writing the scene")
    parser.add_argument("--still", action="store_true", help="when rendering, use Manim -s still-frame mode")
    parser.add_argument("--quality", default="-ql", help="Manim quality flag for --render, such as -ql or -qm")
    parser.add_argument("--force", action="store_true", help="overwrite an existing scene file")
    return parser


def _play_or_add(animate: bool, expression: str = "nn.make_forward_pass_animation(run_time=3)") -> str:
    if animate:
        return f"self.play({expression})"
    return "self.add(nn)"


def _common_header() -> str:
    return """from manim import *\nimport numpy as np\n\n"""


def _wrap_scene(scene_name: str, base_class: str, body: str) -> str:
    indented = "\n".join("        " + line if line else "" for line in body.strip().splitlines())
    return f"class {scene_name}({base_class}):\n    def construct(self):\n{indented}\n"


def _tiny_image_array() -> str:
    return """np.array([\n    [0, 0, 30, 80, 80, 30, 0, 0],\n    [0, 60, 180, 255, 255, 180, 60, 0],\n    [30, 180, 255, 180, 180, 255, 180, 30],\n    [80, 255, 180, 40, 40, 180, 255, 80],\n    [80, 255, 180, 40, 40, 180, 255, 80],\n    [30, 180, 255, 180, 180, 255, 180, 30],\n    [0, 60, 180, 255, 255, 180, 60, 0],\n    [0, 0, 30, 80, 80, 30, 0, 0],\n], dtype=np.uint8)"""


def _make_assets(assets_dir: Path, names: Iterable[str]) -> Dict[str, str]:
    try:
        from PIL import Image, ImageDraw
    except ImportError as exc:  # pragma: no cover - import failure UI path
        raise RuntimeError("Pillow is required to generate tiny image fixtures") from exc
    assets_dir.mkdir(parents=True, exist_ok=True)
    palette = {
        "anchor": (70, 130, 180),
        "positive": (60, 179, 113),
        "negative": (220, 80, 70),
        "query-positive": (60, 179, 113),
        "query-negative": (220, 80, 70),
        "input": (70, 130, 180),
        "output": (220, 160, 60),
    }
    result: Dict[str, str] = {}
    for name in names:
        image = Image.new("RGB", (48, 48), palette.get(name, (120, 120, 120)))
        draw = ImageDraw.Draw(image)
        draw.rectangle([(4, 4), (43, 43)], outline=(255, 255, 255), width=2)
        draw.text((8, 18), name[:3].upper(), fill=(255, 255, 255))
        path = assets_dir / f"{name}.png"
        image.save(path)
        result[name] = path.as_posix()
    return result


def scene_source(mode: str, scene_name: str, animate: bool, assets: Dict[str, str]) -> str:
    header = _common_header()
    if mode == "feed-forward":
        body = f"""
from manim_ml.neural_network import NeuralNetwork, FeedForwardLayer
nn = NeuralNetwork([FeedForwardLayer(3), FeedForwardLayer(5, activation_function="ReLU"), FeedForwardLayer(2, activation_function="Sigmoid")])
nn.move_to(ORIGIN)
{_play_or_add(animate)}
"""
        return header + _wrap_scene(scene_name, "Scene", body)
    if mode == "cnn":
        body = f"""
from manim_ml.neural_network import NeuralNetwork, Convolutional2DLayer, MaxPooling2DLayer, FeedForwardLayer
nn = NeuralNetwork([
    Convolutional2DLayer(1, 8, 3, padding=1, padding_dashed=True, filter_spacing=0.32),
    Convolutional2DLayer(3, 6, 3, activation_function="ReLU", filter_spacing=0.25),
    MaxPooling2DLayer(kernel_size=2),
    Convolutional2DLayer(5, 3, 2, filter_spacing=0.18),
    FeedForwardLayer(3),
], layer_spacing=0.25)
nn.move_to(ORIGIN)
{_play_or_add(animate, 'nn.make_forward_pass_animation(run_time=5)')}
"""
        return header + _wrap_scene(scene_name, "ThreeDScene", body)
    if mode == "image-cnn":
        body = f"""
from manim_ml.neural_network import NeuralNetwork, ImageLayer, Convolutional2DLayer, FeedForwardLayer
image = {_tiny_image_array()}
nn = NeuralNetwork([
    ImageLayer(image, height=1.3),
    Convolutional2DLayer(1, 8, 3, filter_spacing=0.32),
    Convolutional2DLayer(3, 6, 3, filter_spacing=0.25),
    FeedForwardLayer(3),
], layer_spacing=0.25)
nn.move_to(ORIGIN)
{_play_or_add(animate, 'nn.make_forward_pass_animation(run_time=5)')}
"""
        return header + _wrap_scene(scene_name, "ThreeDScene", body)
    if mode == "residual":
        body = f"""
from manim_ml.neural_network import NeuralNetwork, FeedForwardLayer, MathOperationLayer
nn = NeuralNetwork({{
    "input": FeedForwardLayer(3),
    "hidden": FeedForwardLayer(3, activation_function="ReLU"),
    "main": FeedForwardLayer(3),
    "sum": MathOperationLayer("+", activation_function="ReLU"),
}}, layer_spacing=0.38)
nn.add_connection("input", "sum", arc_direction="down")
left_dot = Dot(nn.input_layers_dict["input"].get_left() + LEFT * 0.6)
right_dot = Dot(nn.input_layers_dict["sum"].get_right() + RIGHT * 0.6)
nn.add_connection(left_dot, "input", arc_direction="straight")
nn.add_connection("sum", right_dot, arc_direction="straight")
nn.move_to(ORIGIN)
{_play_or_add(animate, 'nn.make_forward_pass_animation(run_time=4)')}
"""
        return header + _wrap_scene(scene_name, "Scene", body)
    if mode == "dropout":
        body = f"""
from manim_ml.neural_network import NeuralNetwork, FeedForwardLayer
from manim_ml.neural_network.animations.dropout import make_neural_network_dropout_animation
nn = NeuralNetwork([FeedForwardLayer(3), FeedForwardLayer(5), FeedForwardLayer(3), FeedForwardLayer(5), FeedForwardLayer(4)], layer_spacing=0.4)
nn.move_to(ORIGIN)
self.add(nn)
{('self.play(make_neural_network_dropout_animation(nn, dropout_rate=0.25, do_forward_pass=True, first_layer_stable=True, last_layer_stable=True, seed=4))' if animate else '# Add --animate-scene to play the dropout animation.')}
"""
        return header + _wrap_scene(scene_name, "Scene", body)
    if mode == "embedding":
        body = f"""
from manim_ml.neural_network import NeuralNetwork, FeedForwardLayer, EmbeddingLayer
embedding = EmbeddingLayer(dist_theme="ellipse")
nn = NeuralNetwork([FeedForwardLayer(5), FeedForwardLayer(3), embedding, FeedForwardLayer(3)])
nn.move_to(ORIGIN)
self.add(nn)
{('self.play(nn.make_forward_pass_animation(layer_args={embedding: {"dist_args": {"mean": np.array([0.6, -0.2]), "cov": np.array([[0.5, 0.0], [0.0, 0.25]]), "dist_theme": "ellipse", "color": BLUE}, "scale_factor": 1.0}}, run_time=4))' if animate else '# Add --animate-scene to play the embedding distribution animation.')}
"""
        return header + _wrap_scene(scene_name, "Scene", body)
    if mode == "triplet":
        body = f"""
from manim_ml.neural_network import NeuralNetwork, FeedForwardLayer, TripletLayer
triplet = TripletLayer.from_paths("{assets['anchor']}", "{assets['positive']}", "{assets['negative']}", grayscale=True, font_size=18)
triplet.scale(0.22)
nn = NeuralNetwork([triplet, FeedForwardLayer(5), FeedForwardLayer(3)])
nn.move_to(ORIGIN)
{_play_or_add(animate, 'nn.make_forward_pass_animation(run_time=4)')}
"""
        return header + _wrap_scene(scene_name, "Scene", body)
    if mode == "paired-query":
        body = f"""
from manim_ml.neural_network import NeuralNetwork, FeedForwardLayer, PairedQueryLayer
query = PairedQueryLayer.from_paths("{assets['query-positive']}", "{assets['query-negative']}", grayscale=True)
query.scale(0.25)
nn = NeuralNetwork([query, FeedForwardLayer(5), FeedForwardLayer(3)])
nn.move_to(ORIGIN)
{_play_or_add(animate, 'nn.make_forward_pass_animation(run_time=4)')}
"""
        return header + _wrap_scene(scene_name, "Scene", body)
    if mode == "vector-math":
        body = f"""
from manim_ml.neural_network import NeuralNetwork, FeedForwardLayer, MathOperationLayer, VectorLayer
nn = NeuralNetwork([FeedForwardLayer(3), MathOperationLayer("+", activation_function="ReLU"), FeedForwardLayer(2), VectorLayer(1)])
nn.move_to(ORIGIN)
{_play_or_add(animate, 'nn.make_forward_pass_animation(run_time=4)')}
"""
        return header + _wrap_scene(scene_name, "Scene", body)
    if mode == "vae":
        body = f"""
from PIL import Image
from manim_ml.neural_network import NeuralNetwork, FeedForwardLayer, ImageLayer, EmbeddingLayer
input_image = np.asarray(Image.open("{assets['input']}").convert("L"))
output_image = np.asarray(Image.open("{assets['output']}").convert("L"))
nn = NeuralNetwork([
    ImageLayer(input_image, height=1.1),
    FeedForwardLayer(5),
    FeedForwardLayer(3),
    EmbeddingLayer(dist_theme="ellipse"),
    FeedForwardLayer(3),
    FeedForwardLayer(5),
    ImageLayer(output_image, height=1.1),
], layer_spacing=0.1)
nn.move_to(ORIGIN)
{_play_or_add(animate, 'nn.make_forward_pass_animation(run_time=5)')}
"""
        return header + _wrap_scene(scene_name, "Scene", body)
    raise ValueError(f"unsupported mode: {mode}")


def required_assets(mode: str) -> Iterable[str]:
    if mode == "triplet":
        return ("anchor", "positive", "negative")
    if mode == "paired-query":
        return ("query-positive", "query-negative")
    if mode == "vae":
        return ("input", "output")
    return ()


def main(argv: list[str] | None = None) -> int:
    parser = make_parser()
    args = parser.parse_args(argv)
    scene_file = Path(args.scene_file)
    if scene_file.exists() and not args.force:
        parser.error(f"{scene_file} already exists; pass --force to overwrite")
    assets_dir = Path(args.assets_dir)
    if not assets_dir.is_absolute():
        assets_dir = scene_file.parent / assets_dir
    assets = _make_assets(assets_dir, required_assets(args.mode)) if tuple(required_assets(args.mode)) else {}
    source = scene_source(args.mode, args.scene_name, args.animate_scene, assets)
    scene_file.parent.mkdir(parents=True, exist_ok=True)
    scene_file.write_text(source, encoding="utf-8")
    print(f"wrote {scene_file}")
    if assets:
        print(f"generated assets in {assets_dir}")
    if args.render:
        command = ["manim", args.quality]
        if args.still:
            command.append("-s")
        command.extend([str(scene_file), args.scene_name])
        print("running:", " ".join(command))
        completed = subprocess.run(command, check=False)
        return int(completed.returncode)
    print("render skipped; run Manim manually or add --render")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
