# CLI and Streamlit Viewer

## `simple-viewer`

The package installs a `simple-viewer` script. Its source writes a temporary Python file that imports `simpletransformers.streamlit.simple_view.streamlit_runner`, runs `streamlit run`, and then removes the temporary file.

Use it only when the user explicitly wants the interactive Streamlit viewer and accepts opening a local web server:

```bash
simple-viewer
```

Do not run `simple-viewer` as a verification smoke test: it starts a long-running server and writes a temporary file in the current directory. For non-interactive verification, use the root environment checker instead.

## Viewer prerequisites

- `streamlit` installed (package metadata includes it).
- A terminal/session where a web server can run.
- Any model files the viewer should load must exist and be readable.
- The active environment must import the relevant task model class cleanly.

## Safer alternatives

- Use sub-skill Python APIs for training/prediction.
- Use bundled validator scripts to inspect data files.
- Use `scripts/check_simpletransformers_env.py` for import/version/backend diagnostics.
