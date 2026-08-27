# Data preparation workflows

## Local instance data

1. Collect the instance images for each concept.
2. Put each concept in its own `instance_data_dir`.
3. Fill in the `instance_prompt` with the concept token you want training to learn.
4. Validate the concept manifest with `scripts/validate_concepts.py`.

## Generated prior-preservation data

1. Decide the target class prompt.
2. Generate or gather a local class-image directory.
3. Keep the class images in one directory per concept.
4. Validate the directory layout before launching training.

## Real-prior bundle

1. Retrieve or stage the bundle offline if you already have it.
2. Make sure the bundle contains `images.txt`, `caption.txt`, and optional `urls.txt`.
3. Validate the bundle with `scripts/validate_regularization_layout.py`.
4. Hand the class bundle to the training route as the prior-preservation source.

The retrieval helper contract is network-sensitive and should be treated as a reference for bundle shape, not as a default runtime dependency.

## Suggested handoff to training

Once the manifest and layout are valid, route the prepared inputs to the training sub-skill. The training route will decide whether the run is generated-prior or real-prior and how to map the concept fields.
