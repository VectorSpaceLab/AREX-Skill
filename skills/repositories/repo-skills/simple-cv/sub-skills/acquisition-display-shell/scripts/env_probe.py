#!/usr/bin/env python
"""Safe SimpleCV acquisition/display environment probe.

This script does not open a physical camera by default.
"""
from __future__ import print_function

import argparse
import os
import sys


def add_repo_root(path):
    if path:
        root = os.path.abspath(path)
        if root not in sys.path:
            sys.path.insert(0, root)
        print("added_repo_root=%s" % root)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Probe SimpleCV shell/display/hardware flags without opening cameras.")
    parser.add_argument("--repo-root", help="Optional SimpleCV checkout to add to sys.path before import.")
    parser.add_argument("--check-display", action="store_true", help="Create a finite dummy-SDL Display.")
    parser.add_argument("--no-dummy", action="store_true", help="Do not set SDL_VIDEODRIVER=dummy for display checks.")
    args = parser.parse_args(argv)

    if not args.no_dummy:
        os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    add_repo_root(args.repo_root)

    try:
        import SimpleCV
        from SimpleCV import Camera, VirtualCamera, Display
        import SimpleCV.base as base
        print("simplecv_version=%s" % getattr(SimpleCV, "__version__", "unknown"))
        print("classes camera=%s virtual_camera=%s display=%s" % (Camera, VirtualCamera, Display))
        for flag in ["PIL_ENABLED", "FREENECT_ENABLED", "ZXING_ENABLED", "OCR_ENABLED", "PYSCREENSHOT_ENABLED", "ORANGE_ENABLED", "VIMBA_ENABLED"]:
            print("optional_flag %s=%s" % (flag, getattr(base, flag, "unknown")))
        print("sdl=%s" % os.environ.get("SDL_VIDEODRIVER", "unset"))
        if args.check_display:
            display = Display((64, 64), headless=True)
            display.quit()
            print("display_check=ok")
        print("status=ok")
        return 0
    except Exception as exc:
        print("status=failed error=%s: %s" % (exc.__class__.__name__, exc))
        print("hint=Check Python 2.7, OpenCV cv/cv2.cv, pygame, and SDL/headless settings before opening physical devices.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
