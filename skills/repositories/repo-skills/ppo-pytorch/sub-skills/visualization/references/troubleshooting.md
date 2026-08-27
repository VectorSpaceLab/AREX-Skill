# Visualization Troubleshooting

Use this page when plotting or GIF composition fails.

## Missing log files or columns

**Symptoms**

- No CSV files found in the log directory.
- `KeyError` for `episode`, `timestep`, or `reward`.
- A plot is blank or malformed.

**Likely cause**

The CSV path is wrong, the environment name is wrong, or the file does not match the repository's `episode,timestep,reward` layout.

**Next step**

Use the plotting helper in dry-run style first and confirm the log root, environment name, and run number.

## Missing frames or wrong frame order

**Symptoms**

- The GIF helper finds zero frames.
- Frames appear out of order.
- The GIF contains only a few images.

**Likely cause**

The frame glob is wrong or the image names are not zero-padded/sorted the way the native workflow expects.

**Next step**

Check the frame directory and naming scheme before composing the GIF.

## Headless matplotlib problems

**Symptoms**

- Plotting fails on a remote machine.
- `DISPLAY` or backend errors appear.

**Likely cause**

The process is using an interactive backend in a headless session.

**Next step**

Use the bundled plotting helper, which is intended to run headlessly, or set an explicit non-interactive backend before plotting.

## Pillow or image corruption problems

**Symptoms**

- `ImportError` for `PIL`
- `OSError` while opening an image
- GIF generation stops on a damaged frame

**Next step**

Install Pillow and verify that the input image files can be opened individually before composing the GIF.

## Environment render capture problems

**Symptoms**

- You can compose a GIF, but you cannot capture frames.
- The environment render step fails before any image files are written.

**Likely cause**

The live environment backend, display stack, or render mode is missing.

**Next step**

Treat frame capture as a separate environment-dependent workflow. This sub-skill only guarantees composition from existing frames.
