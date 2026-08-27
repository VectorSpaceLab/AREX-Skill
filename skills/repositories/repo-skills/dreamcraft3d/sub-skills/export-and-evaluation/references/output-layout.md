# Output Layout

## Purpose

Read this when locating DreamCraft3D checkpoints, parsed configs, validation media, Gradio assets, or export results.

## Standard training output

The experiment config builds a trial directory from:

```text
<exp_root_dir>/<name>/<tag><timestamp>
```

For canonical configs, `exp_root_dir` is `outputs`, `name` is the config name, and `tag` is normally the prompt with spaces replaced by underscores. The README examples refer to `@LAST` as a placeholder for the actual timestamp/tag directory.

Typical trial tree:

```text
outputs/dreamcraft3d-texture/<prompt-tag>@.../
  ckpts/
    last.ckpt
  configs/
    parsed.yaml
  save/
    it<step>-val.mp4
    it<step>-test.mp4
    it<step>-export/
      model.obj
      model.mtl
      *.jpg
  tb_logs/
  csv_logs/
  cmd.txt
```

Exact subfolders depend on the launch mode and callbacks.

## Checkpoint handoff

| Producing stage | Consumer override |
| --- | --- |
| coarse NeRF `ckpts/last.ckpt` | coarse NeuS `system.weights=<ckpt>` |
| coarse NeuS `ckpts/last.ckpt` | geometry `system.geometry_convert_from=<ckpt>` |
| geometry `ckpts/last.ckpt` | texture `system.geometry_convert_from=<ckpt>` |
| texture `ckpts/last.ckpt` | export `resume=<ckpt>` |

Keep these override names distinct. `system.weights` is used by the coarse NeuS path, while `system.geometry_convert_from` is used by geometry and texture conversion.

## Gradio output

The Gradio app uses `outputs-gradio` as its experiment root. It creates trial directories based on selected demo configs and timestamp tags. It reads progress from a `progress` file, logs from `logs`, and images/videos/meshes from `save/`.

This checkout's Gradio app references generic `configs/gradio/*.yaml` paths; verify those files exist before promising that the generic UI can launch.

## What to summarize

Use the bundled summarizer to answer:

- Does a trial directory exist?
- Does `ckpts/last.ckpt` exist?
- Does `configs/parsed.yaml` exist?
- Which PNG/MP4 files are in `save/`?
- Are there export directories and OBJ/MTL/texture files?
- Is the trial ready for export, or only ready for inspection?

## Common ambiguity

Prompt tags are shell/path-safe derivations, not natural-language prompts. If a user cannot find a directory, search under `outputs/<stage-name>/` and inspect `cmd.txt` or `configs/parsed.yaml` rather than guessing the tag.
