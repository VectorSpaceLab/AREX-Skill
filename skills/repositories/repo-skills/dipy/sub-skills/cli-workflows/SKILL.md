---
name: cli-workflows
description: "Use Dipy console entry points, workflow parser behavior, and safe CLI probes."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Dipy CLI Workflows

Use this sub-skill when a task asks for Dipy command-line entry points, `dipy_*` workflow discovery, help/version probes, workflow parser behavior, output naming, or translation between an API recipe and a command-line workflow. Dipy exposes 61 current console entry points through `dipy.workflows.cli:run`; each command dispatches to a workflow class through `dipy.workflows.cli.cli_flows`.

## Quick Start

1. Start with `references/cli-reference.md` to choose the command family and route scientific details to the owning Dipy sub-skill.
2. Run `python scripts/dipy_cli_probe.py --format text` to list installed flows from the Python API without network access.
3. Run `python scripts/dipy_cli_probe.py --check-help dipy_info dipy_fit_dti --timeout 8 --format json` before trusting shell entry points in a new environment.
4. Use `references/workflow-parser.md` when explaining positional arguments, optional flags, `out_dir`, `out_*`, `--force`, `--out_strat`, `--mix_names`, logging, or sub-workflow flags.
5. Use `references/troubleshooting.md` when a command is missing, optional dependencies are unavailable, help exits unexpectedly, or deprecated aliases appear.

## Routing

- Use `../io-data/` for b-values/b-vectors, gradient tables, NIfTI, tractogram, PAM, fetch, split, extract, conversion, and data-shape questions.
- Use `../reconstruction-models/` for `dipy_fit_*` model choice, metric interpretation, ODF/peaks, tensor/CSD/DKI/DSI/GQI/MAPMRI/SFM details, and `dipy_fit_dti` parameter meaning.
- Use `../denoising-preprocessing/` for NLMeans, LPCA, MPPCA, Patch2Self, Gibbs removal, motion-prep, masks, and bias-correction caveats.
- Use `../registration-alignment/` for affine/SyN registration, apply-transform, motion correction, reslice, SLR, and BundleWarp details.
- Use `../tracking-segmentation/` for tracking, PFT, RecoBundles, LabelsBundles, clustering, masks, tissue classification, BUAN, and streamline outputs.

## Safe CLI Pattern

```bash
python scripts/dipy_cli_probe.py --format text
python scripts/dipy_cli_probe.py --check-help dipy_info dipy_fit_dti --timeout 8 --format json
COMMAND --help
COMMAND --version
COMMAND inputs... --out_dir outputs --log_level INFO --log_file run.log
```

Prefer `--help` first because Dipy builds each command parser from the workflow class docstring and signature. Use explicit `--out_dir` and output filenames for reproducible paths; add `--force` only when overwriting expected outputs is safe.

## Important Version Facts

- The inspected Dipy runtime is `1.13.0.dev0+git20260617.ac9380d`; the distribution version is `1.13.0.dev0`.
- `cli_flows` values are `(module_name, class_name)` tuples, not class objects.
- The correct peaks API import is `dipy.direction.peaks.peaks_from_model`; route peaks/model questions to `../reconstruction-models/`.
- Base installation lacks `fury`, `matplotlib`, `torch`, and `tensorflow`; visualization and neural-network workflows are optional surfaces.
- `dipy_sh_convert_mrtrix` is deprecated; prefer `dipy_convert_sh` when converting spherical harmonics.

## Bundled References

- `references/cli-reference.md` catalogs all current CLI commands by task family and gives API-to-CLI routing hints.
- `references/workflow-parser.md` explains how Dipy turns workflow `run` signatures and NumPy-style docstrings into argparse CLIs.
- `references/troubleshooting.md` covers missing commands, optional dependencies, parser surprises, output overwrites, and deprecated aliases.
- `scripts/dipy_cli_probe.py` lists installed `cli_flows` and can run bounded `--help` checks for selected entry points.
