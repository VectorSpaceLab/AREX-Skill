# CLI Reference

`python -m detikzify.webui` accepts the following options:

- `--model MODEL`
  - Default model shown in the UI.
  - Can also be a local path or another model identifier.
- `--algorithm {mcts,sampling}`
  - Chooses between the search-based and sampling-based UI flow.
- `--lock`
  - Prevents users from changing the model interactively.
- `--lock_reason LOCK_REASON`
  - Extra explanation shown when model selection is locked.
- `--share`
  - Launches Gradio with a shareable public link.
- `--light`
  - Forces the light theme.
- `--timeout TIMEOUT`
  - Allowed compilation window in seconds for the UI's rendering path.

## Runtime model list

The UI shows the v2 / v2.5 models by default and adds legacy v1 choices when `timm` is installed.

## Algorithm choice

- `mcts`: best when the user wants multiple compiled candidates and ranked outputs.
- `sampling`: best when the user wants one output image and a simpler interaction loop.
