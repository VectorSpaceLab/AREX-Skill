#!/usr/bin/env python3
"""Inspect optimizer-network configs and optional shape contracts.

The script only parses and prints derived configuration. If --build-graph is
passed, it instantiates the selected network in a TensorFlow graph and prints
shape metadata without running training.
"""

from __future__ import annotations

import argparse
import ast
import json
import sys
from pathlib import Path

import numpy as np

SUPPORTED_NETS = {
    "StandardDeepLSTM": "StandardDeepLSTM",
    "CoordinateWiseDeepLSTM": "CoordinateWiseDeepLSTM",
    "KernelDeepLSTM": "KernelDeepLSTM",
    "Sgd": "Sgd",
    "sgd": "Sgd",
    "Adam": "Adam",
    "adam": "Adam",
}

DEFAULT_PREPROCESS_OPTIONS = {
    "LogAndSign": {"k": 5},
}


def parse_literal(text):
    """Parse a CLI literal, falling back to the raw string."""
    if text is None:
        return None

    stripped = str(text).strip()
    if not stripped:
        return ""

    lowered = stripped.lower()
    if lowered in {"none", "null"}:
        return None
    if lowered == "true":
        return True
    if lowered == "false":
        return False

    if stripped[:1] in {"{", "["}:
        try:
            return json.loads(stripped)
        except Exception:
            pass

    try:
        return ast.literal_eval(stripped)
    except Exception:
        return stripped


def parse_int_sequence(text, flag_name):
    """Parse a comma-separated or JSON-like integer sequence."""
    if text is None:
        return ()

    value = parse_literal(text)
    if value in (None, ""):
        return ()

    if isinstance(value, (list, tuple)):
        items = value
    elif isinstance(value, str):
        items = [part.strip() for part in value.split(",") if part.strip()]
    else:
        items = [value]

    try:
        return tuple(int(item) for item in items)
    except (TypeError, ValueError) as exc:
        raise ValueError("{} must be a comma-separated list of integers".format(
            flag_name)) from exc


def parse_key_value_options(text):
    """Parse key=value pairs separated by commas."""
    options = {}
    if not text:
        return options

    for raw_item in text.split(","):
        item = raw_item.strip()
        if not item:
            continue
        if "=" not in item:
            raise ValueError(
                "preprocess options must use key=value syntax, got {!r}".format(
                    item))
        key, raw_value = item.split("=", 1)
        options[key.strip()] = parse_literal(raw_value.strip())
    return options


def normalize_preprocess_name(name):
    """Normalize the preprocess name used by the config builder."""
    normalized = str(name).strip()
    if normalized.lower() in {"identity", "tf.identity"}:
        return "identity"
    if normalized.startswith("tf."):
        return normalized[3:]
    return normalized


def parse_preprocess(text):
    """Parse --preprocess into a name/options pair."""
    if text is None:
        return "identity", {}

    stripped = str(text).strip()
    if not stripped or stripped.lower() in {"identity", "tf.identity"}:
        return "identity", {}

    parsed = parse_literal(stripped)
    if isinstance(parsed, dict):
        if "name" not in parsed:
            raise ValueError(
                "preprocess dict form must include a 'name' key")
        name = normalize_preprocess_name(parsed["name"])
        options = parsed.get("options", {})
        if options is None:
            options = {}
        if not isinstance(options, dict):
            raise ValueError("preprocess options must be a mapping")
        return name, options

    if isinstance(parsed, str):
        raw = parsed
    else:
        raw = str(parsed)

    if ":" in raw:
        name, option_text = raw.split(":", 1)
        option_text = option_text.strip()
        if option_text[:1] in {"{", "["}:
            options = parse_literal(option_text)
            if not isinstance(options, dict):
                raise ValueError("preprocess inline options must be a mapping")
        else:
            options = parse_key_value_options(option_text)
    else:
        name = raw
        options = dict(DEFAULT_PREPROCESS_OPTIONS.get(
            normalize_preprocess_name(name), {}))

    return normalize_preprocess_name(name), options


def normalize_initializer_value(value):
    """Normalize initializer leaves into TensorFlow-friendly values."""
    if isinstance(value, dict):
        return {key: normalize_initializer_value(val)
                for key, val in value.items()}

    if isinstance(value, (list, tuple)):
        if not value:
            return np.asarray(value)
        if all(isinstance(item, (int, float, bool, np.number)) for item in value):
            return np.asarray(value)
        if all(isinstance(item, (list, tuple)) for item in value):
            return np.asarray([normalize_initializer_value(item)
                              for item in value])
        raise ValueError(
            "initializer lists must contain numbers or nested numeric lists")

    if isinstance(value, (int, float, bool, np.number)):
        return np.asarray(value)

    return value


def parse_initializer(text):
    """Parse --initializer into a value accepted by networks._convert_to_initializer."""
    if text is None:
        return None

    value = parse_literal(text)
    if value is None:
        return None
    return normalize_initializer_value(value)


def json_ready(value):
    """Convert numpy-heavy objects into JSON-serializable data."""
    if isinstance(value, dict):
        return {str(key): json_ready(val) for key, val in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_ready(item) for item in value]
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    return value


def resolve_net_name(name):
    """Return the canonical network class name."""
    try:
        return SUPPORTED_NETS[str(name)]
    except KeyError as exc:
        raise ValueError(
            "unsupported net {!r}; choose one of {}".format(
                name, ", ".join(sorted(set(SUPPORTED_NETS.values()))))) from exc


def build_derived_config(args):
    """Build a network config dictionary from the parsed CLI flags."""
    net_name = resolve_net_name(args.net)
    layers = parse_int_sequence(args.layers, "--layers")
    kernel_shape = parse_int_sequence(args.kernel_shape, "--kernel-shape")
    preprocess_name, preprocess_options = parse_preprocess(args.preprocess)
    initializer = parse_initializer(args.initializer)
    scale = 1.0 if args.scale is None else float(args.scale)

    if net_name == "StandardDeepLSTM":
        output_size = 1 if args.output_size is None else int(args.output_size)
        if output_size <= 0:
            raise ValueError("--output-size must be a positive integer")
        return {
            "net": net_name,
            "net_options": {
                "output_size": output_size,
                "layers": layers,
                "preprocess_name": preprocess_name,
                "preprocess_options": preprocess_options,
                "scale": scale,
                "initializer": initializer,
            },
        }

    if net_name == "CoordinateWiseDeepLSTM":
        return {
            "net": net_name,
            "net_options": {
                "layers": layers,
                "preprocess_name": preprocess_name,
                "preprocess_options": preprocess_options,
                "scale": scale,
                "initializer": initializer,
            },
        }

    if net_name == "KernelDeepLSTM":
        if len(kernel_shape) != 2:
            raise ValueError(
                "--kernel-shape is required for KernelDeepLSTM and must have exactly two integers")
        return {
            "net": net_name,
            "net_options": {
                "kernel_shape": list(kernel_shape),
                "layers": layers,
                "preprocess_name": preprocess_name,
                "preprocess_options": preprocess_options,
                "scale": scale,
                "initializer": initializer,
            },
        }

    if net_name == "Sgd":
        learning_rate = 0.001 if args.learning_rate is None else float(args.learning_rate)
        return {
            "net": net_name,
            "net_options": {
                "learning_rate": learning_rate,
            },
        }

    if net_name == "Adam":
        learning_rate = 1e-3 if args.learning_rate is None else float(args.learning_rate)
        return {
            "net": net_name,
            "net_options": {
                "learning_rate": learning_rate,
            },
        }

    raise ValueError("unsupported net {!r}".format(args.net))


def find_repo_root(start):
    """Find the repository root by walking upward from a starting path."""
    path = Path(start).resolve()
    search_space = [path] + list(path.parents)
    for candidate in search_space:
        if (candidate / "networks.py").is_file() and (candidate / "preprocess.py").is_file():
            return candidate
    return None


def import_runtime_modules(repo_root):
    """Import repo modules after injecting the repo root into sys.path."""
    repo_root = Path(repo_root).resolve()
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    import tensorflow as tf  # pylint: disable=import-outside-toplevel
    import networks  # pylint: disable=import-outside-toplevel

    return tf, networks


def describe_structure(value):
    """Return a JSON-friendly summary of nested TensorFlow tensors."""
    if isinstance(value, (list, tuple)):
        return [describe_structure(item) for item in value]
    shape = value.get_shape().as_list()
    return {
        "shape": shape,
        "dtype": value.dtype.name,
    }


def make_dummy_input(tf, net_name, kernel_shape):
    """Create a static dummy tensor for graph inspection."""
    if net_name == "KernelDeepLSTM":
        shape = tuple(kernel_shape) + (2, 2)
    else:
        shape = (2, 3)
    return tf.zeros(shape, dtype=tf.float32)


def inspect_graph(repo_root, config):
    """Instantiate the network and record shape metadata."""
    tf, networks = import_runtime_modules(repo_root)

    with tf.Graph().as_default():
        net = networks.factory(config["net"], config["net_options"])
        dummy_input = make_dummy_input(tf, config["net"],
                                       config["net_options"].get("kernel_shape", ()))
        state = net.initial_state_for_inputs(dummy_input)
        update, next_state = net(dummy_input, state)
        trainable_names = [
            var.name for var in tf.compat.v1.trainable_variables()
        ]

        return {
            "dummy_input_shape": dummy_input.get_shape().as_list(),
            "output_shape": update.get_shape().as_list(),
            "state_shape": describe_structure(state),
            "next_state_shape": describe_structure(next_state),
            "trainable_variable_count": len(trainable_names),
            "trainable_variable_names": trainable_names,
        }


def build_parser():
    """Create the CLI parser."""
    parser = argparse.ArgumentParser(
        description=(
            "Inspect optimizer-network configurations and optional build-graph "
            "shape metadata without training."))
    parser.add_argument("--net", required=True,
                        help="Network class name to inspect.")
    parser.add_argument("--layers", default="",
                        help="Comma-separated LSTM layer sizes.")
    parser.add_argument("--kernel-shape", default="",
                        help="Comma-separated 2D kernel shape for KernelDeepLSTM.")
    parser.add_argument("--preprocess", default="identity",
                        help="Preprocess module name or name:option=value list.")
    parser.add_argument("--initializer", default=None,
                        help=(
                            "Initializer spec: a string name, a dict literal, or a "
                            "JSON/Python list of numeric values."))
    parser.add_argument("--repo-root", default=None,
                        help="Repository root used to import the source modules.")
    parser.add_argument("--build-graph", action="store_true",
                        help="Instantiate the network and print shape metadata.")
    parser.add_argument("--output-size", type=int, default=None,
                        help=(
                            "Output size for StandardDeepLSTM. Defaults to 1 if "
                            "omitted."))
    parser.add_argument("--learning-rate", type=float, default=None,
                        help="Optional learning rate override for Sgd or Adam.")
    parser.add_argument("--scale", type=float, default=None,
                        help="Optional scale override for learned LSTM nets.")
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        config = build_derived_config(args)
        payload = {"config": json_ready(config)}

        if args.build_graph:
            if args.repo_root is None:
                repo_root = find_repo_root(Path(__file__).resolve())
            else:
                repo_root = Path(args.repo_root).resolve()
                if not repo_root.exists():
                    raise ValueError("repo root {!r} does not exist".format(repo_root))
            if repo_root is None:
                raise ValueError(
                    "could not find the repository root; pass --repo-root explicitly")
            payload["graph"] = json_ready(inspect_graph(repo_root, config))

        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0
    except Exception as exc:  # pragma: no cover - surfaced through argparse
        parser.error(str(exc))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
