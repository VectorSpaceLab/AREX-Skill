#!/usr/bin/env python3
"""Lightweight installation smoke test for the bundled Tree of Thoughts skill."""

from importlib.metadata import version
import os

import tot
from tot.tasks import get_task


def main():
    print(f"distribution tree-of-thoughts-llm: {version('tree-of-thoughts-llm')}")
    print(f"package tot: {getattr(tot, '__version__', 'unknown')}")
    print(f"OPENAI_API_KEY: {'set' if os.getenv('OPENAI_API_KEY') else 'missing'}")
    for name in ('game24', 'text', 'crosswords'):
        task = get_task(name)
        print(f"{name}: {type(task).__name__}, len={len(task)}")


if __name__ == '__main__':
    main()
