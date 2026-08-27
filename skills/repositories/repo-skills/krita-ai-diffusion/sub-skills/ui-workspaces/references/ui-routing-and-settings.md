# UI Routing and Settings Reference

Use this reference to connect user-facing workspace controls and settings to
model/backend behavior.

## Generation routing

When `DocumentModel.generate()` is called, it first validates document color
mode, collects active document/layer/selection/region state, resolves style and
client models, then enqueues one or more jobs according to workspace state.

Common routing rules:

- No selection and `strength == 1.0` usually creates `WorkflowKind.generate`.
- Existing image/canvas with `strength < 1.0` usually creates
  `WorkflowKind.refine`.
- Active selection or inpaint operation creates `WorkflowKind.inpaint` with an
  initial image and mask.
- Batch count queues multiple jobs; fixed seed controls deterministic wildcard
  behavior.
- Upscale workspace selects simple or diffusion-tiled upscale according to
  upscaler/diffusion/tile settings.
- Live workspace creates live preview jobs and uses live strength/sampler values.
- Custom workspace delegates to Graph workspace collection and parameter logic.
- Animation workspace batches frame/keyframe work and may use custom workflow
  animation mode.

## Settings classes and enums

Important settings enums:

- `ServerMode`: `undefined`, `managed`, `external`, `cloud`.
- `ServerBackend`: `cpu`, `cuda`, `mps`, `directml`, `xpu`, `rocm` with
  platform support filtering.
- `GenerationFinishedAction`: `none`, `preview`, `apply`.
- `ApplyBehavior`: `replace`, `layer`, `layer_active`.
- `ApplyRegionBehavior`: `none`, `replace`, `layer_group`,
  `transparency_mask`, `no_hide`.
- `PerformancePreset`: `auto`, `cpu`, `low`, `medium`, `high`, `cloud`,
  `custom`.
- `ImageFileFormat`: `png`, `png_small`, `webp`, `webp_lossless`, `jpeg`.

Common settings fields:

- Server mode, path, URL, backend, arguments, authorization token, and whether to
  refuse connection when resources are missing.
- Selection feather/grow behavior and inpaint defaults.
- Apply behavior for finished images and region outputs.
- Performance preset, batch size, resolution multiplier, max pixel count,
  dynamic caching, and tiled VAE.
- Auto-update and language settings.

## Headless model testing

For headless model tests or inspections:

```bash
export QT_QPA_PLATFORM=offscreen
python sub-skills/ui-workspaces/scripts/inspect_workspace_enums.py --static-only
```

Use live import mode only when `ai_diffusion` imports successfully:

```bash
QT_QPA_PLATFORM=offscreen python sub-skills/ui-workspaces/scripts/inspect_workspace_enums.py --import-live
```

Do not construct `QWidget` classes without `QApplication`. For model/QObject
classes, ensure a `QCoreApplication` exists.

## Persistence boundaries

- UI/model properties marked `persist=True` are saved into document or settings
  persistence layers.
- Runtime-only properties such as progress, errors, live result availability,
  and connection state should not be treated as stable project settings.
- Custom workflow parameters are stored per workflow ID in the custom workspace.
- Style selection refers to style files managed by the `Styles` collection;
  route style JSON content to `document-image-state`.

## Applying generated results

Apply behavior determines whether results replace the active layer, create a new
layer, create a layer above active, or update regions/layer groups. This crosses
with layer/document APIs. If a bug report is about layer order, masks,
transparency, or region groups after generation, route to `document-image-state`
for data manipulation and keep this sub-skill for UI setting/state origin.
