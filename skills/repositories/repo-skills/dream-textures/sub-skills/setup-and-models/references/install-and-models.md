# Install and Model Management

This reference is self-contained operating guidance for Dream Textures setup. It distinguishes ordinary release installation from source/developer installation, explains how the add-on stores dependencies and model preferences, and gives safe validation/recovery steps.

## What Dream Textures is expected to register

- Blender add-on name: **Dream Textures**.
- Minimum Blender version declared by the add-on: **3.1.0**.
- Source version evidence: **0.4.1**.
- Add-on location hint: **Image Editor -> Sidebar -> Dream**; after setup, open an Image Editor or Shader Editor, enable `View > Sidebar`, and select the `Dream` tab.
- The add-on registers a default local `DiffusersBackend` when Blender imports and enables the package successfully.
- The package folder should be importable as `dream_textures`. If a source checkout or extracted archive is named `dream-textures`, rename/copy the actual Blender add-on folder to `dream_textures` before enabling it.

## Release install versus source/developer install

Prefer a prebuilt official release archive for ordinary users.

Release-oriented path:

1. Download the latest Dream Textures add-on release that matches the user's platform/backend.
2. Install the archive through Blender preferences and enable the checkbox for Dream Textures.
3. On Windows, release archives may contain an inner `.zip` extracted from a 7-Zip archive; install the inner add-on zip/folder according to the release instructions.
4. Do **not** run development dependency tooling just because setup is incomplete. If the add-on preferences say dependencies are missing for an ordinary user, first suspect that source was installed by accident or the wrong release variant was unpacked.
5. Complete model or DreamStudio setup from the add-on preferences.

Source/developer path:

1. Use source/developer setup only for contributors, maintainers, or Linux/source installs where the user intentionally chose source.
2. Put the source folder in Blender's user add-ons directory and ensure the folder name is `dream_textures`.
3. Enable **Developer Extras** in Blender preferences to reveal Dream Textures' **Development Tools** section.
4. Choose exactly one dependency requirement variant in the Dream Textures preferences for the intended backend, then use the in-Blender developer install action or manual Blender-Python `pip install --target .python_dependencies` equivalent.
5. Every source/developer dependency install must target the add-on folder's `.python_dependencies` directory. Installing the packages only into a shell virtualenv, a system Python, or Blender's global site-packages is not sufficient for this add-on's expected layout.

Do not instruct future agents to run Dream Textures source operators or scripts directly. The add-on's dependency installer is a Blender UI/developer tool: it closes the generator process, obtains pip if needed, may open a console on Windows, and installs the selected requirements into `.python_dependencies` using Blender's Python. Treat this as UI behavior to explain, not as a standalone script to invoke.

## Dependency target and setup flow

Dream Textures checks whether `.python_dependencies` contains more than a minimal placeholder set. If it appears empty, the preferences UI reports **Dependencies Missing** and points ordinary users back to the latest release. When dependencies are present, the preferences UI exposes model search/download, installed model list, checkpoint import/link controls, and DreamStudio key status.

Recommended validation order:

1. Confirm the add-on directory is the Blender package folder, not the parent downloads directory.
2. Confirm `__init__.py`, `preferences.py`, `operators/install_dependencies.py`, `requirements/`, `generator_process/`, and `.python_dependencies/` exist inside that folder.
3. Run `scripts/check_addon_layout.py /path/to/dream_textures` from this skill to inspect layout without importing Blender or using the network.
4. In Blender preferences, enable Dream Textures and check whether the preferences panel says dependencies are missing, a model is required, setup is complete, or a conflict is detected.
5. If local generation is desired, make sure at least one compatible model is installed, imported, or linked. If cloud processing is desired, make sure the DreamStudio key is entered and valid.

## Hugging Face model search and download

Dream Textures' preferences provide Hugging Face model search and download for repositories tagged as Diffusers-compatible.

Important behavior:

- Search uses the user's query and filters for Diffusers models.
- Some gated or private repositories require a Hugging Face Hub access token. Generate a token in the Hugging Face account settings, paste it into the add-on preferences **Token** field, and avoid copying the token into logs or screenshots.
- If a gated model still fails after adding a token, verify that the account accepted the model's terms and that the token has permission for that repository.
- The model download action prefers the `fp16` variant when **Prefer Half Precision Weights** is enabled and the repository provides compatible fp16 files; otherwise it falls back to available weights.
- **Resume Incomplete Download** allows interrupted downloads to continue rather than forcing a full redownload.
- Existing installed models are discovered from Hugging Face/Diffusers caches and displayed in the preferences model list. If an entry already resolves to a local path, the install/open button opens that local folder rather than downloading again.

Good initial models:

- `stabilityai/stable-diffusion-2-1-base`: useful 512x512 prompt-to-image starting point from the setup guidance.
- `stabilityai/stable-diffusion-2-1`: the add-on's own recommended prompt-to-image default in source UI/model-type code, suited to 768-oriented v2.1 use when hardware allows.
- `stabilityai/stable-diffusion-2-inpainting`: required for inpaint and outpaint workflows.
- `stabilityai/stable-diffusion-2-depth`: required for depth-to-image, texture projection, render-pass workflows that use depth input, and image-to-image with depth.
- `stabilityai/stable-diffusion-x4-upscaler`: required for AI upscaling.

## Linking and importing checkpoints

Dream Textures supports original checkpoint files with extensions `.ckpt`, `.safetensors`, and `.pth`.

There are two distinct operations:

- **Link Checkpoint File or Folder** keeps the checkpoint at its existing path and records it in add-on preferences. Linking a folder scans that folder for supported checkpoint extensions. If the same basename appears from both a file link and a folder link, the file-specific link/config takes precedence.
- **Import Checkpoint File** converts the original checkpoint into Diffusers format and stores the converted result in the Hugging Face cache. Importing can save half-precision weights when the corresponding preference is enabled.

For either operation, choose the model config that matches the checkpoint family. Wrong config selection is a common cause of shape errors, failed conversion, or later task/model mismatch. See `backend-compatibility.md` for the checkpoint config matrix.

## DreamStudio cloud setup

DreamStudio is the cloud-processing path for users whose local hardware is unsupported or who prefer not to run local model inference.

Setup facts:

- Paste the DreamStudio API key into the **DreamStudio Key** field in Dream Textures preferences.
- A DreamStudio key can make the add-on setup appear complete even when local model weights are not installed.
- DreamStudio credentials should be treated as secrets. Never echo the key into logs, issue text, or generated files.
- If a workflow specifically needs a local model or local Diffusers behavior, a DreamStudio key does not replace that local model requirement; route model-specific generation issues to the model/task matrix first.

## Concrete recovery checklist

When setup fails, use this order before reinstalling broadly:

1. Run the bundled static layout checker on the add-on folder.
2. If the folder name is not `dream_textures`, fix the folder name and restart Blender.
3. If `.python_dependencies` is absent or effectively empty and the user is not a developer, reinstall the correct prebuilt release variant.
4. If the user intentionally uses source, install exactly one backend requirement variant into `.python_dependencies` with Blender's Python or the add-on's Developer Tools.
5. Restart Blender after dependency changes so imports and the generator subprocess see the updated target directory.
6. Download, link, or import a model matching the intended task.
7. Add a Hugging Face token only for gated/private Hub models; add a DreamStudio key only for cloud processing.
8. Reproduce the error from Blender's system console or Terminal-launched Blender on macOS and match the symptom against `troubleshooting.md`.
