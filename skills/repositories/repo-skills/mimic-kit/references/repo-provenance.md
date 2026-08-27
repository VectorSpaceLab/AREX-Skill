# MimicKit repository provenance

This page records the evidence base and verification boundary for the generated `mimic-kit` skill tree.

## Source anchor

The skill tree was distilled from the current MimicKit checkout snapshot used in this production batch. The checkout was on `main` at commit `2ed1e6c093bb0829f55d33cb4f7a1731cfe6cb69`.

Primary evidence sources were the repository README, `docs/README_*.md` files, `requirements.txt`, `args/*.txt`, `data/*.yaml`, `mimickit/run.py`, the `mimickit/{engines,envs,learning,anim,util}` source tree, and the `tools/` utilities.

## Construction summary

The generated skill tree is organized as five operating sub-skills:

- `runner-and-backends` for shared runner, config-triad, device, and backend checks
- `motion-tools` for motion conversion, viewing, DoF diagnostics, and log plotting
- `motion-imitation` for DeepMimic, AWR, LCP, and vault/static-object workflows
- `adversarial-control` for AMP, ADD, ASE, and task-conditioned adversarial control
- `smp` for TinyMDM prior training and SMP task-policy workflows

## Verification record

The production environment confirmed the following before finalizing the skill tree:

- repository source imports work when the checkout root and `mimickit/` are on `PYTHONPATH`
- `python -m compileall -q mimickit tools` succeeds
- GMR and SMPL bundled converters accept tiny fixture inputs and emit loadable MimicKit motion pickles
- the bundled log-plotting helper writes an image from a text log sample
- the SMP prior wrapper and config checker perform dry-run validation
- PyTorch CUDA tensor allocation succeeds in the inspection environment

## Known limitations

This production environment did **not** verify full simulator-native training or viewer runs because the external backend packages were absent:

- Isaac Gym
- Isaac Lab / Isaac Sim
- Newton / Warp

The checkout also lacked several runtime assets that the docs reference, including downloaded motion archives, pretrained model files, training logs, and some task object XML files.

## Refresh triggers

Refresh this skill tree if any of the following change in the MimicKit checkout:

- runner or preset behavior in `mimickit/run.py` or `args/*.txt`
- env, agent, or engine config layouts under `data/`
- the converter or plotting utilities under `tools/`
- motion / model / object asset availability
- simulator backend support or import behavior

If the checkout changes, rerun the lightweight verification checks before claiming the skill tree is current.
