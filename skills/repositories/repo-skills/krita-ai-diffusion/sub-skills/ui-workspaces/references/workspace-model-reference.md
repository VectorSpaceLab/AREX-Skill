# Workspace Model Reference

`ai_diffusion.model.model.DocumentModel` is the main observable state object for
a Krita document. It stores UI settings, collects document/layer/region inputs,
launches generation jobs, listens to client/server messages, and updates job
history/progress/errors.

## Workspace enum

`Workspace` values:

```text
generation, upscaling, live, animation, custom
```

User-facing mapping:

- `generation`: ordinary prompt/image generation, refine, inpaint, region and
  control workflows.
- `upscaling`: super-resolution with optional diffusion refinement and tiling.
- `live`: automatically refresh preview output after changes.
- `animation`: batch processing keyframes/frames.
- `custom`: Graph workspace for custom ComfyUI workflows.

## DocumentModel persistent properties

Important persisted properties and defaults in this snapshot:

| Property | Default | Meaning |
| --- | --- | --- |
| `workspace` | `Workspace.generation` | Current workspace. |
| `style` | default style | Selected generation style. |
| `strength` | `1.0` | Refine/inpaint strength; values below 1 can route to refine. |
| `region_only` | `False` | Generate/refine only configured regions. |
| `edit_mode` | `False` | Edit-model mode and prompt behavior. |
| `batch_count` | `1` | Number of queued jobs for generation. |
| `seed` | `0` | Base seed. |
| `fixed_seed` | `False` | Reuse seed instead of generating new seeds. |
| `resolution_multiplier` | `1.0` | Generation resolution scale. |
| `queue_mode` | `QueueMode.back` | Add work at back, front, or replace queue. |
| `translation_enabled` | `True` | Use translation support when configured. |
| `layer_count` | `4` | Layered output count. |

Transient properties include `progress_kind`, `progress`, and `error`.

## Queue and job state

`QueueMode`:

```text
back, front, replace
```

`JobKind` includes:

```text
diffusion, control_layer, upscaling, live_preview, animation_batch,
animation_frame, animation
```

`JobState`:

```text
queued, executing, finished, cancelled
```

`ProgressKind`:

```text
generation, upload
```

The job queue tracks current, queued, finished, canceled, and selected jobs.
Server/client events update progress and errors. Disconnections can cancel or
lose a running job while later reconnects allow new jobs.

## Error model

`ErrorKind` values:

```text
none, plugin_error, server_error, insufficient_funds, warning,
incompatible_lora, validation_warning
```

Warnings have numeric values at or above `warning`. Custom Graph validation
errors surface as `validation_warning`; server/cloud errors map to server or
insufficient-funds kinds where appropriate.

## Connection state

Connection state is owned by the connection model and affects style filtering,
upscaler defaults, custom workflow loading, and generation ability.

Common values:

```text
disconnected, connecting, connected, error, discover_models, auth_missing,
auth_requesting, auth_pending, auth_error
```

When connected, `DocumentModel._init_on_connect()` filters styles supported by
client resources and sets the default upscaler if needed.

## Workspace-specific child models

- `model.inpaint`: custom inpaint controls such as mode, fill, prompt focus,
  context, and context layer.
- `model.upscale`: upscaler name, factor, diffusion toggle, strength, unblur,
  tile overlap mode/value, prompt usage, and `can_generate`.
- `model.live`: active/recording state, strength, and result availability.
- `model.animation`: sampling quality, target layer, and batch mode.
- `model.custom`: Graph workspace state; route to `custom-graphs` for details.
- `model.regions` and `model.edit_regions`: root region trees; route to
  `document-image-state` for region/layer details.

## Native evidence anchors

- `tests/test_model.py::test_generate_simple` proves no selection and strength
  1.0 forwards `WorkflowKind.generate` with no initial image.
- `tests/test_model.py::test_generate_refine` proves strength below 1.0 forwards
  `WorkflowKind.refine` with the document image.
- `tests/test_model.py::test_generate_inpaint` proves an active selection
  forwards `WorkflowKind.inpaint` with image and mask.
- `tests/test_model.py::test_generate_batch` proves wildcard batch generation
  queues multiple jobs.
- Job-processing tests in `tests/test_model.py` anchor progress, cancellation,
  server errors, and reconnect behavior.
- `tests/test_connection.py` and `tests/test_properties.py` anchor connection
  and observable property behavior.
