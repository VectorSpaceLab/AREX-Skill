#!/usr/bin/env python3
"""Read-only checks for a Frustum PointNets legacy runtime.

This helper never installs packages, compiles operators, downloads data, or
modifies the repository. It is intentionally tolerant of missing optional
TensorFlow/CUDA support so the report can explain which gate failed.
"""
import argparse
import json
import shutil
import subprocess
import sys


def probe():
    result = {
        "python": sys.version.split()[0],
        "executable": sys.executable,
        "packages": {},
        "tensorflow": {"imported": False, "graph_smoke": False, "gpus": [], "error": None},
        "tools": {name: shutil.which(name) is not None for name in ("nvcc", "g++")},
    }
    for name in ("numpy", "scipy", "cv2", "PIL", "tensorflow"):
        try:
            module = __import__(name)
            result["packages"][name] = getattr(module, "__version__", "present")
            if name == "tensorflow":
                result["tensorflow"]["imported"] = True
                try:
                    result["tensorflow"]["gpus"] = [d.name for d in module.config.list_physical_devices("GPU")]
                except Exception as exc:
                    result["tensorflow"]["error"] = "GPU probe: %s" % exc
                try:
                    with module.Graph().as_default():
                        x = module.placeholder(module.float32, shape=[None, 1])
                        y = module.reduce_sum(x)
                        with module.Session() as session:
                            value = session.run(y, {x: [[2.0]]})
                        result["tensorflow"]["graph_smoke"] = float(value) == 2.0
                except Exception as exc:
                    result["tensorflow"]["error"] = "graph smoke: %s" % exc
        except Exception as exc:
            result["packages"][name] = "ERROR: %s" % exc
            if name == "tensorflow":
                result["tensorflow"]["error"] = str(exc)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = parser.parse_args()
    result = probe()
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print("Python:", result["python"])
        print("TensorFlow:", result["packages"].get("tensorflow"))
        print("Graph smoke:", result["tensorflow"]["graph_smoke"])
        print("GPU devices:", result["tensorflow"]["gpus"] or "none")
        print("nvcc:", result["tools"]["nvcc"], "g++:", result["tools"]["g++"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
