# Troubleshooting: Catalog Lookup and Safe Planning

Use this when paper lookup, dependency interpretation, or safe-run planning is blocked. Keep the default posture conservative: this sub-skill plans from the bundled catalog and does not execute native paper implementations.

## Missing or ambiguous paper names

Symptoms:
- no match for a query such as "SD", "3DGS", "RAdam", or "NeRF without cameras";
- several entries match a broad term such as "diffusion", "GAN", "flow", "rendering", or "optimizer";
- the user names a paper alias while the folder uses a longer title.

Resolution:
1. Run or emulate `scripts/plan_paper_run.py --list-groups` to see group counts.
2. Search titles, folder labels, evidence script labels, aliases, and requirement names.
3. Present close alternatives with their detail route and safety flags; ask the user only if the selected paper affects the plan.
4. Common alias fixes:
   - Stable Diffusion -> High-Resolution Image Synthesis with Latent Diffusion Models.
   - 3DGS -> 3D Gaussian Splatting; Speedy-Splat and Spherical Voronoi are separate 3DGS-like entries.
   - NeRF -> many entries: base NeRF, NeRF--, FastNeRF, KiloNeRF, FreeNeRF, InfoNeRF, K-Planes, PlenOctrees, Plenoxels, Fourier features, SIREN/MFN.
   - Adam vs RAdam -> separate optimizer entries.
   - DPM-Solver, DDPM, DDIM, PNDM -> separate diffusion sampler/model entries.

## Conflicting old dependency pins

Symptoms:
- selected entries request mutually incompatible Torch/Torchvision/Keras versions;
- `+cu111`, `+cu113`, `+cu116`, or `+cu126` wheels do not install from default indexes;
- package names such as `sklearn`, `skimage`, `UMNN`, or `json==2.0.9` fail or look suspicious;
- a modern environment already has incompatible packages.

Resolution:
1. Do not combine requirements across paper folders. Pick one entry and create an isolated environment for it.
2. Treat requirement pins as historical evidence. Convert only after compatibility review and after the user approves a run/adaptation.
3. For static lookup/adaptation, avoid installation entirely when possible.
4. For CUDA pins, verify hardware, driver, Python version, and wheel index before installing; CPU-only installation does not prove CUDA behavior.
5. If the task is adaptation, port the concept to the user's existing stack instead of reproducing every old pin.

## Imports that may download data, weights, or tokenizers

Symptoms:
- import or first call reaches Keras/Torchvision dataset helpers;
- Diffusers/Transformers/Stable Diffusion code expects model/tokenizer files;
- Real NVP, MAF, optimizer/layer demos, or diffusion examples touch dataset utilities;
- offline execution hangs or fails with cache/network errors.

Resolution:
1. Before importing any candidate code, inspect the catalog flags and source-summary fields for `downloads_or_network`, `dataset_download`, or dataset/model keywords.
2. Require explicit user approval for network access and declare cache locations outside the runtime skill files.
3. Prefer a static plan or a rewritten tiny synthetic example that uses user-provided tensors/data.
4. For Stable Diffusion or DreamBooth, require user-provided weights/tokenizer/model identifiers and a resource budget; do not trigger automatic downloads during planning.

## Hard-coded CUDA or missing accelerator

Symptoms:
- code assumes `cuda`, calls `.cuda()`, or constructs tensors/devices on CUDA directly;
- CPU-only machine fails immediately;
- CUDA wheel versions do not match the host.

Resolution:
1. Mark full native execution as optional/unverified unless the user has a compatible GPU and approves the run.
2. For adaptation, rewrite device handling as an explicit parameter and test on tiny tensors before any training/rendering.
3. Do not claim CPU substitution is equivalent for rendering, Stable Diffusion, DreamBooth, or long training workloads unless separately verified.
4. Route device-specific algorithm work to the relevant sibling sub-skill after lookup.

## Missing output directories or assets

Symptoms:
- code tries to write plots/images/GIFs or render frames into non-existent folders;
- README expects `Imgs`, `Data`, `data`, `novel_views`, `camera_trajectories`, `out_colmap`, pretrained weights, camera files, or dataset archives;
- result images are missing even though computation appeared to run.

Resolution:
1. In the plan, list all cataloged assets and output-writing risk before any run.
2. Require the user to provide external datasets/weights/camera assets or approve acquisition separately.
3. Create explicit output directories only in the user's chosen workspace, not inside the skill tree.
4. For adaptations, make output paths arguments and use temporary or user-approved destinations.

## External weights and datasets

High-risk families:
- Stable Diffusion / DreamBooth: model weights, tokenizer files, Diffusers/Transformers caches, high memory.
- NeRF / 3DGS / Splatter / LFN: dataset archives, camera poses/intrinsics, trained Gaussian assets, generated view folders.
- Atari RL: Gym/ALE/ROM support and long reward-curve training.
- Torchvision/Keras demos: MNIST/CIFAR downloads and version-sensitive cache behavior.

Resolution: make the plan conditional on user-supplied assets and state that lookup/adaptation can proceed without full native execution.

## Top-level train loops and no CLI controls

Symptoms:
- running an evidence script would start training/rendering immediately;
- no argparse flags exist for epochs, steps, output, dataset, device, or dry-run;
- import triggers computation due to top-level calls.

Resolution:
1. Do not use full upstream execution as a smoke test.
2. For a safe trial, rewrite or extract the minimal function/class into a new controlled snippet with tiny tensors, explicit stop limits, and no network.
3. Use the sibling sub-skill for algorithm-specific shape/loop guidance.
4. Document that full native execution remains unverified for this skill unless a later verification phase explicitly narrows and authorizes it.

## Specific usability triage

- **Stable Diffusion lookup:** Select the latent-diffusion entry, route to `generative-models`, and warn about weights/tokenizer, `safetensors`, `transformers`, likely CUDA/high memory, and output image writes.
- **Adam lookup/adaptation:** Select the Adam optimizer entry, route to `optimization-meta-rl`, and prefer adapting the optimizer logic to a tiny CPU tensor/model rather than running the old pinned demo.
- **NeRF lookup/planning:** Select base NeRF or ask which NeRF-family variant is intended; route to `neural-rendering-3d`, and warn about dataset/camera assets, CUDA, long optimization, and `novel_views` outputs.
