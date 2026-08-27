# Repo Provenance

schema: disco.repo-provenance.v1

## Source Identity

- Repository: Make-It-3D
- Public remote: https://github.com/junshutang/Make-It-3D.git
- Commit: `d5caefb496d17274ff37094c4fe49358ec89906e`
- Branch at capture: `master`
- Exact tag: none detected
- Commit date: 2024-06-26 20:06:58 +0800
- Commit subject: Update README.md
- Root package version: none; this is a script-style research checkout
- Embedded DPT package version evidence: `DPT/setup.py` declares `0.0.1dev1`
- Raymarching package version evidence: `raymarching/setup.py` declares package name `raymarching` without an explicit version

## Dirty State at Construction

The checkout already had a repo-local `skills/` directory containing the production log. Generated skill outputs under `skills/disco/make-it-3d/` and review artifacts under `skills/tests/make-it-3d/` are construction products, not upstream source evidence.

## Evidence Paths Used

- `README.md` for installation, model assets, two-stage training commands, refine commands, known geometry note, and citation/context.
- `requirements.txt` for runtime dependency surface.
- `main.py` for argument names/defaults, source control flow, DPT/BLIP2/Stable Diffusion usage, workspace layout, forced `opt.cuda_ray = True`, and refine/test/export behavior.
- `nerf/provider.py` for camera pose sampling, train/val/test dataloaders, and view direction logic.
- `nerf/utils.py` for `Trainer`, losses, checkpoint/log/output behavior, and rendering/test/refine methods.
- `nerf/network.py` and `nerf/network_tcnn.py` for vanilla and tiny-cuda-nn NeRF backbones.
- `nerf/sd.py` and `nerf/clip.py` for Stable Diffusion and CLIP guidance behavior.
- `nerf/refine_utils.py` for point-cloud/refinement dependencies and projection utilities.
- `nerf/renderer.py` for raymarching, test rendering, mesh export, `xatlas`, and `nvdiffrast` dependencies.
- `raymarching/setup.py`, `raymarching/backend.py`, and `raymarching/raymarching.py` for CUDA extension packaging and lazy backend behavior.
- `DPT/README.md`, `DPT/setup.py`, `DPT/requirements.txt`, `DPT/run_monodepth.py`, and `DPT/warp_depth.py` for DPT depth utility commands, weights, and options.
- `demo/*.png` and `demo/*.gif` as public example evidence of expected inputs/outputs; not copied into this runtime skill.
