---
name: gimp-ml
description: "Route GIMP-ML computer-vision plug-in, GIMP layer, local FastAPI
  image-generation, and legacy-host troubleshooting tasks with explicit model,
  runtime, credential, and verification boundaries."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# GIMP-ML

Use this repo skill when a task names **GIMP-ML** or asks for GIMP-integrated
computer vision such as deblurring, denoising, dehazing, enhancement, depth,
segmentation, face parsing, matting, inpainting, super-resolution, frame
interpolation, K-means, palette operations, or text-to-image/edit/extend/outpaint.
This is a router for the repository's two distinct surfaces: historical GIMP 2
Python-Fu plug-ins and a newer local Python 3 HTTP service.

## First classify the task

1. Start with [setup-and-host](sub-skills/setup-and-host/SKILL.md) for installation,
   host compatibility, plugin discovery, weights, permissions, refresh safety,
   GIMP menus, or choosing between legacy and service paths.
2. Use [classical-image-ops](sub-skills/classical-image-ops/SKILL.md) for invert,
   K-means clustering, palette behavior, drawable/array checks, and CPU-safe
   image primitives.
3. Use [vision-filters](sub-skills/vision-filters/SKILL.md) for deblur, dehaze,
   denoise, enhancement, monocular depth, semantic segmentation, face parsing,
   super-resolution, or frame interpolation.
4. Use [guided-editing](sub-skills/guided-editing/SKILL.md) for inpainting,
   trimap matting, face-generation layer preparation, or sparse color masks.
   Route ordinary segmentation or restoration back to `vision-filters`.
5. Use [text-generation-service](sub-skills/text-generation-service/SKILL.md)
   for the local FastAPI protocol, GIMP 2 bridge payloads, text-to-image,
   text-edit, text-extend, outpaint, or OpenAI/provider failures.

Read [architecture](references/architecture.md) when a request spans routes,
and [troubleshooting](references/troubleshooting.md) before changing a host,
weights tree, service process, or configuration. Run the shared
[environment diagnostic](scripts/check_environment.py) for a read-only import,
GIMP/Python-2 executable, or no-allocation CUDA report.

## Verification boundary

The generated operating context is based on public docs and source evidence at
one repository snapshot. A Python 3 service-core verification established
common imports, package consistency, and FastAPI route declarations. The
verification host had no GIMP or Python 2.7, no model weights, and no provider
credentials. CUDA was visible but a tiny allocation was blocked by the host's
CUDA memory state. Therefore:

- A static registration scan or input-validator pass is **not** GIMP execution.
- A present checkpoint path is **not** compatible weights or successful inference.
- CUDA visibility is **not** proof that a filter can run on the target image.
- A local `/status` response is **not** model loading or provider success.
- No skill instruction downloads weights, calls OpenAI, or runs a destructive
  updater automatically.

Keep those labels in any downstream report. Read
[repo provenance](references/repo-provenance.md) before treating this graph as
current for another checkout.

## Safe operating sequence

1. Identify the requested surface and required inputs (selected layer, aligned
   mask/trimap, second frame, output directory, or HTTP payload).
2. Run the nearest bundled read-only validator or asset/layout check before
   loading a model or mutating GIMP state.
3. Check the host/backend gate: legacy workflows need a compatible GIMP 2.10
   Python-Fu/Python 2 host; model workflows also need external weights; text
   workflows need an installed service launcher and separately authorized
   provider access.
4. Preserve source layers and input files. Report whether the result is
   generated, static-only, blocked, or unverified rather than inferring success.

There is no single installable Python distribution for the legacy plugin
collection. For a read-only local diagnostic, run the bundled helper from the
root of this generated skill:

```bash
python scripts/check_environment.py --help
```

Install or launch the legacy GIMP application, model assets, or service only
through the target deployment's separately reviewed public procedure.
