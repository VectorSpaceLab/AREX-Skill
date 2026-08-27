# Troubleshooting

## Unsupported Python
**Symptom:** install or import fails immediately.

**Likely cause:** the interpreter is outside the supported 3.10–3.12 range.

**Fix:** move to a supported interpreter and reinstall DeepLabCut there.

## GUI does not open
**Symptom:** `dlc` or `python -m deeplabcut` prints a lite notice instead of opening the Project Manager.

**Likely cause:** GUI dependencies are missing, especially `PySide6`.

**Fix:** install the GUI extra. A headless install is still fine for project creation and config inspection.

## Entry-point confusion
**Symptom:** the user expects `dlc` to behave like the click command tree in `deeplabcut.cli`.

**Likely cause:** the installed console script points to `deeplabcut.__main__:main`, not to the click group.

**Fix:** explain that `dlc` is the launcher, while `deeplabcut.cli` is importable for command discovery only.

## Windows symlink or permission problems
**Symptom:** project creation fails while adding videos as links.

**Likely cause:** symlink permissions are restricted or the shell is not elevated.

**Fix:** open an elevated shell or copy the videos instead of linking them.

Helpful reminder:
- API calls default to symlink/move behavior
- the CLI defaults to copying unless the user disables it

## Invalid video paths or empty inputs
**Symptom:** project creation returns `nothingcreated` or leaves no usable video set.

**Likely cause:** one or more video paths do not exist, a directory has no matching videos, or the extension filter is too strict.

**Fix:** verify the paths, make sure the directory contains videos with the expected extension, and tighten or loosen `video_extensions` as needed.

## Stale or moved project roots
**Symptom:** `config.yaml` points to one project root, but the directory lives somewhere else.

**Likely cause:** the project was moved after creation or the config was copied to a new location.

**Fix:** use the summary script to inspect the mismatch. Only update the config when the user explicitly wants to relocate the project.

## Missing PyTorch model tree
**Symptom:** a fresh project has no `dlc-models-pytorch/` directory.

**Likely cause:** no PyTorch shuffle or training artifact has been created yet.

**Fix:** this is usually normal. The folder typically appears after later workflow steps create the first PyTorch outputs.

## 3D setup gotchas
**Symptom:** later 3D steps fail even though project creation succeeded.

**Likely cause:** unstable camera names, mismatched camera labels, or missing calibration inputs.

**Fix:** keep camera names fixed, use consistent camera labels in filenames, and hand off calibration and triangulation to the 3D/post-processing sub-skill.
