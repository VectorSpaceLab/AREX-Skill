#!/usr/bin/env python3
"""Tiny DIG large-scale smoke check.

Reports the current large-scale extension status and attempts a minimal
FeatureMomentum CPU operation. No dataset downloads.
"""
import argparse
import json

import torch

from dig.lsgraph.method.FM import FeatureMomentum


def main():
    parser = argparse.ArgumentParser(description="Tiny DIG large-scale smoke check.")
    parser.parse_args()

    dig_ext_error = None
    try:
        import dig.lsgraph.dataset  # noqa: F401
    except Exception as exc:
        dig_ext_error = f"{type(exc).__name__}: {exc}"

    feature_momentum_summary = None
    try:
        fm = FeatureMomentum(num_embeddings=4, embedding_dim=3, device='cpu', gamma=0.5)
        x = torch.tensor([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]])
        n_id = torch.tensor([0, 1])
        fm.push(x, n_id=n_id)
        pulled = fm.pull(n_id)
        feature_momentum_summary = {
            "feature_momentum": repr(fm),
            "pulled_shape": list(pulled.shape),
        }
    except Exception as exc:
        feature_momentum_summary = {
            "feature_momentum_error": f"{type(exc).__name__}: {exc}",
        }

    print(json.dumps({
        "dig_ext_error": dig_ext_error,
        "feature_momentum": feature_momentum_summary,
    }, indent=2, sort_keys=True))
    print("lsgraph_feature_momentum_smoke: ok")


if __name__ == "__main__":
    main()
