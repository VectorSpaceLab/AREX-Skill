# Root Troubleshooting

## Purpose

Use this page for extension-level failures before entering a feature-specific route. If the extension is loaded and only one panel or workflow is failing, continue to the nearest sub-skill troubleshooting page.

## Extension does not appear in WebUI

**Symptoms**

- No **Tiled Diffusion**, **Tiled VAE**, or **DemoFusion** panel after restart.
- WebUI startup logs mention import errors from extension scripts.

**Likely causes and recovery**

1. The folder is not installed under WebUI `extensions/` or is nested one level too deep.
2. WebUI was not restarted after install/update.
3. The WebUI environment cannot import its own `modules.*` package during extension discovery.
4. A WebUI API moved and the extension version is stale for the current WebUI.

Restart WebUI, check that the extension folder contains `scripts/`, `tile_methods/`, `tile_utils/`, and `javascript/` at its top level, then inspect the WebUI startup traceback. If the traceback names WebUI sampler or UI modules, compare the current WebUI version with the extension compatibility notes in [setup and compatibility](setup-and-compatibility.md).

## Standalone Python import fails

**Symptom**

`ModuleNotFoundError: No module named 'modules'` or similar from `modules.scripts`, `modules.processing`, or sampler imports.

**Cause**

This is expected outside AUTOMATIC1111 WebUI. The repo is not a pip-installable standalone library.

**Recovery**

Do not debug this as a package-install failure. Load the extension through WebUI and verify UI panels instead.

## Optional ControlNet or StableSR behavior is absent

**Symptoms**

- Tiled Diffusion works, but ControlNet conditioning does not seem tiled.
- StableSR-specific behavior is missing.
- Logs do not print messages such as ControlNet or StableSR found.

**Likely causes and recovery**

- The optional extension is not installed, not enabled, not loaded for the current script, or exposes different attributes than this extension expects.
- ControlNet detection looks for a script titled `controlnet` with `latest_network` and control params.
- StableSR detection looks for a script titled `stablesr` with a non-null `stablesr_model`.

First verify the optional extension independently in WebUI. Then run a small Tiled Diffusion job and inspect logs for detection messages before scaling up.

## Large-image job OOMs or becomes too slow

**Symptoms**

- CUDA out of memory, GPU memory exhaustion, or extremely slow tile loops.
- Very high tile count or many tile batches in logs.

**Recovery path**

1. Lower the relevant tile or window batch size.
2. Lower Tiled Diffusion overlap or DemoFusion overlap if seams remain acceptable.
3. For VAE OOM, reduce encoder/decoder tile sizes and read `sub-skills/tiled-vae/references/troubleshooting.md`.
4. Use the **Free GPU** button after interrupted runs, then restart WebUI if hooks remain stale.
5. Do not switch on both Tiled Diffusion and DemoFusion together.

## Extension appears loaded but has no effect

**Common causes**

- The feature checkbox is off.
- Tiled Diffusion sees only one latent tile and no region/noise-inversion work, so it deliberately ignores tiling.
- DemoFusion is enabled at the same time as Tiled Diffusion.
- The selected sampler is `UniPC` for MultiDiffusion or DemoFusion.

Confirm the panel is enabled, target canvas/upscale size exceeds one tile, and the selected sub-skill's workflow settings are internally consistent.

## License and redistribution caution

The source repository uses CC BY-NC-SA 4.0. The README states that versions after 2023-03-28 may not be used for commercial sale of the repository code. Do not present this skill as legal advice; tell users to read the license terms for redistribution decisions.
