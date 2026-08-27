# Workflows

## Image-conditioned generation

1. Load the model and processor with `detikzify.model.load(...)`.
2. Build a `DetikzifyPipeline`.
3. Call `sample(image=...)` for one program, or `simulate(image=..., timeout=...)` for search.
4. Inspect `TikzDocument.is_rasterizable` and then `rasterize()` or `save()`.

## Text-conditioned generation

1. Load a model with `load_adapter(...)` or another adapter-capable path.
2. Pass `text=...` to `sample(...)` or `simulate(...)`.
3. Verify the adapter is active before assuming text prompts are supported.
4. Use `compile_timeout` to keep invalid TeX from stalling the workflow.

## Save and render

- `save("figure.tex")` writes the source code.
- `save("figure.pdf")` writes the compiled PDF when available.
- `save("figure.png")`, `save("figure.svg")`, or another raster extension writes an image only after rasterization succeeds.
- Check `has_content` when you need to know that the result is not just a blank page.

## Search-based synthesis

- `simulate()` returns scored candidates from the MCTS helper.
- Use `metric="model"` when you want the perceptual score path.
- Use `metric="fast"` when you only need compiler-diagnostics scoring.
- `strict=True` is useful when recoverable compile issues should still count as failures.

## When to stop and debug

- Stop if the loader cannot find the adapter or the expected model family.
- Stop if the document compiles but rasterization fails; that usually means the TeX / PDF toolchain is incomplete.
- Stop if the generated document is empty; do not assume a successful compile means usable output.
