---
name: checkpoints
description: "Manage Luminoth checkpoint indexes, remote downloads, local
  metadata, and shareable checkpoint tarballs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Luminoth Checkpoints

Use this sub-skill when the task is to inspect, refresh, download, create,
edit, delete, import, export, or troubleshoot Luminoth checkpoints and their
local index. Checkpoints are Luminoth's packaged model weights plus metadata;
using a checkpoint for inference is routed to the prediction sibling.

## Route here for

- `lumi checkpoint list`, `info`, `refresh`, `download`, `create`, `edit`,
  `delete`, `export`, or `import` command planning.
- Local checkpoint database inspection under `$LUMI_HOME/checkpoints/checkpoints.json`
  or the default user home state.
- Remote index refresh/download behavior, including the `LUMI_REMOTE_URL`
  override.
- Packaging a completed local training run into a named checkpoint alias and
  sharing it as a tar file.
- Alias-versus-id resolution problems, duplicate aliases, stale checkpoint
  directories, and missing TensorFlow checkpoint files.

## Do not use this sub-skill alone for

- Prediction CLI, Python `Detector`, visualization, or the demo web server;
  route to [prediction](../prediction/SKILL.md) after the checkpoint is present.
- Training or evaluation lifecycle details; route to
  [training](../training/SKILL.md) to produce or validate a run directory before
  returning here for `lumi checkpoint create`.
- Dataset conversion, TFRecord layouts, or `classes.json` generation; route to
  [dataset-preparation](../dataset-preparation/SKILL.md).
- Cross-cutting install/import/TensorFlow/Python-version failures; start at the
  [root Luminoth router](../../SKILL.md) and its root troubleshooting reference.

## Fast operating procedure

1. Decide which Luminoth home should be read or mutated. Luminoth uses
   `~/.luminoth` unless `LUMI_HOME=/path/to/home` is set for the command.
2. Inspect current state without network access before mutating it:

   ```bash
   python scripts/inspect_checkpoint_index.py
   # or isolate a job/user:
   LUMI_HOME=/path/to/lumi-home python scripts/inspect_checkpoint_index.py --id-or-alias traffic
   ```

3. Read [references/workflows.md](references/workflows.md) for command recipes,
   storage layout, local/remote state transitions, metadata fields, tar
   import/export, and alias-vs-id rules.
4. Read [references/troubleshooting.md](references/troubleshooting.md) when a
   command reports a missing run checkpoint, duplicate id/alias, already
   downloaded checkpoint, stale directory, invalid tar, malformed index, or
   remote index failure.
5. Prefer exact checkpoint ids for destructive or ambiguous operations. Aliases
   are friendly labels, but this Luminoth version can keep duplicate aliases
   and resolves local/newer matches before remote/older matches.

## Common commands at a glance

```bash
lumi checkpoint list
lumi checkpoint info accurate
lumi checkpoint refresh                     # network: remote index
lumi checkpoint download accurate           # network: tar download, then import files
lumi checkpoint create config.yml -e name="OpenImages Traffic" -e alias=traffic
lumi checkpoint edit traffic -e description="Model trained for traffic scenes."
lumi checkpoint export traffic --output ./checkpoint-tars
lumi checkpoint import ./checkpoint-tars/<checkpoint-id>.tar
lumi checkpoint delete <checkpoint-id>
```

For any workflow that crosses from training into packaging, from checkpoint
selection into prediction/server use, or from dataset conversion into
`classes.json`, keep the root router and the owning sibling sub-skill in the
conversation instead of duplicating their full guidance here.
