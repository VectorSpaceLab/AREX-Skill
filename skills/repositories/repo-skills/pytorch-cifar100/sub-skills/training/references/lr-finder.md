# Learning-Rate Finder

## Purpose

Use this reference only when you intentionally want the optional learning-rate scan in `lr_finder.py`.
It is reference-only because the script has CUDA-only assumptions, external plotting dependencies, and a file-writing side effect.

## Command template

```bash
python lr_finder.py -net <name> [-b 64] [-base_lr 1e-7] [-max_lr 10] [-num_iter 100]
```

## Important constraints

- `cv2` is imported at module load time.
- Matplotlib is forced to the `Agg` backend and the scan writes `result.jpg` in the current working directory.
- The loop calls `.cuda()` on images and labels directly, so treat the script as CUDA-only.
- The `-gpu` parser entry exists, but the training loop does not use it as a CPU fallback.
- The `-gpus` argument is parsed, but the loop does not consult it.
- The script downloads CIFAR-100 through the same training loader helper, so it has the same `./data` side effect.

## What the scan does

1. Build the CIFAR-100 training loader with the standard training transform and the chosen batch size.
2. Create the selected network and an SGD optimizer with `lr=args.base_lr`, `momentum=0.9`, `weight_decay=1e-4`, and `nesterov=True`.
3. Grow the learning rate exponentially from `base_lr` to `max_lr` across `num_iter` iterations.
4. Collect learning-rate and loss points.
5. Trim the first 10 and last 5 points before plotting.
6. Save the plot as `result.jpg`.

## Operational notes

- The scan is for LR selection, not for verifying the main training recipe.
- Do not copy the LR-finder hyperparameters into the main trainer without checking the training reference first.
- `num_iter` should be comfortably larger than 15, or the trimmed curve can be too short to read.
- Because the script touches CUDA and OpenCV at startup, it is not a safe default smoke test.

## When to use it

Use the LR finder when you want to compare how a supported net reacts to learning-rate growth before committing to a long training run.
For ordinary training command construction, use `scripts/build_train_command.py` instead.
