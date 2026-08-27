---
name: dipy
description: "Use Dipy for diffusion MRI IO, preprocessing, reconstruction,
  tractography, registration, visualization-aware workflows, and command-line
  operations."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Dipy Repo Skill

Use this skill when a task involves Dipy, DIPY, diffusion MRI, diffusion-weighted imaging, tractography, reconstruction models, b-values/b-vectors, NIfTI DWI data, streamline tractograms, medical-image registration, Dipy `dipy_*` commands, or debugging Dipy installation/runtime behavior.

Dipy is a research-focused Python package for diffusion MRI imaging workflows. It is not a clinical-deployment guide; keep user guidance framed as research/analysis support.

## Start Here

1. Identify whether the task is about files, preprocessing, reconstruction, tractography/segmentation, registration/alignment, or command-line workflow mechanics.
2. Read the matching sub-skill below before answering detailed API or CLI questions.
3. Run `python scripts/check_dipy_install.py` when the environment is uncertain or the user reports missing commands/imports.
4. Prefer the bundled smoke scripts for tiny deterministic validation before running user data or expensive workflows.
5. Treat network fetches, GUI visualization, neural-network helpers, and whole-brain tracking/registration as optional or potentially expensive unless the user explicitly authorizes them.

## Route By Task

- `sub-skills/io-data/`: NIfTI image IO, bvals/bvecs, `GradientTable`, `StatefulTractogram`, tractogram/PAM formats, dataset listing/fetching, and IO conversion commands.
- `sub-skills/denoising-preprocessing/`: NLMeans, local PCA, MPPCA, Patch2Self, Gibbs ringing removal, noise estimation, DWI bias correction, and pre-fit validation.
- `sub-skills/reconstruction-models/`: DTI, DKI, CSD/MSMT-CSD, CSA/QBall/OPDT, DSI/DSID, GQI, MAPMRI, SFM, FORECAST, FWDTI, FORCE, RUMBA API surfaces, ODFs, scalar maps, peaks, and reconstruction CLIs.
- `sub-skills/tracking-segmentation/`: tractography, seeds, direction getters, stopping criteria, streamline operations, QuickBundles, RecoBundles, LabelsBundles, brain masks, tissue classification, AFQ, BUAN, and tractometry handoffs.
- `sub-skills/registration-alignment/`: reslicing, affine/SyN registration, transform application, motion correction, streamline linear registration, BundleWarp, and registration CLIs.
- `sub-skills/cli-workflows/`: `dipy_*` entry-point discovery, parser behavior, `--help` probes, command families, output naming, and translation between APIs and CLI workflows.

## Cross-Cutting References

- `references/troubleshooting.md`: install/import, source-checkout shadowing, optional dependency, data validation, CLI, and workflow safety issues shared across sub-skills.
- `references/repo-provenance.md`: generation baseline, source commit, package version, dirty-state summary, and relative evidence paths.
- `references/repo-routing-metadata.json`: structured import metadata consumed by the managed repo-skills-router.
- `scripts/check_dipy_install.py`: safe installed-package and CLI-flow probe with JSON/text output.

## Safe Validation Commands

Run these from the root of this skill directory, or adapt paths to wherever the skill is installed:

```bash
python scripts/check_dipy_install.py --format text
python sub-skills/io-data/scripts/dipy_io_probe.py --check-imports --check-signatures --tiny-gradient
python sub-skills/reconstruction-models/scripts/dipy_tensor_smoke.py --json
python sub-skills/denoising-preprocessing/scripts/dipy_denoise_smoke.py --json
python sub-skills/registration-alignment/scripts/dipy_reslice_smoke.py
python sub-skills/tracking-segmentation/scripts/dipy_streamline_smoke.py
python sub-skills/cli-workflows/scripts/dipy_cli_probe.py --format text
```

These probes use synthetic or import-only checks. They do not fetch datasets, train models, open GUIs, or require the original source repository.

## Environment Expectations

Install Dipy with a public package manager before using the runtime checks:

```bash
pip install dipy
# or
conda install -c conda-forge dipy
```

- Base Dipy workflows require Python plus Dipy's core runtime dependencies such as NumPy, SciPy, nibabel, h5py, tqdm, packaging, and tractogram support dependencies.
- Visualization workflows can require FURY, matplotlib, display/OpenGL support, or headless rendering setup.
- Neural-network workflows such as EVAC+ or neural bias correction can require optional ML packages and model assets.
- Patch2Self can require scikit-learn-compatible estimator support depending on the selected model.
- CLI entry points must come from the same installed environment as the imported Dipy package; use `sub-skills/cli-workflows/` when shell commands and Python imports disagree.

## Common Routing Patterns

- Data-to-FA map: `io-data` to load NIfTI and gradients, `denoising-preprocessing` if cleanup is needed, `reconstruction-models` for `TensorModel`, then `io-data` to save outputs.
- Data-to-tractography: `io-data` for DWI/gradients, `denoising-preprocessing` as needed, `reconstruction-models` for peaks/PAM, `tracking-segmentation` for seeds/stopping/streamlines, then `io-data` for tractogram saving.
- Registration before analysis: `io-data` for files/headers, `registration-alignment` for reslice/affine/SyN/motion correction, then return to the scientific owner.
- Command-line request: `cli-workflows` for command discovery/parser/output mechanics, then the scientific sub-skill for parameter meaning and validation.

## Safety And Scope

- Do not run Dipy dataset fetchers, long registration, whole-brain tracking, large model fits, GUI visualization, or neural-network model downloads without user intent.
- Use explicit output directories and avoid overwriting user data unless requested.
- Validate DWI shape, bvals/bvecs length, masks, affine/reference metadata, and optional dependencies before expensive work.
- If an import works only inside a source checkout or fails because generated version metadata is missing, prefer a normal installed package environment and use `cli-workflows` troubleshooting.
