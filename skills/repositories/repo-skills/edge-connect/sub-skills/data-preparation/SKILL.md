---
name: data-preparation
description: "Prepare EdgeConnect images, masks, edges, and flists and validate
  path-oriented config inputs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Data Preparation

Use this sub-skill when the task is about preparing EdgeConnect inputs rather than running the model itself.
It is the route for turning image folders into file lists, checking whether masks or edges are required,
and validating the config paths that control how the runtime finds data.

## What this route owns

- Build deterministic flists from image directories.
- Validate `config.yml` path keys and mode-dependent data requirements.
- Explain how `Dataset.load_flist` interprets lists, directories, and text flists.
- Describe mask modes 1-6 and edge modes 1-2.
- Catch common path mistakes before training, testing, or evaluation starts.

## What to read first

- `references/data-formats.md` for input layouts, flist semantics, and pairing rules.
- `references/configuration.md` for config keys, path resolution, and fallback behavior.
- `references/troubleshooting.md` for the most common failure patterns.

## What to run

- `scripts/build_flist.py` when you need a recursive, sorted image flist.
- `scripts/validate_config.py` when you want to check a config file or path override before launch.

## Typical questions this sub-skill answers

- "How should I lay out images and masks for EdgeConnect?"
- "Why is my external mask list ignored or mismatched?"
- "Do I need edge flists for this mode?"
- "Which config paths are read from the config directory, and which are read from the launch working directory?"
- "Why does a directory input appear empty even though it has images?"

## Workflow summary

1. Decide whether the run is train, test, or eval.
2. Decide whether masks are random, external, mixed, or paired one-to-one.
3. Decide whether edges come from Canny or external edge files.
4. Build flists from the actual image, mask, and edge directories.
5. Validate the config file and any relative paths.
6. Confirm that the image/mask/edge ordering will stay aligned.

## Key rules to remember

- Python lists are used as-is.
- Directory inputs only pick up top-level `*.jpg` and `*.png` files in the runtime loader.
- Text flists are read line by line and should stay sorted when positional pairing matters.
- `MASK=3`, `MASK=4`, and `MASK=5` need external mask data.
- `MASK=6` is test-mode only and requires one mask per input image.
- `EDGE=2` needs external edge data.
- `EDGE=1` uses Canny and `SIGMA`; `SIGMA=0` randomizes the blur and `SIGMA=-1` disables edge output.
- `NMS=1` only affects the external-edge path.
- The runtime derives `PATH` from the config file location; editing `PATH` in YAML does not change output placement.

## Common routing cues

Route here when the user asks to:

- build a flist from a dataset directory
- prepare paired image/mask/test assets
- check whether a config file can locate its data
- diagnose empty directory inputs or bad file-list ordering
- confirm whether a run needs external edges or masks
- validate the data layout before training or testing

Route elsewhere when the user asks to:

- download or restore checkpoints
- stage a training or test command
- inspect losses, metrics, or evaluation outputs
- change model architecture or training behavior

## Handoff expectation

A future agent should be able to prepare EdgeConnect data inputs and validate the config wiring from this route alone, without reopening the source repository.
