---
name: inference-and-rendering
description: "Load DeTikZify models and adapters, build inference pipelines,
  generate TikZ, compile and rasterize documents, and troubleshoot programmatic
  synthesis workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Inference and Rendering

Use this sub-skill when the task is about DeTikZify's Python inference surface: model loading, processor handling, adapter-backed text conditioning, `DetikzifyPipeline`, `DetikzifyGenerator`, `TikzDocument`, compile/rasterize/save, or MCTS-backed sampling.

Route away from this sub-skill when the main task is the browser UI, training loops, evaluation metrics, or dataset builders. Those workflows have dedicated sub-skills.

## Fast Path

1. Confirm the package imports and the public API surface is present:
   ```bash
   python scripts/api_smoke.py
   ```
2. For a rendering-specific smoke, compile a tiny document through the bundled helper:
   ```bash
   python scripts/tikz_smoke.py
   ```
3. If you need search-based synthesis or tree-search behavior, run the MCTS helper:
   ```bash
   python scripts/mcts_smoke.py
   ```

## What This Sub-Skill Owns

- `detikzify.model.load(...)` and `detikzify.model.load_adapter(...)`
- `DetikzifyProcessor` and `AdapterProcessor`
- `DetikzifyPipeline.sample(...)` and `DetikzifyPipeline.simulate(...)`
- `DetikzifyGenerator` and the MCTS bridge used inside the pipeline
- `TikzDocument.compile()`, `rasterize()`, `save()`, and error inspection
- image loading / preprocessing helpers that feed inference or rendering
- text-conditioned generation when an adapter is loaded

## Common Decisions

- Use `load(model_name_or_path, ...)` for image-conditioned generation with the default processor flow.
- Use `load_adapter(...)` or a model that already carries an adapter when the request needs text prompts.
- Use `sample(...)` for a single best TikZ program and `simulate(...)` when the user wants search / multiple candidates.
- Treat `metric="model"` as the perceptual path and `metric="fast"` as the compiler-diagnostics path.
- Set `preprocess=True` when you want the image trimmed and padded to a square before generation.
- Check `compile_timeout` and `mcts_timeout` separately; they control different stages.

## Bundled References

- [references/api-reference.md](references/api-reference.md): signatures and object roles for the public inference surface.
- [references/workflows.md](references/workflows.md): image-conditioned, text-conditioned, save/rasterize, and search-based workflows.
- [references/troubleshooting.md](references/troubleshooting.md): adapter, CUDA, image-source, and compile/rasterize failure modes.

## Related Helpers

- [../../scripts/api_smoke.py](../../scripts/api_smoke.py): safe import and signature snapshot.
- [../../scripts/tikz_smoke.py](../../scripts/tikz_smoke.py): safe TeX compile/rasterize smoke.
- [../../scripts/mcts_smoke.py](../../scripts/mcts_smoke.py): safe dummy-state MCTS sanity check.

## Guardrails

- A CPU import does not prove the GPU path works.
- Do not assume text prompts work unless an adapter-capable load path is active.
- Do not treat compile success as proof that the output is non-empty; check the rasterized result too.
