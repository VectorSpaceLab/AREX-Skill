#!/usr/bin/env python
"""Check SimpleCV Display in a headless-safe SDL dummy session.

This helper is intentionally finite. It does not open a camera or run an
interactive display loop.
"""
from __future__ import print_function

import argparse
import os
import sys


def add_repo_root(path):
    if not path:
        return
    root = os.path.abspath(path)
    if root not in sys.path:
        sys.path.insert(0, root)
    print("added_repo_root=%s" % root)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Run a finite headless Display smoke check for SimpleCV.")
    parser.add_argument("--repo-root", help="Optional SimpleCV checkout to add to sys.path before importing.")
    parser.add_argument("--resolution", default="64x64", help="Display resolution as WIDTHxHEIGHT; default: 64x64.")
    parser.add_argument("--no-dummy", action="store_true", help="Do not force SDL_VIDEODRIVER=dummy before import.")
    args = parser.parse_args(argv)

    if not args.no_dummy:
        os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    add_repo_root(args.repo_root)

    try:
        width_s, height_s = args.resolution.lower().split("x", 1)
        resolution = (int(width_s), int(height_s))
    except Exception:
        print("status=failed reason=resolution must look like WIDTHxHEIGHT")
        return 2

    try:
        import SimpleCV
        from SimpleCV import Display, Image
        display = Display(resolution, headless=True)
        img = Image("simplecv").scale(resolution[0], resolution[1])
        display.writeFrame(img)
        display.quit()
        print("status=ok simplecv=%s resolution=%s sdl=%s" % (
            getattr(SimpleCV, "__version__", "unknown"), resolution, os.environ.get("SDL_VIDEODRIVER", "unset")))
        return 0
    except Exception as exc:
        print("status=failed error=%s: %s" % (exc.__class__.__name__, exc))
        print("hint=Use Python 2.7, pygame, and SDL_VIDEODRIVER=dummy for headless checks; avoid live display loops unless requested.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
