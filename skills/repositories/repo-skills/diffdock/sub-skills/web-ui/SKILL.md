---
name: web-ui
description: "Use, deploy, debug, and inspect DiffDock's Gradio web UI and
  downloadable output archives."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# DiffDock Web UI

Use this sub-skill when a user wants to launch DiffDock's Gradio interface, understand the single-complex UI inputs, debug app startup/runtime issues, or inspect the zip returned by the UI.

## Start Here

- For launch, deployment, input precedence, configuration upload, and sample-count behavior, read [references/ui-workflow.md](references/ui-workflow.md).
- For downloaded result archives, ranked SDF naming, confidence labels, PDB/SDF recovery, and visualization gaps, read [references/output-zip-format.md](references/output-zip-format.md).
- For app import errors, Gradio dependency issues, PDB download failures, missing inputs, temp/output zip problems, heavy DiffDock runtime failures, and browser/port issues, read [references/troubleshooting.md](references/troubleshooting.md).
- To summarize a returned archive without importing Gradio or DiffDock, run [scripts/inspect_diffdock_output_zip.py](scripts/inspect_diffdock_output_zip.py).

## Scope And Routing

This sub-skill covers the Gradio app only: one protein plus one ligand, optional YAML config upload, sample count control, app launch/deployment constraints, and the UI zip/result visualization conventions.

Route these tasks elsewhere:

- Full command-line inference flags, CSV/batch inference, model checkpoint options, and `default_inference_args.yaml` tuning: `../docking-inference/SKILL.md`.
- Shared installation, CUDA/Torch/RDKit/PyG/ESM/OpenFold/ProDy dependency failures: `../../references/troubleshooting.md`.
- Training, benchmark evaluation, dataset preparation, or confidence-model development: the relevant sibling sub-skill.

## Quick Commands

```bash
# Launch the app from a DiffDock checkout after installing the runtime stack.
python app/main.py

# Use a custom Gradio port.
GRADIO_SERVER_PORT=7861 python app/main.py

# Inspect a downloaded DiffDock UI zip.
python sub-skills/web-ui/scripts/inspect_diffdock_output_zip.py diffdock_output.zip
```

## Key Facts

- The web UI is a convenience wrapper around DiffDock inference for one complex at a time; use command-line inference for batch workflows.
- Protein input can be a PDB ID or an uploaded `.pdb`; ligand input can be a SMILES string or an uploaded `.sdf`/`.mol2` file.
- If a PDB ID is supplied and no protein file is uploaded, the app downloads the PDB from RCSB before running inference.
- The optional YAML config replaces the default inference config path; it must contain every argument required for the intended run.
- The sample-count UI field maps to `samples_per_complex` and is limited to integer values from 1 through 100 in the app.
- Directly importing the app module from outside the app directory can fail because `mol_viewer` is imported as a sibling module; launch through the app entrypoint or ensure the app directory is importable.
