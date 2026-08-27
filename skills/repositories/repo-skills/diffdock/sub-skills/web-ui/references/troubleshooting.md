# DiffDock Web UI Troubleshooting

## `ModuleNotFoundError: No module named 'mol_viewer'`

Cause: the UI imports `mol_viewer` as a sibling module. Importing `app.main` from a working directory that does not put the app directory on `sys.path` can fail.

Fixes:

- Prefer `python app/main.py` from a DiffDock checkout.
- If using a custom launcher, run from the app directory or prepend the app directory to `PYTHONPATH`.
- Do not expect the UI to behave like an installed package entry point; DiffDock is script-style in this area.

## Gradio Import Or Version Errors

The app was written against `gradio==3.50.*`. Newer major Gradio versions can change component APIs and break `Blocks`, `Box`, or event wiring behavior.

Fixes:

- Install the app requirements in the same environment used to launch the UI.
- Keep Gradio pinned to the compatible 3.50 series unless intentionally porting the UI.
- If only the zip-inspection helper is needed, use `scripts/inspect_diffdock_output_zip.py`; it does not import Gradio.

## Missing Protein Input

Symptom:

```text
Protein file is missing! Must provide a protein file in PDB format
```

Fixes:

- Upload a `.pdb` file, or provide a valid PDB ID and leave the protein upload empty.
- If both a PDB ID and file are present, expect the uploaded file path to be used by the wrapper path branch.
- Confirm that a custom launcher passes Gradio file objects in the expected shape with a `name` field.

## Missing Ligand Input

Symptom:

```text
Ligand is missing! Must provide a ligand file in SDF format or SMILE string
```

Fixes:

- Upload a `.sdf` or `.mol2` ligand file, or provide a non-empty SMILES string.
- If an uploaded ligand is present, it takes precedence over the SMILES text for the inference argument.
- For chemistry parsing or inference failures after this validation passes, route to inference/runtime troubleshooting rather than UI validation.

## PDB ID Download Fails

The app downloads PDB IDs from RCSB only when a PDB ID is supplied and no protein file is uploaded. Network restrictions, invalid PDB codes, service failures, or write permission issues in the app temp directory can make the resolved protein path `None`.

Fixes:

- Prefer uploading a known-good `.pdb` file when running offline or behind restrictive network controls.
- Check that outbound HTTPS access to RCSB is allowed.
- Use a valid four-character PDB code or an accepted RCSB download identifier.
- Ensure the app's temporary directory is writable.

## Output Zip Missing Or Empty

The UI wraps inference in a temporary directory and zips whatever output tree exists. An inference failure can still leave a downloadable zip with logs but no usable PDB/SDF results.

Fixes:

- Inspect the archive with `scripts/inspect_diffdock_output_zip.py`.
- Look for `output.log` or other log files inside the archive.
- Confirm that model directories, checkpoint names, config paths, and runtime dependencies match the selected config.
- Route detailed inference flags and model/config behavior to `../docking-inference/SKILL.md`.

## Visualization Dropdown Is Empty

The app only creates dropdown entries for SDF files whose filenames include a parseable confidence suffix such as `rank1_confidence-0.10.sdf`. A plain `rank1.sdf` can still be a valid pose file but is skipped for visualization labels.

Fixes:

- Inspect the archive summary and check `sdf_files_without_confidence` warnings.
- Recover SDF files manually if they are present.
- Explain that missing labels are a UI naming/metadata limitation, not necessarily proof that docking failed.

## Visualization Shows Unavailable

The app needs both a PDB file and a confidence-labelled SDF file to build a 3Dmol.js visualization entry. Browser-side JavaScript, iframe restrictions, or blocked CDN access can also prevent rendering.

Fixes:

- Confirm the archive contains at least one `.pdb` and one confidence-labelled `.sdf`.
- Try the downloaded PDB/SDF in an external molecular viewer.
- Check browser console/network restrictions if the archive looks valid but the iframe remains blank.

## Full Runtime Dependency Failures

Gradio can start even when DiffDock inference later fails because of missing or incompatible Torch, PyG, RDKit, ESM/OpenFold, ProDy, model weights, or CUDA components.

Fixes:

- Validate the full DiffDock runtime before blaming the UI.
- Use CPU only for slow demos or small tests; use CUDA-compatible GPU environments for practical runs.
- For shared dependency and environment issues, read `../../references/troubleshooting.md`.

## Browser Or Port Failures

The app reads `GRADIO_SERVER_PORT` and defaults to `7860`, then binds to `0.0.0.0` with `share=False`.

Fixes:

- Set a free port with `GRADIO_SERVER_PORT=<port> python app/main.py`.
- Check whether another process already uses the port.
- In containers or remote servers, publish/forward the selected port and check firewall rules.
- Use `http://localhost:<port>` for local access; use the host's reachable address only when network policy allows it.
