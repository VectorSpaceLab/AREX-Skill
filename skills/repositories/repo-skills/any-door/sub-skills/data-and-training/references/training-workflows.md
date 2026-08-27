# Training Workflows

AnyDoor’s training path is a multi-dataset, GPU-oriented Lightning workflow.
The source script is short, but the assumptions behind it are not.

## Source training recipe

The training entry does the following:

- loads `configs/anydoor.yaml`,
- restores a checkpoint into a `ControlLDM` model,
- loads a large mixed dataset collection,
- concatenates multiple image, video, try-on, and 3D-style sources,
- and starts a distributed Lightning trainer.

## Mixed dataset groups

The source groups the data into rough families:

- image data,
- video data,
- try-on data,
- and multi-view / 3D-style data.

That means the reported ratios and sample lengths are not arbitrary; they are
part of the curriculum balance.

## Training defaults to remember

- GPU-oriented distributed training.
- Batch accumulation is used.
- The source comments mention that 2 A100 GPUs were used for a satisfactory
  long run.
- The training loop expects a model checkpoint to restore from.

## Safe validation before a real run

- Check the dataset paths.
- Check that the required dataset helper packages are installed.
- Check that the model config and initial weights are available.
- Check the `WORLD_SIZE` / DDP assumptions.
- Use the dataset debug helper if you only need to inspect samples.

## Weight conversion workflow

The source conversion helper transforms a Stable Diffusion 2.1 checkpoint into
an AnyDoor-style initialization checkpoint.

Important caveat:

- the source helper uses a stale `./models/anydoor.yaml` path.
- The bundled conversion guardrail should expose that bug rather than hide it.

## When not to run training

Do not launch the actual training run when:

- datasets are still placeholder paths,
- the checkpoint path is missing,
- the user only wants an install or import check,
- or the machine does not have the required GPU resources.

## What a good explanation looks like

A future agent should be able to say:

- which datasets are mixed,
- what GPU resources are assumed,
- what checkpoint is being restored,
- and which parts are safe to inspect without a full training run.
