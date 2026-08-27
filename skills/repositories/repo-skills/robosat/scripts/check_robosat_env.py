#!/usr/bin/env python3
"""Check whether an installed RoboSat environment is ready for basic use."""

import argparse
import importlib
import shutil
import subprocess
import sys


def check_import(name, errors, optional=False):
    try:
        module = importlib.import_module(name)
        version = getattr(module, "__version__", None)
        if version:
            print("OK import {} {}".format(name, version))
        else:
            print("OK import {}".format(name))
        return module
    except Exception as exc:
        label = "WARN" if optional else "ERROR"
        print("{} import {} failed: {}".format(label, name, exc), file=sys.stderr)
        if not optional:
            errors.append("import {} failed".format(name))
        return None


def check_pyproj(errors):
    pyproj = check_import("pyproj", errors)
    if pyproj is None:
        return
    try:
        from pyproj import CRS
        CRS.from_user_input("ESRI:54009")
        print("OK pyproj resolves ESRI:54009 equal-area CRS")
    except Exception as exc:
        errors.append("pyproj cannot resolve ESRI:54009")
        print(
            "ERROR pyproj cannot resolve ESRI:54009: {}. "
            "Use a pyproj/proj-data combination that includes ESRI authorities; "
            "pyproj 2.6.x is a known compatible 2.x line for RoboSat.".format(exc),
            file=sys.stderr,
        )


def check_rtree(errors):
    try:
        from rtree.index import Index, Property  # noqa: F401
        print("OK rtree imports libspatialindex")
    except Exception as exc:
        errors.append("rtree/libspatialindex unavailable")
        print(
            "ERROR rtree could not import libspatialindex: {}. "
            "Install libspatialindex (for example OS package libspatialindex or conda-forge libspatialindex).".format(exc),
            file=sys.stderr,
        )


def check_torch(optional_cuda, errors):
    torch = check_import("torch", errors, optional=False)
    torchvision = check_import("torchvision", errors, optional=False)
    if torch is None or torchvision is None:
        return
    cuda = bool(torch.cuda.is_available())
    print("OK torch cuda_available={}".format(cuda))
    if optional_cuda and not cuda:
        print("WARN CUDA requested for this check but torch reports cuda_available=False", file=sys.stderr)


def run_help_command(cmd, label, errors):
    try:
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, timeout=20)
    except Exception as exc:
        errors.append("{} help failed".format(label))
        print("ERROR {} help command failed: {}".format(label, exc), file=sys.stderr)
        return
    if proc.returncode != 0:
        errors.append("{} help returned nonzero".format(label))
        print("ERROR {} help returned {}".format(label, proc.returncode), file=sys.stderr)
        if proc.stderr:
            print(proc.stderr.strip(), file=sys.stderr)
    else:
        first = proc.stdout.splitlines()[0] if proc.stdout else "help produced no stdout"
        print("OK {}: {}".format(label, first))


def check_cli(errors):
    exe = shutil.which("rs")
    if not exe:
        print("WARN rs console script not found on PATH; trying python -m robosat.tools", file=sys.stderr)
        base = [sys.executable, "-m", "robosat.tools"]
    else:
        base = [exe]

    commands = [
        ("root help", base + ["--help"]),
        ("extract help", base + ["extract", "--help"]),
        ("cover help", base + ["cover", "--help"]),
        ("download help", base + ["download", "--help"]),
        ("rasterize help", base + ["rasterize", "--help"]),
        ("train help", base + ["train", "--help"]),
        ("export help", base + ["export", "--help"]),
        ("predict help", base + ["predict", "--help"]),
        ("masks help", base + ["masks", "--help"]),
        ("features help", base + ["features", "--help"]),
        ("merge help", base + ["merge", "--help"]),
        ("dedupe help", base + ["dedupe", "--help"]),
        ("serve help", base + ["serve", "--help"]),
        ("weights help", base + ["weights", "--help"]),
        ("compare help", base + ["compare", "--help"]),
        ("subset help", base + ["subset", "--help"]),
    ]

    for label, cmd in commands:
        run_help_command(cmd, label, errors)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Check an installed RoboSat runtime environment.")
    parser.add_argument("--check-cli", action="store_true", help="also run rs --help or python -m robosat.tools --help")
    parser.add_argument("--expect-cuda", action="store_true", help="warn if torch CUDA is unavailable")
    args = parser.parse_args(argv)

    errors = []
    check_import("robosat", errors)
    check_import("mercantile", errors)
    check_import("PIL", errors)
    check_pyproj(errors)
    check_rtree(errors)
    check_torch(args.expect_cuda, errors)
    if args.check_cli:
        check_cli(errors)

    if errors:
        print("RoboSat environment check failed: {}".format(", ".join(errors)), file=sys.stderr)
        return 1
    print("RoboSat environment check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
