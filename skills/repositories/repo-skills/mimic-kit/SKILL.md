---
name: mimic-kit
description: "Use MimicKit repo-specific guidance for motion imitation,
  physics-simulator RL training, motion conversion, and SMP prior workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# MimicKit Repo Skill

Use this skill when a task is about MimicKit, a checkout-oriented motion imitation and physics-simulator control framework. It covers the repository's runner, simulator backend choices, motion data tools, DeepMimic/AWR/LCP recipes, AMP/ADD/ASE recipes, and Score-Matching Motion Prior workflows.

Read [references/repo-provenance.md](references/repo-provenance.md) before deciding whether this skill is current for a checkout. Read [references/troubleshooting.md](references/troubleshooting.md) when the request starts with an install, backend, missing asset, or config-path failure.

## First decision

1. If the user needs to build, launch, or debug a train/test command, load [runner-and-backends](sub-skills/runner-and-backends/SKILL.md).
2. If the user needs motion conversion, motion-file validation, `view_motion`, DoF diagnostics, or plotting logs, load [motion-tools](sub-skills/motion-tools/SKILL.md).
3. If the user asks for DeepMimic, AWR, LCP, vault/static-object, or PPO-style motion tracking, load [motion-imitation](sub-skills/motion-imitation/SKILL.md).
4. If the user asks for AMP, ADD, ASE, discriminator rewards, task-location, task-steering, or adversarial imitation, load [adversarial-control](sub-skills/adversarial-control/SKILL.md).
5. If the user asks for SMP, TinyMDM, score-matching priors, GSI, `smp_prior_cfg`, `smp_prior_model`, or SMP task policies, load [smp](sub-skills/smp/SKILL.md).

## Important repository facts

- MimicKit is not packaged by `pyproject.toml`, `setup.py`, or `setup.cfg` in this checkout. Treat it as a checkout-oriented project, not as a pip-installable distribution.
- Commands and helper scripts should accept an explicit MimicKit checkout root. Do not assume the current working directory is the target checkout.
- The main runner expects the checkout's root and `mimickit/` directory to be importable. The bundled runner wrapper in `sub-skills/runner-and-backends/scripts/run_mimickit.py` prepares that import layout.
- Runtime Python dependencies are listed in `requirements.txt`, but simulator backends are external: Isaac Gym, Isaac Lab/Isaac Sim, or Newton/Warp must be installed separately according to the chosen engine.
- The repository snapshot used for this skill did not contain downloaded motion clips, pretrained model files, training logs, or several task object XML assets. Preserve that limitation before promising a runnable simulator job.

## Minimal safe checks

For a target checkout, start with the non-simulator checker:

```bash
python sub-skills/runner-and-backends/scripts/check_mimickit_layout.py \
  --repo-root <mimickit-checkout>
```

To preview a runner command without launching a simulator:

```bash
python sub-skills/runner-and-backends/scripts/run_mimickit.py \
  --repo-root <mimickit-checkout> \
  --dry-run \
  -- --arg_file args/deepmimic_humanoid_ppo_args.txt --visualize false
```

For motion tools, prefer the bundled helpers in `sub-skills/motion-tools/scripts/` instead of source utility paths. For SMP prior/policy checks, use `sub-skills/smp/scripts/train_smp_prior.py --dry-run-config` and `sub-skills/smp/scripts/check_smp_config.py` before launching training.

## Verification status to preserve

This generated skill was verified for source syntax/import routing, PyTorch CUDA availability, converter parser help, tiny GMR/SMPL conversion fixtures, plotting helper output, and SMP dry-run/config checks. It was **not** verified by running full simulator-native training/testing because the external simulator packages and downloaded data/model/object assets were unavailable in the production environment.

Do not auto-import or claim full backend validation from this skill alone. If a user needs full native validation, install the selected simulator backend, restore the required data/model/object assets, and run a focused native case after checking the relevant sub-skill.
