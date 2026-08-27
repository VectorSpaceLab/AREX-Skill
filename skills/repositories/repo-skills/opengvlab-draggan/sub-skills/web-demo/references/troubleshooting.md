# Web demo troubleshooting

## Purpose

Read this when the browser UI launches but does not behave as expected.

## Symptoms and fixes

### The UI launches, but `Drag it` fails immediately

Most often this means the environment does not have a usable CUDA backend.
Run `../../scripts/check_install.py --mode web` and confirm the CUDA check passes before retrying.

### The model dropdown is slow or stalls on first use

The checkpoint is probably being downloaded into the cache root.
Check `../../references/checkpoints.md` for the cache location and the checkpoint name spelling.

### `Undo Last` or `Reset All` behaves strangely

Those controls only manage the point lists and the current seeded image in the browser state.
If the drag loop never started, there may be no history to undo.

### The mask tab does nothing

That is expected in this snapshot.
The current optimizer does not enforce the mask, so the tab should be treated as a placeholder rather than a protected-region tool.

### Uploading a custom image fails

Treat uploaded-image inversion as experimental.
If the upload path raises an error, fall back to the seeded-image workflow and treat the upload path as non-essential.

### Saved files are hard to find

Look for the `draggan_tmp/` directory under the current working directory where the launcher was started.

## When to stop

If the failure is a missing checkpoint, missing CUDA backend, or a broken Gradio import stack, fix the environment first rather than retrying the browser workflow.
