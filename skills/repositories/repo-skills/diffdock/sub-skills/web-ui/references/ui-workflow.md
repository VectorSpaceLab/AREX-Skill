# DiffDock Gradio UI Workflow

## What The App Does

DiffDock's Gradio app is a single-complex front end for inference. It gathers one protein, one ligand, an optional YAML config, and a sample count, then calls the same inference script used by the command-line workflow. The app returns a completion message, a downloadable zip archive, and an optional browser visualization for ranked samples.

Use the UI for quick interactive docking demos and small exploratory runs. Use `../docking-inference/SKILL.md` for bulk CSV inference, full command-line flag control, reproducible scripted runs, and deeper inference configuration.

## Launching Locally

Minimal launch pattern after the DiffDock runtime stack and app dependencies are installed:

```bash
python app/main.py
```

Then open `http://localhost:7860` in a browser.

To choose a port:

```bash
GRADIO_SERVER_PORT=7861 python app/main.py
```

The app binds to `0.0.0.0`, so remote access depends on host firewall, container, SSH forwarding, or platform networking rules. The app does not enable Gradio public sharing by default.

## Import And Working Directory Behavior

The UI source is script-style rather than packaged as a normal Python package. The main app imports `mol_viewer` and `run_utils` as sibling modules, so direct imports from arbitrary working directories can fail with `ModuleNotFoundError: No module named 'mol_viewer'`.

Prefer launching with the app entrypoint:

```bash
python app/main.py
```

If another supervisor imports or launches the app module, ensure the app directory is on `PYTHONPATH` or run from an app-aware context. Avoid treating the UI as an installed package entry point.

## Dependency And Runtime Expectations

The app-level requirements are lightweight:

- `gradio==3.50.*`
- `requests`

A successful docking run still needs the full DiffDock inference runtime behind the UI, including the model/checkpoint files and optional-heavy scientific stack used by inference. CPU execution can work for PDB-file inputs but is slow. GPU execution is recommended for practical latency.

The app sets `DiffDockDir` to the repository root when it starts and uses that directory as the working directory for the inference subprocess. It also sets `LOG_LEVEL=INFO` unless already provided.

## UI Inputs

### Protein

The protein panel accepts either:

- A PDB code in the text field.
- An uploaded protein `.pdb` file.

Input precedence follows the app wrapper behavior: if a PDB ID is present and no protein file is uploaded, the app downloads the PDB file from RCSB into its temporary app directory. Otherwise it uses the uploaded file object.

If no protein file can be resolved, the app returns:

```text
Protein file is missing! Must provide a protein file in PDB format
```

### Ligand

The ligand panel accepts either:

- A SMILES string.
- An uploaded `.sdf` or `.mol2` ligand file.

If a ligand file is uploaded, that file path is passed as the ligand description. Otherwise the SMILES string is passed to inference.

If both ligand inputs are empty, the app returns:

```text
Ligand is missing! Must provide a ligand file in SDF format or SMILE string
```

### Optional YAML Config

The configuration upload accepts `.yml` or `.yaml`. If no config is uploaded, the app uses DiffDock's default inference config. If a config is uploaded, the app passes the uploaded path as `--config` to inference.

A custom config is not a patch overlay in the UI: it must provide all settings required by the inference script for the desired run. For full configuration details and command-line alternatives, route to `../docking-inference/SKILL.md`.

### Samples Per Complex

The UI exposes `Samples Per Complex` as an integer from 1 to 100 with default `10`. Internally this maps to `samples_per_complex` and is passed to inference as a command-line argument.

Increasing the sample count increases runtime and output size. On CPU demo environments, even the default can take minutes.

## CLI Wrapper Behavior

The UI wrapper builds an inference command with these core arguments:

- `--protein_path=<resolved protein pdb path>`
- `--ligand=<uploaded ligand path or SMILES string>`
- `--config=<uploaded config or default config>`
- `--no_final_step_noise`
- `--loglevel=<INFERENCE_LOG_LEVEL or LOG_LEVEL-derived value>`
- `--samples_per_complex=<UI sample count>`
- `--out_dir=<temporary directory>`

Before inference, it runs a lightweight device probe through DiffDock's device-printing utility. It then runs inference in a temporary directory, copies the input protein into the single output subdirectory when exactly one subdirectory is produced, and zips the temporary output tree into a file named like `diffdock_output_YYYYMMDD_HHMMSS_<uuid>.zip` under a `tmp` directory.

The app has an internal development escape hatch named `__SKIP_RUNNING`; future agents should not rely on it for production behavior.

## Examples As Evidence

The UI includes example rows using PDB IDs such as `6w70` and `6moa`, uploaded protein/ligand example files, SMILES strings, and default sample count `10`. Treat these as evidence for supported input shapes, not as a dependency for this skill. Runtime instructions must not require opening the original examples directory.

## Deployment Notes

- For Hugging Face Spaces, the app metadata indicates Docker SDK, `main.py`, and port `7860`.
- The demo is designed for one protein and one ligand at a time.
- CPU deployments are expected to be slow; duplicated GPU deployments are faster but require the deployment platform to provide GPU resources and compatible DiffDock dependencies.
- The visualization uses browser-side 3Dmol.js resources, so network policy, browser script restrictions, or iframe sandboxing can affect display even when the downloadable zip is valid.
