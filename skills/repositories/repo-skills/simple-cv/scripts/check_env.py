#!/usr/bin/env python
"""Diagnose a SimpleCV runtime without relying on the current directory.

Usage examples:
  python check_env.py
  python check_env.py --repo-root /path/to/SimpleCV-checkout
  SDL_VIDEODRIVER=dummy python check_env.py --strict-optional
"""
from __future__ import print_function

import argparse
import os
import sys

CORE_MODULES = [
    ("cv2", "OpenCV Python module"),
    ("cv", "OpenCV 2.x compatibility module required by SimpleCV"),
    ("numpy", "numeric arrays"),
    ("scipy", "image/math helpers"),
    ("PIL", "Pillow/PIL image helpers"),
    ("pygame", "display/image surface helpers"),
    ("svgwrite", "SVG output helpers"),
]

OPTIONAL_MODULES = [
    ("freenect", "Kinect support"),
    ("zxing", "barcode support"),
    ("tesseract", "OCR support"),
    ("pyscreenshot", "screen capture support"),
    ("orange", "Orange legacy ML support"),
    ("Orange", "Orange package alias"),
    ("pymba", "Vimba/industrial camera support"),
]


def add_repo_root(path):
    if not path:
        return
    root = os.path.abspath(path)
    if root not in sys.path:
        sys.path.insert(0, root)
    print("added_repo_root=%s" % root)


def import_one(name):
    try:
        module = __import__(name)
        version = getattr(module, "__version__", None)
        if version is None and name == "PIL":
            version = getattr(module, "VERSION", None)
        return True, version or "unknown", None
    except Exception as exc:
        return False, None, "%s: %s" % (exc.__class__.__name__, exc)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Check SimpleCV importability and optional runtime modules.")
    parser.add_argument("--repo-root", help="Optional SimpleCV checkout to add to sys.path before importing.")
    parser.add_argument("--strict-optional", action="store_true", help="Exit nonzero when optional integrations are missing.")
    args = parser.parse_args(argv)

    add_repo_root(args.repo_root)

    failures = []
    print("python=%s" % sys.version.replace("\n", " "))

    for name, purpose in CORE_MODULES:
        ok, version, err = import_one(name)
        if ok:
            print("core_ok %s version=%s purpose=%s" % (name, version, purpose))
        else:
            print("core_fail %s purpose=%s error=%s" % (name, purpose, err))
            failures.append(name)

    ok, version, err = import_one("SimpleCV")
    if ok:
        import SimpleCV
        print("simplecv_ok version=%s" % getattr(SimpleCV, "__version__", version))
        try:
            from SimpleCV import Image, Color, Camera, Display
            img = Image("simplecv")
            print("sample_image_ok size=%s color_red=%s camera=%s display=%s" % (img.size(), Color.RED, Camera, Display))
        except Exception as exc:
            print("simplecv_smoke_fail error=%s: %s" % (exc.__class__.__name__, exc))
            failures.append("SimpleCV-smoke")
    else:
        print("simplecv_fail error=%s" % err)
        print("hint=SimpleCV 1.3 expects Python 2.7 and OpenCV 2.4-style cv/cv2.cv bindings.")
        failures.append("SimpleCV")

    optional_failures = []
    for name, purpose in OPTIONAL_MODULES:
        ok, version, err = import_one(name)
        if ok:
            print("optional_ok %s version=%s purpose=%s" % (name, version, purpose))
        else:
            print("optional_missing %s purpose=%s error=%s" % (name, purpose, err))
            optional_failures.append(name)

    if failures:
        print("status=failed core_failures=%s" % ",".join(failures))
        return 1
    if args.strict_optional and optional_failures:
        print("status=failed optional_failures=%s" % ",".join(optional_failures))
        return 2
    print("status=ok optional_missing=%s" % (",".join(optional_failures) if optional_failures else "none"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
