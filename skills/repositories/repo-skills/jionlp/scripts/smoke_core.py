#!/usr/bin/env python3
"""Fast import and a few core JioNLP smoke checks."""

from __future__ import annotations

from importlib import metadata

import jionlp as jio


def main() -> int:
    version = metadata.version("jionlp")
    print(f"jionlp.__version__ = {jio.__version__}")
    print(f"distribution version = {version}")
    print(f"jio_help entry point = {[e.value for e in metadata.entry_points(group='console_scripts') if e.name == 'jio_help']}")

    samples = {
        "clean_text": jio.clean_text("<p>你好 &amp; world</p>"),
        "remove_url": jio.remove_url("see https://example.com now"),
        "parse_money": jio.parse_money("1万元"),
        "parse_location": jio.parse_location("湖南湘潭城塘社区", town_village=True, change2new=True),
        "split_sentence": jio.split_sentence("中华古汉语，泱泱大国，历史传承的瑰宝。", criterion="fine"),
    }

    for name, value in samples.items():
        print(f"{name}: {value}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
