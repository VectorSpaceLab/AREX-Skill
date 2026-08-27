# API Reference

## Public entry points

- `detikzify.model.load(model_name_or_path, modality_projector=None, is_v1=False, **kwargs)`
  - Loads the model and processor for the current generation family.
  - Switches to the legacy v1 path when `is_v1=True`, `timm` is available, or the model name matches a legacy alias.
- `detikzify.model.load_adapter(model, processor, adapter_name_or_path=None, **kwargs)`
  - Wraps the processor for text-conditioned adapter workflows.
- `detikzify.infer.DetikzifyPipeline(model, processor, temperature=0.8, top_p=0.95, top_k=0, compile_timeout=60, metric="model", **gen_kwargs)`
  - High-level generation wrapper used by both sampling and MCTS.
- `DetikzifyPipeline.sample(image=None, text=None, preprocess=True, **gen_kwargs)`
  - Generates one TikZ document and returns a `TikzDocument`.
- `DetikzifyPipeline.simulate(image=None, text=None, preprocess=True, expansions=None, timeout=None, **gen_kwargs)`
  - Iterates over MCTS rollouts and yields `(score, TikzDocument)` pairs.
- `detikzify.infer.TikzDocument(code, timeout=60)`
  - Wraps TikZ source code and exposes `compile`, `rasterize`, `save`, and error helpers.
- `detikzify.model.DetikzifyProcessor(...)`
  - Image-plus-text processor for the v2 family.
- `detikzify.model.adapter.AdapterProcessor(...)`
  - Processor wrapper for the adapter/text-conditioning path.

## Practical signatures and behaviors

- `TikzDocument.compile()` returns an object with `status`, `pdf`, and `log`.
- `TikzDocument.rasterize()` returns a PIL image when compilation produced a usable PDF.
- `TikzDocument.save(filename)` writes `.tex`, `.pdf`, or raster image output depending on the extension.
- `DetikzifyProcessor.__call__` expects `images=` and optional text; it prepends image tokens automatically.
- `AdapterProcessor.__call__` can accept text alone, images alone, or both, but text-conditioned use requires the adapter path.
- `ImageSim.from_detikzify(model, processor, ...)` is the perceptual metric path used by MCTS and evaluation.

## Key constraints

- `sample()` is best for one best-effort result.
- `simulate()` is best when you need multiple candidates or search-time control.
- `strict=True` treats recoverable compile issues as fatal when computing search scores.
- `preprocess=True` trims whitespace and pads to square before generation.
- `compile_timeout` applies to TeX compilation; `mcts_timeout` applies to search duration.
