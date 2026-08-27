#!/usr/bin/env python3
"""Inspect key Megatron Core API signatures without starting training."""

from __future__ import annotations

import inspect
import json


def main() -> int:
    import torch
    import megatron.core as mcore
    from megatron.core.models.gpt.gpt_layer_specs import get_gpt_layer_local_spec
    from megatron.core.models.gpt.gpt_model import GPTModel
    from megatron.core.transformer.transformer_config import TransformerConfig

    cfg_fields = list(getattr(TransformerConfig, "__dataclass_fields__", {}).keys())
    report = {
        "megatron_core_version": getattr(mcore, "__version__", None),
        "torch_version": torch.__version__,
        "torch_cuda": getattr(torch.version, "cuda", None),
        "TransformerConfig_first_fields": cfg_fields[:30],
        "GPTModel_signature": str(inspect.signature(GPTModel)),
        "local_gpt_layer_spec_type": type(get_gpt_layer_local_spec()).__name__,
    }
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
