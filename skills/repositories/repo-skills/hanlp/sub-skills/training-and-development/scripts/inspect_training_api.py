#!/usr/bin/env python3
"""Inspect HanLP training-related API signatures without downloading or training."""
from __future__ import annotations
import argparse, inspect, json

def collect():
    import hanlp
    from hanlp.common.torch_component import TorchComponent
    from hanlp.components.tokenizers.transformer import TransformerTaggingTokenizer
    from hanlp.components.mtl.multi_task_learning import MultiTaskLearning
    from hanlp.components.classifiers.transformer_classifier import TransformerClassifier
    return {
        "hanlp_version": getattr(hanlp, "__version__", None),
        "TorchComponent.fit": str(inspect.signature(TorchComponent.fit)),
        "TorchComponent.evaluate": str(inspect.signature(TorchComponent.evaluate)),
        "TorchComponent.load": str(inspect.signature(TorchComponent.load)),
        "TransformerTaggingTokenizer.fit": str(inspect.signature(TransformerTaggingTokenizer.fit)),
        "MultiTaskLearning.fit": str(inspect.signature(MultiTaskLearning.fit)),
        "TransformerClassifier.fit": str(inspect.signature(TransformerClassifier.fit)),
    }

def main():
    ap = argparse.ArgumentParser(description="Print HanLP training API signatures without running training.")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(); data = collect()
    print(json.dumps(data, ensure_ascii=False, indent=2) if a.json else "\n".join(f"{k}: {v}" for k,v in data.items()))
    return 0
if __name__ == "__main__": raise SystemExit(main())
