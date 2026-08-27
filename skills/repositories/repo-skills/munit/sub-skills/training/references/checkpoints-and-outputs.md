# Checkpoints and outputs

## Output tree

The training entrypoint derives `model_name` from the config filename stem, then writes below `--output_path`:

```text
<output_path>/
  logs/
    <model_name>/
      tensorboard event files
  outputs/
    <model_name>/
      config.yaml
      index.html
      images/
        gen_a2b_train_current.jpg
        gen_b2a_train_current.jpg
        gen_a2b_train_XXXXXXXX.jpg
        gen_b2a_train_XXXXXXXX.jpg
        gen_a2b_test_XXXXXXXX.jpg
        gen_b2a_test_XXXXXXXX.jpg
      checkpoints/
        gen_XXXXXXXX.pt
        dis_XXXXXXXX.pt
        optimizer.pt
```

`XXXXXXXX` is an eight-digit iteration written as `iterations + 1` when a snapshot or image-save event fires.

## What is written when

- TensorboardX writer: created at startup under `logs/<model_name>`.
- Config copy: after output subfolders are prepared, the selected YAML is copied to `outputs/<model_name>/config.yaml`.
- Scalar losses: every `log_iter` iterations through the loss writer. It logs trainer attributes whose names contain `loss`, `grad`, or `nwd`.
- Current training images: every `image_display_iter` iterations as `train_current` image grids.
- Train/test image grids plus HTML: every `image_save_iter` iterations. The HTML page is regenerated and points at the image files under `images/`.
- Checkpoints: every `snapshot_save_iter` iterations as generator, discriminator, and optimizer files.

## Checkpoint contents

Generator checkpoint:

```text
gen_XXXXXXXX.pt -> {'a': gen_a.state_dict(), 'b': gen_b.state_dict()}
```

Discriminator checkpoint:

```text
dis_XXXXXXXX.pt -> {'a': dis_a.state_dict(), 'b': dis_b.state_dict()}
```

Optimizer checkpoint:

```text
optimizer.pt -> {'gen': gen_opt.state_dict(), 'dis': dis_opt.state_dict()}
```

The same filenames are used for both `MUNIT` and `UNIT`, but checkpoint tensors are not interchangeable across trainer families or incompatible architecture configs.

## Resume mechanics

With `--resume`, training computes the checkpoint directory from the current `--output_path` and current config filename stem, then:

1. Finds the lexicographically last `.pt` filename containing `gen`.
2. Loads generator state dicts for domains `a` and `b`.
3. Parses the iteration from the last eight digits in the generator filename.
4. Finds the lexicographically last `.pt` filename containing `dis`.
5. Loads discriminator state dicts for domains `a` and `b`.
6. Loads `optimizer.pt`.
7. Reinitializes schedulers with the parsed iteration.
8. Prints `Resume from iteration N` and continues the main loop.

Because of this implementation, successful resume requires all of the following to match the previous run:

- Same `--output_path` or a copied directory with the same `outputs/<model_name>/checkpoints` shape.
- Same config filename stem, unless checkpoint directories are manually moved to the new stem.
- Same trainer family and compatible architecture/loss config.
- Zero-padded generator/discriminator snapshot names so lexicographic sort picks the latest checkpoint.
- `optimizer.pt` present, not just generator weights.

## Monitoring a real run

For a user-approved real run, monitor without disturbing training:

- Check stdout for `Iteration: XXXXXXXX/YYYYYYYY` at `log_iter` cadence.
- Check tensorboard event files under `logs/<model_name>`.
- Check current image grids for qualitative drift at `image_display_iter` cadence.
- Check `index.html` and saved train/test grids at `image_save_iter` cadence.
- Check `checkpoints/` for new `gen_*.pt`, `dis_*.pt`, and updated `optimizer.pt` at `snapshot_save_iter` cadence.

Do not infer completion from one image or one checkpoint. The loop intentionally runs until `max_iter` and exits with `Finish training`.

## Artifact hygiene

- Use a dedicated `--output_path` per experiment to avoid mixing logs and checkpoints.
- Keep `config.yaml` copied with outputs; it is the first diagnostic artifact when reproducing or resuming a run.
- Preserve matching generator, discriminator, and optimizer files together.
- If using `vgg_w > 0`, preserve `<output_path>/models/vgg16.weight` with the run or make sure the environment policy permits preparing it before launch.
- For downstream inference, route to `../inference-and-evaluation/` with the selected `gen_*.pt` checkpoint and the matching config.
