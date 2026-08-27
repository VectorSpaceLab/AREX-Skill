#!/usr/bin/env python3
"""Create a tiny deterministic word2vec-format fixture for text2vec Word2Vec.

The fixture is for smoke tests only. It is small enough to inspect by hand and
contains a few Chinese characters commonly used in text2vec embedding examples.
"""

import argparse
import struct
import sys
from pathlib import Path

# Nine 4-dimensional vectors. Character-level entries keep the fixture useful
# with text2vec.Word2Vec.encode on plain Chinese strings.
VECTORS = (
    ("银", (1.0, 0.0, 0.0, 0.0)),
    ("行", (0.0, 1.0, 0.0, 0.0)),
    ("卡", (0.0, 0.0, 1.0, 0.0)),
    ("花", (0.0, 0.0, 0.0, 1.0)),
    ("呗", (0.5, 0.5, 0.0, 0.0)),
    ("更", (0.25, 0.25, 0.25, 0.25)),
    ("改", (0.1, 0.2, 0.3, 0.4)),
    ("绑", (0.4, 0.3, 0.2, 0.1)),
    ("定", (0.6, 0.0, 0.2, 0.2)),
)


def build_parser():
    parser = argparse.ArgumentParser(
        description="Write a tiny local word2vec-format file for deterministic Word2Vec smoke tests.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--output-file", "--output_file",
        dest="output_file",
        required=True,
        help="Path to write. Parent directories are created automatically.",
    )
    parser.add_argument(
        "--binary",
        action="store_true",
        default=False,
        help="Write binary word2vec format. Default is plain text word2vec format.",
    )
    return parser


def write_text(path):
    dim = len(VECTORS[0][1])
    with path.open("w", encoding="utf-8") as handle:
        handle.write("%d %d\n" % (len(VECTORS), dim))
        for token, vector in VECTORS:
            handle.write(token + " " + " ".join("%.6f" % value for value in vector) + "\n")


def write_binary(path):
    dim = len(VECTORS[0][1])
    fmt = "<" + "f" * dim
    with path.open("wb") as handle:
        handle.write(("%d %d\n" % (len(VECTORS), dim)).encode("utf-8"))
        for token, vector in VECTORS:
            handle.write(token.encode("utf-8"))
            handle.write(b" ")
            handle.write(struct.pack(fmt, *vector))
            handle.write(b"\n")


def main(argv=None):
    args = build_parser().parse_args(argv)
    output_path = Path(args.output_file).expanduser()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if args.binary:
        write_binary(output_path)
        mode = "binary"
    else:
        write_text(output_path)
        mode = "text"

    print(
        "Wrote %s word2vec fixture with %d tokens and %d dimensions to %s"
        % (mode, len(VECTORS), len(VECTORS[0][1]), output_path),
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
