#!/usr/bin/env python3
"""Build a safe deep-daze `imagine` CLI command without running generation.

The script intentionally does not import deep_daze, torch, or CLIP. It only
validates user-supplied file paths, applies bounded resource presets, and prints
a shell-quoted command for the caller to review and run separately.
"""

import argparse
import os
import shlex
import sys
from typing import Dict, Iterable, List, Optional, Tuple


PRESETS: Dict[str, Dict[str, object]] = {
    "smoke": {
        "epochs": 1,
        "iterations": 10,
        "save_every": 5,
        "image_width": 256,
        "num_layers": 8,
        "hidden_size": 128,
        "batch_size": 1,
        "gradient_accumulate_every": 4,
    },
    "low-vram": {
        "epochs": 1,
        "iterations": 50,
        "save_every": 10,
        "image_width": 256,
        "num_layers": 16,
        "hidden_size": 256,
        "batch_size": 1,
        "gradient_accumulate_every": 16,
    },
    "balanced": {
        "epochs": 4,
        "iterations": 100,
        "save_every": 25,
        "image_width": 512,
        "num_layers": 24,
        "hidden_size": 256,
        "batch_size": 4,
        "gradient_accumulate_every": 4,
    },
    "quality": {
        "epochs": 10,
        "iterations": 300,
        "save_every": 50,
        "image_width": 512,
        "num_layers": 32,
        "hidden_size": 256,
        "batch_size": 8,
        "gradient_accumulate_every": 2,
    },
}

MODEL_NAMES = ("RN50", "RN101", "RN50x4", "ViT-B/32", "ViT-L/14")
OPTIMIZERS = ("AdamP", "Adam", "DiffGrad")


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return parsed


def nonnegative_int(value: str) -> int:
    parsed = int(value)
    if parsed < 0:
        raise argparse.ArgumentTypeError("must be a non-negative integer")
    return parsed


def positive_float(value: str) -> float:
    parsed = float(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be a positive number")
    return parsed


def add_bool_pair(parser: argparse.ArgumentParser, true_name: str, false_name: str, dest: str, default: bool, help_text: str) -> None:
    parser.add_argument(true_name, dest=dest, action="store_true", default=default, help=help_text)
    parser.add_argument(false_name, dest=dest, action="store_false", help=argparse.SUPPRESS)


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Print a shell-quoted deep-daze imagine command. The command is not executed.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        epilog=(
            "Examples:\n"
            "  build_imagine_command.py --prompt 'a house in the forest'\n"
            "  build_imagine_command.py --prompt 'a watercolor sky' --start-image inputs/prime.jpg --preset low-vram\n"
            "  build_imagine_command.py --img inputs/target.jpg --preset smoke\n"
            "  build_imagine_command.py --prompt 'scene one. scene two.' --story --story-separator . --save-video"
        ),
    )
    p.add_argument("positional_prompt", nargs="?", help="Optional positional prompt text for the generated imagine command.")
    p.add_argument("--prompt", dest="prompt", help="Prompt text. Use instead of the positional prompt when scripting.")
    p.add_argument("--img", help="JPG/PNG image path to use as a CLIP optimization target.")
    p.add_argument("--start-image", dest="start_image", help="JPG/PNG image path used to prime the generator before optimization.")
    p.add_argument("--preset", choices=sorted(PRESETS), default="smoke", help="Bounded resource preset to apply before overrides.")

    p.add_argument("--epochs", type=positive_int, help="Override preset epochs.")
    p.add_argument("--iterations", type=positive_int, help="Override preset iterations per epoch.")
    p.add_argument("--save-every", dest="save_every", type=positive_int, help="Override preset progress-frame interval.")
    p.add_argument("--image-width", dest="image_width", type=positive_int, help="Override preset square output width.")
    p.add_argument("--num-layers", dest="num_layers", type=positive_int, help="Override preset SIREN layer count.")
    p.add_argument("--hidden-size", dest="hidden_size", type=positive_int, help="Override preset SIREN hidden size.")
    p.add_argument("--batch-size", dest="batch_size", type=positive_int, help="Override preset batch size.")
    p.add_argument("--gradient-accumulate-every", dest="gradient_accumulate_every", type=positive_int, help="Override preset gradient accumulation.")
    p.add_argument("--learning-rate", dest="learning_rate", type=positive_float, help="Main optimization learning rate.")

    p.add_argument("--story", dest="create_story", action="store_true", help="Enable deep-daze story mode for long prompts.")
    p.add_argument("--story-start-words", dest="story_start_words", type=positive_int, default=5, help="Initial word count for story mode without separator.")
    p.add_argument("--story-words-per-epoch", dest="story_words_per_epoch", type=positive_int, default=5, help="Words added per story epoch without separator.")
    p.add_argument("--story-separator", dest="story_separator", help="Separator used to split story text into epoch chunks, for example '.'.")

    p.add_argument("--start-image-train-iters", dest="start_image_train_iters", type=nonnegative_int, default=50, help="Priming iterations for --start-image.")
    p.add_argument("--start-image-lr", dest="start_image_lr", type=positive_float, default=3e-4, help="Learning rate for start-image priming.")

    add_bool_pair(p, "--save-progress", "--no-save-progress", "save_progress", True, "Save intermediate progress frames.")
    p.add_argument("--save-gif", dest="save_gif", action="store_true", help="Request GIF generation from progress frames.")
    p.add_argument("--save-video", dest="save_video", action="store_true", help="Request MP4 generation from progress frames.")
    add_bool_pair(p, "--open-folder", "--no-open-folder", "open_folder", False, "Ask imagine to open the output folder. Disabled by default for headless safety.")
    add_bool_pair(p, "--timestamp", "--no-timestamp", "save_date_time", True, "Use timestamped output filenames to avoid overwrite prompts.")
    p.add_argument("--allow-overwrite", dest="overwrite", action="store_true", help="Set --overwrite=True in the printed command.")
    p.add_argument("--seed", type=int, help="Seed for deterministic attempts.")

    p.add_argument("--model-name", dest="model_name", choices=MODEL_NAMES, default="ViT-B/32", help="CLIP model name.")
    p.add_argument("--optimizer", choices=OPTIMIZERS, default="AdamP", help="Optimizer name.")
    p.add_argument("--deeper", action="store_true", help="Emit --deeper=True, which makes imagine use 32 layers.")
    return p


def bool_text(value: bool) -> str:
    return "True" if value else "False"


def warn(message: str) -> None:
    print(f"warning: {message}", file=sys.stderr)


def validate_file(path: str, label: str, errors: List[str]) -> None:
    if not os.path.exists(path):
        errors.append(f"{label} does not exist: {path}")
    elif not os.path.isfile(path):
        errors.append(f"{label} is not a regular file: {path}")


def choose_prompt(args: argparse.Namespace, errors: List[str]) -> str | None:
    if args.prompt and args.positional_prompt:
        errors.append("provide either positional prompt or --prompt, not both")
        return None
    return args.prompt if args.prompt is not None else args.positional_prompt


def merge_config(args: argparse.Namespace) -> Dict[str, object]:
    config = dict(PRESETS[args.preset])
    for name in (
        "epochs",
        "iterations",
        "save_every",
        "image_width",
        "num_layers",
        "hidden_size",
        "batch_size",
        "gradient_accumulate_every",
        "learning_rate",
    ):
        value = getattr(args, name)
        if value is not None:
            config[name] = value
    return config


def append_flag(flags: List[Tuple[str, object]], name: str, value: Optional[object]) -> None:
    if value is not None:
        flags.append((name, value))


def render_value(value: object) -> str:
    if isinstance(value, bool):
        return bool_text(value)
    return str(value)


def render_command(prompt: Optional[str], flags: Iterable[Tuple[str, object]]) -> str:
    parts = ["imagine"]
    if prompt:
        parts.append(shlex.quote(prompt))
    for name, value in flags:
        parts.append(shlex.quote(f"--{name}={render_value(value)}"))
    return " ".join(parts)


def main(argv: Optional[List[str]] = None) -> int:
    args = parser().parse_args(argv)
    errors: List[str] = []
    prompt = choose_prompt(args, errors)

    if not prompt and not args.img:
        errors.append("provide a prompt, --img, or both; start-image alone has no optimization target")
    if args.img:
        validate_file(args.img, "--img", errors)
    if args.start_image:
        validate_file(args.start_image, "--start-image", errors)
    if args.create_story and not prompt:
        errors.append("--story requires a text prompt")
    if (args.save_gif or args.save_video) and not args.save_progress:
        errors.append("--save-gif/--save-video require --save-progress")

    if args.story_separator and prompt and args.story_separator not in prompt:
        warn("story separator is not present in the prompt; imagine will ignore the separator")
    if prompt and not args.create_story:
        rough_word_count = len(prompt.split())
        if rough_word_count > 70:
            warn("prompt has more than 70 whitespace-delimited words; CLIP has a 77-token context, so consider --story")
    if args.deeper and args.num_layers and args.num_layers != 32:
        warn("--deeper makes imagine use 32 layers, overriding --num-layers")

    if errors:
        for error in errors:
            print(f"error: {error}", file=sys.stderr)
        return 2

    config = merge_config(args)

    flags: List[Tuple[str, object]] = []
    append_flag(flags, "img", args.img)
    for key in (
        "epochs",
        "iterations",
        "save_every",
        "image_width",
        "num_layers",
        "hidden_size",
        "batch_size",
        "gradient_accumulate_every",
        "learning_rate",
    ):
        append_flag(flags, key, config.get(key))

    if args.deeper:
        append_flag(flags, "deeper", True)

    append_flag(flags, "save_progress", args.save_progress)
    append_flag(flags, "open_folder", args.open_folder)
    append_flag(flags, "save_date_time", args.save_date_time)
    append_flag(flags, "overwrite", args.overwrite)
    append_flag(flags, "seed", args.seed)

    append_flag(flags, "start_image_path", args.start_image)
    if args.start_image:
        append_flag(flags, "start_image_train_iters", args.start_image_train_iters)
        append_flag(flags, "start_image_lr", args.start_image_lr)

    if args.create_story:
        append_flag(flags, "create_story", True)
        append_flag(flags, "story_start_words", args.story_start_words)
        append_flag(flags, "story_words_per_epoch", args.story_words_per_epoch)
        append_flag(flags, "story_separator", args.story_separator)

    append_flag(flags, "save_gif", args.save_gif)
    append_flag(flags, "save_video", args.save_video)
    append_flag(flags, "model_name", args.model_name)
    append_flag(flags, "optimizer", args.optimizer)

    print(render_command(prompt, flags))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
