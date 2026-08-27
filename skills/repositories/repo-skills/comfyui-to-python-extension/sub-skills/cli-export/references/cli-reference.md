# CLI Reference

## Commands

Run the exporter from a source checkout:

```bash
python -m comfyui_to_python
```

Run it with explicit file paths:

```bash
python -m comfyui_to_python -f workflow_api.json -o workflow_api.py -q 10
```

Legacy wrapper:

```bash
python comfyui_to_python.py
```

## Flags

| Flag | Default | Meaning |
| --- | --- | --- |
| `-f`, `--input_file` | `workflow_api.json` | Path to the API-format workflow JSON. |
| `-o`, `--output_file` | `workflow_api.py` | Path to the generated Python file. |
| `-q`, `--queue_size` | `10` | Number of workflow iterations rendered into the exported script. |

## CLI behavior

- `main()` parses the flags and calls `run(...)`.
- `run(...)` uses `needs_init_custom_nodes=True`, so the exporter can initialize ComfyUI custom nodes when the workflow needs them.
- `ComfyUItoPython(...)` can also be used directly from Python code when a script wants to supply inline workflow JSON or a custom mapping.
- The exporter writes formatted Python via `black`.

## Practical guidance

- Use `File -> Export (API)` in ComfyUI first if the workflow started in the UI.
- Keep the output filename explicit when you want the generated script in a different location.
- Pass a larger queue size only when the workflow should be repeated in the generated runner.
