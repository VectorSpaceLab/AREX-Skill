# Export and Evaluation Troubleshooting

## Missing parsed config

**Symptoms**
- Export command cannot open `<trial-dir>/configs/parsed.yaml`.

**Likely causes**
- The trial did not finish config snapshotting.
- The path points to a stage root instead of a timestamped trial directory.
- The user copied only checkpoints without configs.

**Recovery**
- Summarize the trial directory and locate `configs/parsed.yaml`.
- If only the original config is available, reconstruct all runtime overrides carefully before export.

## Missing checkpoint

**Symptoms**
- `resume=<trial-dir>/ckpts/last.ckpt` fails.
- Export starts but cannot restore system state.

**Likely causes**
- Training did not reach checkpoint save.
- The prompt tag or output root is wrong.
- The checkpoint came from an incompatible stage.

**Recovery**
- Use the output summarizer with `--require-checkpoint`.
- Match checkpoint stage to exporter goal: texture for final OBJ/MTL, geometry for geometry inspection.

## nvdiffrast/OpenGL context failure

**Symptoms**
- Export or rendering fails on a headless server/container with OpenGL/EGL context errors.

**Likely causes**
- The exporter default context is `gl`.
- Docker/headless environment lacks usable OpenGL display context.

**Recovery**
- Add `system.exporter.context_type=cuda` to export commands.
- For training renderers that support it, add the corresponding `system.renderer.context_type=cuda` override.
- Verify CUDA torch and nvdiffrast are installed in the same environment.

## Texture not saved or white/default material

**Symptoms**
- OBJ exists but no expected texture maps.
- Export warns that `save_texture` is true but no albedo texture was found.

**Likely causes**
- Exporting from a geometry-only or incomplete stage.
- `save_uv` is false while texture saving is requested.
- Material implementation did not produce texture fields.

**Recovery**
- Export from a completed texture stage when final appearance matters.
- Ensure `system.exporter.save_uv=true` if `save_texture=true`.
- Check trial stage and material config before rerunning.

## Metrics fail to import or download models

**Symptoms**
- Import errors for CLIP/Transformers/LPIPS/contextual loss.
- Metric run attempts downloads or fails without cached model files.

**Likely causes**
- Metrics are optional and use additional model dependencies.
- Offline environment lacks model caches.

**Recovery**
- Treat metrics as optional evaluation, not export validation.
- Confirm input image lists, prediction patterns, and caches before running.
- Use visual/video artifacts and output summary for a cheap first check.
