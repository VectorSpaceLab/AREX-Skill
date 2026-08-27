#!/usr/bin/env python3
"""Visualize a keras-rl FileLogger JSON file.

This helper is self-contained for the generated skill. It expects the JSON
schema written by rl.callbacks.FileLogger: a top-level object containing an
"episode" list and one or more metric lists with matching lengths.
"""

from __future__ import print_function

import argparse
import json
import os
import sys


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Plot metrics from a keras-rl FileLogger JSON file."
    )
    parser.add_argument(
        "filename",
        help="JSON file produced by rl.callbacks.FileLogger; it must contain an 'episode' key.",
    )
    parser.add_argument(
        "--output",
        help="Save the plot to this file. When set, a noninteractive Matplotlib backend is used.",
    )
    parser.add_argument(
        "--figsize",
        nargs=2,
        type=float,
        metavar=("WIDTH", "HEIGHT"),
        help="Figure size in inches. Defaults to 15 by 3.5 times the number of plotted metrics.",
    )
    parser.add_argument(
        "--keys",
        nargs="+",
        help="Optional metric keys to plot. Defaults to every key except 'episode'.",
    )
    parser.add_argument(
        "--title",
        default=None,
        help="Optional figure title.",
    )
    return parser.parse_args(argv)


def fail(message, exit_code=2):
    print("error: {}".format(message), file=sys.stderr)
    return exit_code


def load_log(filename):
    if not os.path.exists(filename):
        raise ValueError("file does not exist: {}".format(filename))
    if not os.path.isfile(filename):
        raise ValueError("not a regular file: {}".format(filename))
    try:
        with open(filename, "r") as handle:
            data = json.load(handle)
    except ValueError as exc:
        raise ValueError("failed to parse JSON: {}".format(exc))
    except OSError as exc:
        raise ValueError("failed to read file: {}".format(exc))

    if not isinstance(data, dict):
        raise ValueError("top-level JSON value must be an object/dictionary")
    if "episode" not in data:
        raise ValueError("log file does not contain the required 'episode' key")
    episodes = data["episode"]
    if not isinstance(episodes, list):
        raise ValueError("'episode' must be a list")
    if len(episodes) == 0:
        raise ValueError("'episode' list is empty; no completed episodes to plot")
    return data


def select_keys(data, requested_keys=None):
    if requested_keys:
        missing = [key for key in requested_keys if key not in data]
        if missing:
            raise ValueError("requested key(s) not present: {}".format(", ".join(missing)))
        keys = list(requested_keys)
    else:
        keys = sorted(key for key in data.keys() if key != "episode")
    if not keys:
        raise ValueError("no metric keys to plot; JSON contains only 'episode'")

    episode_len = len(data["episode"])
    valid_keys = []
    for key in keys:
        values = data[key]
        if not isinstance(values, list):
            raise ValueError("key '{}' must map to a list, got {}".format(key, type(values).__name__))
        if len(values) != episode_len:
            raise ValueError(
                "key '{}' has length {}, but 'episode' has length {}".format(
                    key, len(values), episode_len
                )
            )
        valid_keys.append(key)
    return valid_keys


def import_pyplot(output):
    try:
        import matplotlib
    except Exception as exc:  # pragma: no cover - depends on user environment
        raise RuntimeError(
            "failed to import matplotlib: {}. Install matplotlib or run in an environment that provides it.".format(exc)
        )

    if output:
        try:
            matplotlib.use("Agg", force=True)
        except TypeError:  # older Matplotlib did not support force=
            matplotlib.use("Agg")
    elif not os.environ.get("DISPLAY") and sys.platform not in ("darwin", "win32"):
        # Do not fail yet: a user may have configured a noninteractive backend.
        print(
            "warning: no DISPLAY detected; use --output for reliable noninteractive rendering.",
            file=sys.stderr,
        )

    try:
        import matplotlib.pyplot as plt
    except Exception as exc:  # pragma: no cover - depends on user environment
        raise RuntimeError(
            "failed to import matplotlib.pyplot: {}. If headless, rerun with --output.".format(exc)
        )
    return plt


def visualize_log(filename, output=None, figsize=None, keys=None, title=None):
    data = load_log(filename)
    keys = select_keys(data, keys)
    plt = import_pyplot(output)

    if figsize is None:
        figsize = (15.0, max(3.5, 3.5 * len(keys)))
    episodes = data["episode"]

    fig, axes = plt.subplots(len(keys), sharex=True, figsize=figsize)
    if len(keys) == 1:
        axes = [axes]

    for axis, key in zip(axes, keys):
        try:
            axis.plot(episodes, data[key])
        except Exception as exc:
            raise ValueError("failed to plot key '{}': {}".format(key, exc))
        axis.set_ylabel(key)
        axis.grid(True, alpha=0.3)

    axes[-1].set_xlabel("episode")
    if title:
        fig.suptitle(title)
    fig.tight_layout()

    if output:
        try:
            fig.savefig(output)
        except Exception as exc:
            raise RuntimeError("failed to save plot to '{}': {}".format(output, exc))
        print("saved plot to {}".format(output))
    else:
        try:
            plt.show()
        except Exception as exc:
            raise RuntimeError("failed to display plot: {}. Rerun with --output.".format(exc))


def main(argv=None):
    args = parse_args(argv)
    try:
        visualize_log(
            args.filename,
            output=args.output,
            figsize=tuple(args.figsize) if args.figsize else None,
            keys=args.keys,
            title=args.title,
        )
    except (ValueError, RuntimeError) as exc:
        return fail(str(exc))
    return 0


if __name__ == "__main__":
    sys.exit(main())
