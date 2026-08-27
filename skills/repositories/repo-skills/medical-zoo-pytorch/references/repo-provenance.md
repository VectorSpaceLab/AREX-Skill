# Repository Provenance

schema: `disco.repo-provenance.v1`

## Source snapshot

- Skill id: `medical-zoo-pytorch`
- Public project name: `MedicalZooPytorch`
- Repository: `black0017/MedicalZooPytorch`
- Remote URL: `https://github.com/black0017/MedicalZooPytorch.git`
- Current commit: `8f40dab689841d7ff0e36aa5e583a1a1509fac3d`
- Branch: `master`
- Exact tag: `none`
- Working tree state: dirty checkout with untracked DisCo skill outputs under `skills/`
- Package metadata at repo root: none; this is a source-tree-oriented project

## Evidence paths

Runtime skill content was distilled from these relative paths:

- `README.md`
- `manual/README.md`
- `installation/readme.md`
- `installation/requirements.txt`
- `installation/out_pip_list.txt`
- `datasets/`
- `docker/readme.md`
- `docker/requirements.txt`
- `examples/`
- `lib/`
- `notebooks/README.md`
- `tests/`
- `skills/tests/medical-zoo-pytorch/reports/integration/analysis-notes.md`
- `skills/tests/medical-zoo-pytorch/reports/integration/subskill-plan.md`

## Generation-time verification notes

- The `lib.*` import surface was inspected in a private PyTorch environment.
- Representative optional dependencies imported successfully during generation: `nibabel`, `torchsummary`, `torchsummaryX`, and `torchvision`.
- CUDA was available on the generation host, and a tiny GPU tensor allocation succeeded.
- The repository has no installable package metadata at the root, so the generated skill treats the checkout as the import source.

## Refresh guidance

Refresh this skill when any of the following change:

- `lib/medzoo/`, `lib/medloaders/`, `lib/losses3D/`, `lib/train/`, `lib/utils/`, or `lib/visual3D_temp/` public APIs change.
- Dataset directory names, manifest formats, or example launcher assumptions change.
- Optional runtime dependencies such as `torchsummary`, `torchsummaryX`, `tensorboard`, `torchvision`, `nibabel`, or `scipy` change.
- A new major workflow is added, such as a new model family, dataset branch, or trainer path.
- The bundled smoke scripts or validation behavior change.
