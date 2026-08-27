#!/usr/bin/env python3
"""Opt-in Twitter/X stream template.

This template is dry-run by default. It only imports Tweepy and opens a network
connection when --connect is supplied.
"""

import argparse
import os
import sys
from pathlib import Path

LEGACY_ENV_VARS = [
    "TWITTER_CONSUMER_KEY",
    "TWITTER_CONSUMER_SECRET",
    "TWITTER_ACCESS_TOKEN",
    "TWITTER_ACCESS_TOKEN_SECRET",
]


def parse_args():
    parser = argparse.ArgumentParser(
        description="Plan or start a Tweepy-based Twitter/X stream without hardcoded secrets."
    )
    parser.add_argument(
        "--track",
        nargs="+",
        help="One or more track terms or phrases to follow.",
    )
    parser.add_argument(
        "--output",
        default="-",
        help="Append raw JSON lines to this file, or - for standard output.",
    )
    parser.add_argument(
        "--connect",
        action="store_true",
        help="Actually open the Tweepy stream. Dry run is the default.",
    )
    return parser.parse_args()


def collect_credentials():
    creds = {name: os.environ.get(name, "").strip() for name in LEGACY_ENV_VARS}
    missing = [name for name, value in creds.items() if not value]
    return creds, missing


def open_output(path):
    if path == "-":
        return sys.stdout, False
    output_path = Path(path).expanduser()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    return open(output_path, "a", encoding="utf-8", newline="\n"), True


def show_plan(args):
    creds, missing = collect_credentials()
    print("Dry run only; no network connection will be opened.", file=sys.stderr)
    if args.track:
        print(f"Track terms: {', '.join(args.track)}", file=sys.stderr)
    else:
        print("Track terms: none supplied yet", file=sys.stderr)
    print(f"Output target: {args.output}", file=sys.stderr)
    print(
        "If you later add --connect, this template expects the legacy OAuth1 env vars: "
        + ", ".join(LEGACY_ENV_VARS),
        file=sys.stderr,
    )
    if missing:
        print(f"Currently missing: {', '.join(missing)}", file=sys.stderr)
    else:
        print("All legacy OAuth1 environment variables are present.", file=sys.stderr)


def stream_with_tweepy(args):
    try:
        import tweepy
    except ImportError as exc:
        raise SystemExit("tweepy is required only when --connect is used") from exc

    creds, missing = collect_credentials()
    if missing:
        raise SystemExit("Missing required environment variables: " + ", ".join(missing))
    if not args.track:
        raise SystemExit("Use --track TERM [TERM ...] before --connect.")

    try:
        StreamListener = tweepy.StreamListener
    except AttributeError:
        from tweepy.streaming import StreamListener  # type: ignore

    try:
        Stream = tweepy.Stream
    except AttributeError:
        from tweepy import Stream  # type: ignore

    try:
        OAuthHandler = tweepy.OAuthHandler
    except AttributeError:
        from tweepy import OAuthHandler  # type: ignore

    auth = OAuthHandler(creds["TWITTER_CONSUMER_KEY"], creds["TWITTER_CONSUMER_SECRET"])
    auth.set_access_token(creds["TWITTER_ACCESS_TOKEN"], creds["TWITTER_ACCESS_TOKEN_SECRET"])

    class JSONLineListener(StreamListener):
        def __init__(self, sink):
            super().__init__()
            self.sink = sink
            self.count = 0

        def on_data(self, data):
            if isinstance(data, bytes):
                data = data.decode("utf-8", "replace")
            line = data.rstrip("\r\n")
            if not line:
                return True
            self.sink.write(line + "\n")
            self.sink.flush()
            self.count += 1
            return True

        def on_error(self, status):
            print(f"stream error: {status}", file=sys.stderr)
            return False

        def on_exception(self, exception):
            print(f"stream exception: {exception}", file=sys.stderr)
            return False

    sink, close_sink = open_output(args.output)
    try:
        listener = JSONLineListener(sink)
        stream = Stream(auth, listener)
        print(f"Connecting with {len(args.track)} track term(s).", file=sys.stderr)
        stream.filter(track=args.track)
    except KeyboardInterrupt:
        print("Stream stopped by user.", file=sys.stderr)
        return 130
    finally:
        if close_sink:
            sink.close()
    return 0


def main():
    args = parse_args()
    if not args.connect:
        show_plan(args)
        return 0
    return stream_with_tweepy(args)


if __name__ == "__main__":
    raise SystemExit(main())
