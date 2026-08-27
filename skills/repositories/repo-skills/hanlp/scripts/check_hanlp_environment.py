#!/usr/bin/env python3
"""Safe HanLP environment diagnostic without model downloads or RESTful calls."""
from __future__ import annotations
import argparse, importlib, json, os
from importlib import metadata

DISTS = ["hanlp", "hanlp-common", "hanlp-trie", "hanlp-restful", "torch", "transformers"]
MODULES = ["hanlp", "hanlp_common", "hanlp_trie", "hanlp_restful"]
ENV_VARS = ["HANLP_HOME", "HANLP_URL", "HANLP_VERBOSE", "HANLP_AUTH", "CUDA_VISIBLE_DEVICES", "TRANSFORMERS_OFFLINE"]

def dist_version(name):
    try: return metadata.version(name)
    except metadata.PackageNotFoundError: return None

def main():
    ap = argparse.ArgumentParser(description="Check HanLP imports, versions, and backend/cache signals.")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    out = {"distributions": {d: dist_version(d) for d in DISTS}, "imports": {}, "env": {}, "pretrained_count": None, "torch": None}
    for name in ENV_VARS:
        out["env"][name] = "<set>" if name == "HANLP_AUTH" and os.getenv(name) else os.getenv(name)
    for m in MODULES:
        try:
            mod = importlib.import_module(m)
            out["imports"][m] = {"ok": True, "version": getattr(mod, "__version__", None)}
        except Exception as e:
            out["imports"][m] = {"ok": False, "error": f"{type(e).__name__}: {e}"}
    try:
        import hanlp
        out["pretrained_count"] = len(getattr(hanlp.pretrained, "ALL", {}))
    except Exception as e:
        out["pretrained_error"] = f"{type(e).__name__}: {e}"
    try:
        import torch
        avail = bool(torch.cuda.is_available())
        out["torch"] = {"version": torch.__version__, "cuda_version": torch.version.cuda, "cuda_available": avail, "cuda_device_count": torch.cuda.device_count() if avail else 0}
        if avail:
            out["torch"]["cuda_device_0"] = torch.cuda.get_device_name(0)
    except Exception as e:
        out["torch"] = {"error": f"{type(e).__name__}: {e}"}
    ok = all(v.get("ok") for v in out["imports"].values())
    if args.json:
        print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        print("HanLP environment diagnostic")
        print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0 if ok else 1

if __name__ == "__main__":
    raise SystemExit(main())
