---
name: model-zoo-pretraining
description: "Select, instantiate, inspect, and troubleshoot DGL-LifeSci
  model-zoo architectures, pretrained models, readouts, molecule embeddings, and
  link prediction heads."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Model Zoo and Pretraining

Use this sub-skill when an agent needs to choose or instantiate `dgllife.model` architectures, inspect constructor compatibility, load pretrained models, produce molecule embeddings from pretrained GIN encoders, or wire link-prediction heads.

## Use This For

- Selecting among `dgllife.model.gnn`, `dgllife.model.readout`, `dgllife.model.model_zoo`, and `dgllife.model.load_pretrained` entry points.
- Matching graph feature tensors such as `g.ndata['h']`, `g.ndata['hv']`, `g.edata['e']`, or pretrained categorical lists to constructor parameters.
- Diagnosing constructor signatures, missing root exports, zero-in-degree errors, and pretrained checkpoint download failures.
- Adapting molecule embedding or link-prediction patterns without running large dataset downloads.

## Route Elsewhere

- For SMILES parsing, featurizers, graph construction, label masks, splitters, and dataset field names, use `../molecule-data-prep/SKILL.md`.
- For property prediction training loops, metrics, masking, and model evaluation workflows, use `../property-prediction/SKILL.md` after choosing the model here.
- For WLN reaction-center/ranking workflows and reaction-specific featurization, use `../reaction-prediction/SKILL.md`; this sub-skill only covers shared constructors and pretrained names.

## References

- Start with [references/model-catalog.md](references/model-catalog.md) for constructor families, feature dimensions, output expectations, pretrained names, molecule embedding, and link prediction usage.
- Use [references/constructor-recipes.md](references/constructor-recipes.md) for tiny CPU instantiation snippets and shape reasoning without data downloads.
- Use [references/troubleshooting.md](references/troubleshooting.md) for import/install, optional dependency, data/config, CLI/API misuse, pretrained download, zero-in-degree, and version/export caveats.
- Run [scripts/inspect_model_constructors.py](scripts/inspect_model_constructors.py) to print installed constructor signatures and optionally instantiate tiny CPU-safe constructors.

## Fast Workflow

1. Identify whether the user needs a GNN encoder, graph-level predictor, readout, pretrained model, molecule embedding encoder, or link-prediction head.
2. Check feature ownership: node and edge feature construction belongs to `molecule-data-prep`; this sub-skill only maps those tensor widths and field names into constructors.
3. Read `references/model-catalog.md` for the closest constructor family and any pretrained feature contract.
4. Validate the installed API with `python scripts/inspect_model_constructors.py --constructors GCNPredictor,GATPredictor,MPNNPredictor` before writing code that must run across DGL-LifeSci versions.
5. If pretrained checkpoints are needed, provide a no-network fallback plan because `load_pretrained()` downloads checkpoint files on first use.

## Version Caveats

The verified installed package was `dgllife` 0.3.1 with DGL 1.1.3 and CPU Torch. The source includes `GATv2Predictor`, but one installed inspection found no `GATv2Predictor` attribute at `dgllife.model`; prefer `GATv2` as the stable encoder and inspect submodule fallback availability before promising root-level `GATv2Predictor` imports.
