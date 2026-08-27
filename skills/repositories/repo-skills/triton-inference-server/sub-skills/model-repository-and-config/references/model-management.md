# Model Management

Triton supports three control modes:

- `none`: load all models at startup and ignore live repository changes.
- `explicit`: load only the models named by `--load-model` and manage load/unload through APIs.
- `poll`: watch the repository and reload models when files change.

Important rules:

- `--load-model=*` must be the only `--load-model` argument.
- `--load-model` is only meaningful with `--model-control-mode=explicit`.
- `poll` can observe partial or incomplete repository edits, so it is risky for production unless updates are staged atomically.
- If a model is actively loading or unloading, do not mutate files in that model directory.
- Editing shared libraries used by a backend while loaded is unsafe; unload dependent models first.
- Repository index and model metadata APIs help confirm live state after a load/unload action.

For a live operator, the safest pattern is: stage a new model tree, switch the repository atomically, then confirm readiness or explicit load status.
