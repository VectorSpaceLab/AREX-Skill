---
name: papers-in-100-lines-of-code
description: "Routes Papers-in-100-Lines-of-Code catalog lookup, compact ML
  paper implementation adaptation, dependency planning, backend safety, and
  troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Papers-in-100-Lines-of-Code

Use this repo skill when the user asks about the Papers-in-100-Lines-of-Code
repository, compact educational implementations of ML papers, or safe planning
for adapting/running those implementations. The source is a catalog of 62
standalone paper mini-projects, not one installable Python package.

## Start here

- Read [repo provenance](references/repo-provenance.md) before checking whether
  this skill matches a current checkout or before refreshing it.
- Read [implementation index](references/implementation-index.md), or query
  [implementation-index.json](references/implementation-index.json) with
  [query_implementation_index.py](scripts/query_implementation_index.py), when
  the task names a paper, method, script, symbol, or family.
- Read [dependency and backend guide](references/dependency-and-backend-guide.md)
  before installing requirements or attempting a full run.
- Read [repo-level troubleshooting](references/troubleshooting.md) for
  installability, dependency conflicts, data/weight downloads, CUDA, and output
  side effects.
- Run [check_skill_assets.py](scripts/check_skill_assets.py) when validating the
  generated skill tree itself.

## Route by user intent

| User task | Route |
|---|---|
| Find whether a paper is implemented, choose an entry, interpret requirements, or plan a safe first run | [paper-catalog-and-execution](sub-skills/paper-catalog-and-execution/SKILL.md) |
| Adapt or explain GANs, VAEs, normalizing flows, diffusion/DDIM/PNDM/DPM-Solver, DreamBooth, Stable Diffusion, image translation, SNL, or AALR | [generative-models](sub-skills/generative-models/SKILL.md) |
| Work with NeRF, Fourier/SIREN/MFN implicit fields, PlenOctrees/Plenoxels/K-Planes, 3D Gaussian Splatting, Speedy-Splat, Spherical Voronoi, Splatter Image, cameras, rays, or rendering memory | [neural-rendering-3d](sub-skills/neural-rendering-3d/SKILL.md) |
| Adapt optimizers, activations, layers, MAML/Reptile/hypergradients, Deep Image Prior, DQN/DDQN/PPO, or long-loop training examples | [optimization-meta-rl](sub-skills/optimization-meta-rl/SKILL.md) |

## Operating posture

- Do **not** install every requirements file into one environment. Choose one
  paper or compatible family first, then use its per-entry pins.
- Do **not** treat full upstream scripts as quick smoke tests. Many train for
  thousands to millions of steps, write output images, hard-code CUDA, or need
  external datasets/weights.
- Do **not** report full paper reproduction unless the user supplied the data,
  weights, hardware/backend, output policy, and budget and the run actually
  passed.
- For algorithm understanding, prefer tiny offline adaptations with explicit
  `device`, data, and output arguments.
- For CUDA-heavy rendering/text-to-image/RL tasks, verify the framework/backend
  separately before starting a long run.

## Minimal generated-skill checks

From this skill directory, safe checks are stdlib-only:

```bash
python scripts/query_implementation_index.py --query "stable diffusion"
python scripts/query_implementation_index.py --group neural-rendering-3d --limit 5
python scripts/check_skill_assets.py
```

These checks validate the generated catalog and routing assets. They do not
execute or reproduce upstream paper implementations.

## When not to use this skill

- Do not use it as a replacement for a specialized production library skill
  such as Diffusers, PyTorch, Gym, or a full NeRF framework when the user is not
  working with this paper-code catalog.
- Do not use it to claim benchmark parity with any paper. The repository favors
  compact educational clarity over exhaustive reproduction infrastructure.
- Do not use it for ordinary repository maintenance unless the change affects
  the paper catalog, per-paper requirements, or implementation scripts.

## Scope limits

This skill distills source evidence into operating guidance and bundled helper
scripts. It does not bundle every full upstream training/rendering program, does
not fetch datasets or weights, and does not verify optional full CUDA paper
runs. When a user needs a full reproduction, use the catalog and owning
sub-skill to plan an isolated environment, data/weight acquisition, runtime
budget, and backend validation first.
