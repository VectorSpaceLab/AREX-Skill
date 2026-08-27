#!/usr/bin/env python3
"""Check optional DALLE-pytorch backend imports safely."""
import argparse, importlib, json


def import_status(name):
    try:
        mod = importlib.import_module(name)
        return {"available": True, "version": getattr(mod, "__version__", None)}
    except Exception as exc:
        return {"available": False, "error": f"{type(exc).__name__}: {exc}"}


def main():
    p = argparse.ArgumentParser(description="Inspect DALLE-pytorch backend availability without launching distributed jobs.")
    p.add_argument("--include-cuda", action="store_true")
    p.add_argument("--json", action="store_true")
    args = p.parse_args()
    report = {
        "modules": {
            "torch": import_status("torch"),
            "deepspeed": import_status("deepspeed"),
            "horovod.torch": import_status("horovod.torch"),
            "dalle_pytorch.distributed_utils": import_status("dalle_pytorch.distributed_utils"),
        },
        "cuda": None,
    }
    if args.include_cuda:
        try:
            import torch
            cuda = {
                "available": bool(torch.cuda.is_available()),
                "device_count": int(torch.cuda.device_count()),
                "torch_cuda": torch.version.cuda,
            }
            if torch.cuda.is_available():
                x = torch.empty((1,), device="cuda")
                cuda["device_name_0"] = torch.cuda.get_device_name(0)
                cuda["device_capability_0"] = torch.cuda.get_device_capability(0)
                cuda["allocation_device"] = str(x.device)
            report["cuda"] = cuda
        except Exception as exc:
            report["cuda"] = {"available": False, "error": f"{type(exc).__name__}: {exc}"}
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        for name, status in report["modules"].items():
            print(f"{name}: {'available' if status['available'] else 'missing'} {status.get('version') or status.get('error') or ''}")
        if report["cuda"] is not None:
            print(f"cuda: {report['cuda']}")


if __name__ == "__main__":
    main()
