#!/usr/bin/env python3
"""Safe Dexbotic package, dependency, and CUDA diagnostic; no installs/downloads."""
from __future__ import annotations
import importlib, importlib.metadata, json

def ver(name):
    try:return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:return None

def main():
    modules=["dexbotic","dexbotic.client","dexbotic.policy.base_policy","dexbotic.policy.types","dexbotic.data.dataset.dex_dataset","dexbotic.exp.backend_resolver"]
    result={"packages":{n:ver(n) for n in ["dexbotic","torch","torchvision","transformers","accelerate","deepspeed","triton"]},"imports":{},"cuda":{}}
    for m in modules:
        try: importlib.import_module(m); result["imports"][m]="ok"
        except Exception as e: result["imports"][m]=repr(e)
    try:
        import torch
        result["cuda"]={"available":bool(torch.cuda.is_available()),"device_count":torch.cuda.device_count()}
        if torch.cuda.is_available():
            x=torch.zeros(1,device="cuda"); result["cuda"]["allocation"]="ok"; result["cuda"]["device"]=torch.cuda.get_device_name(0); del x
    except Exception as e: result["cuda"]["error"]=repr(e)
    print(json.dumps(result,indent=2))
if __name__=="__main__":main()
