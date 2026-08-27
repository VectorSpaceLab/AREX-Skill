#!/usr/bin/env python3
"""Generate deterministic adjacent n-grams without repository dependencies."""

import argparse
import codecs
import json
import sys


def generate_ngrams(tokens, min_n=1, max_n=3, separator=""):
    """Return adjacent n-grams in stable position-major, n-ascending order.

    For each token position, all available n values from ``min_n`` through
    ``max_n`` are emitted before advancing to the next position. Components of
    one gram are joined with ``separator``. The input iterable is copied and is
    never mutated.
    """
    if isinstance(min_n, bool) or not isinstance(min_n, int) or min_n < 1:
        raise ValueError("min_n must be an integer >= 1")
    if isinstance(max_n, bool) or not isinstance(max_n, int) or max_n < 1:
        raise ValueError("max_n must be an integer >= 1")
    if min_n > max_n:
        raise ValueError("min_n must be <= max_n")
    if not isinstance(separator, str):
        raise TypeError("separator must be a string")

    token_list = list(tokens)
    result = []
    token_count = len(token_list)
    for start in range(token_count):
        for n_value in range(min_n, max_n + 1):
            stop = start + n_value
            if stop <= token_count:
                result.append(separator.join(token_list[start:stop]))
    return result


def _positive_int(value):
    try:
        parsed = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError("must be an integer >= 1")
    if parsed < 1:
        raise argparse.ArgumentTypeError("must be >= 1")
    return parsed


def _build_parser():
    parser = argparse.ArgumentParser(
        description=(
            "Generate adjacent n-grams in position-major order. Input records "
            "are never modified."
        )
    )
    source_group = parser.add_mutually_exclusive_group()
    source_group.add_argument(
        "--text", help="Treat one whitespace-tokenized string as one record."
    )
    source_group.add_argument(
        "--file", metavar="PATH", help="Read one independent record per line; - means stdin."
    )
    source_group.add_argument(
        "--stdin", action="store_true", help="Read one independent record per stdin line."
    )
    parser.add_argument(
        "tokens",
        nargs="*",
        help="Tokens for one record (cannot be combined with --text/--file/--stdin).",
    )
    parser.add_argument("--min-n", type=_positive_int, default=1, help="Minimum n (default: 1).")
    parser.add_argument("--max-n", type=_positive_int, default=3, help="Maximum n (default: 3).")
    parser.add_argument(
        "--separator",
        default="",
        help="Join token components inside a gram (default: empty, matching the repository helper).",
    )
    parser.add_argument(
        "--output-separator",
        default=" ",
        help="Join generated grams in each plain output record (default: one space).",
    )
    parser.add_argument("--encoding", default="utf-8", help="Encoding for file/stdin input.")
    parser.add_argument(
        "--json", action="store_true", help="Emit a deterministic JSON object."
    )
    return parser


def _stdin_records(encoding):
    stream = getattr(sys.stdin, "buffer", sys.stdin)
    for line_number, raw_line in enumerate(stream, 1):
        if isinstance(raw_line, bytes):
            line = raw_line.decode(encoding, errors="strict")
        else:
            line = raw_line
        yield line_number, line.rstrip("\r\n").split()


def _file_records(path, encoding):
    with open(path, "rb") as stream:
        for line_number, raw_line in enumerate(stream, 1):
            line = raw_line.decode(encoding, errors="strict")
            yield line_number, line.rstrip("\r\n").split()


def main(argv=None):
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.min_n > args.max_n:
        parser.error("--min-n must be <= --max-n")
    if args.tokens and (args.text is not None or args.file is not None or args.stdin):
        parser.error("positional tokens cannot be combined with --text, --file, or --stdin")
    try:
        codecs.lookup(args.encoding)
    except LookupError:
        parser.error("unknown encoding: {}".format(args.encoding))

    try:
        if args.tokens:
            source = "<arguments>"
            input_records = [(1, list(args.tokens))]
        elif args.text is not None:
            source = "<text>"
            input_records = [(1, args.text.split())]
        elif args.file is not None and args.file != "-":
            source = args.file
            input_records = _file_records(args.file, args.encoding)
        else:
            source = "<stdin>"
            input_records = _stdin_records(args.encoding)

        records = []
        for line_number, tokens in input_records:
            grams = generate_ngrams(
                tokens,
                min_n=args.min_n,
                max_n=args.max_n,
                separator=args.separator,
            )
            records.append(
                {
                    "record": line_number,
                    "tokens": tokens,
                    "ngrams": grams,
                }
            )
    except (OSError, UnicodeError) as exc:
        print("error: cannot read {}: {}".format(source, exc), file=sys.stderr)
        return 2

    if args.json:
        result = {
            "source": source,
            "min_n": args.min_n,
            "max_n": args.max_n,
            "separator": args.separator,
            "output_separator": args.output_separator,
            "records": records,
        }
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        for record in records:
            print(args.output_separator.join(record["ngrams"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
