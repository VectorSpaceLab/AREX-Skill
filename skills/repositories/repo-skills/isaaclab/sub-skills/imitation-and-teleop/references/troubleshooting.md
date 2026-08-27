# Imitation and Teleoperation Troubleshooting

## `robomimic`, `isaacteleop`, `dex-retargeting`, or `tomli` missing

- **Likely cause:** an optional Mimic or teleop path was selected without the matching optional package installed.
- **Recovery:** install only the missing optional package or the exact extra needed by the workflow.

## SpaceMouse not detected

- **Likely cause:** the host lacks permission to read the relevant `hidraw` device node.
- **Recovery:** inspect the `/dev/hidraw*` devices and grant the required access before retrying the teleop session.

## CloudXR or XR device path fails

- **Likely cause:** the Isaac Teleop / CloudXR stack is missing, misconfigured, or running on an unsupported host architecture.
- **Recovery:** confirm the Linux x86_64 requirement, the optional teleop packages, and the CloudXR runtime configuration.

## Annotation workflow cannot find subtask signals

- **Likely cause:** the environment does not expose the expected success or subtask APIs.
- **Recovery:** use a task variant that implements the required annotation hooks or choose a simpler dataset path.

## SkillGen start-signal failure

- **Likely cause:** the dataset does not contain the required subtask start annotations.
- **Recovery:** re-annotate the dataset with explicit start signals before attempting generation again.

## `FileNotFoundError` for the dataset or template file

- **Likely cause:** the input HDF5, MP4, or prompt-template file path is wrong.
- **Recovery:** confirm the file layout and naming convention before retrying the conversion or augmentation step.

## MP4-to-HDF5 pairing mismatch

- **Likely cause:** the video filename does not preserve the original demo ID.
- **Recovery:** rename the file to keep the `demo_<id>` prefix stable so the converter can pair it correctly.

## cuRobo or warp compatibility issue

- **Likely cause:** the optional motion-planning stack is using a warp API version that no longer exposes the expected `warp.torch` names.
- **Recovery:** use the compatibility shim described in the package notes or a cuRobo version that matches the installed warp API.
