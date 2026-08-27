---
name: replay-and-data
description: "Use Acme adders, Reverb replay tables and datasets, offline data
  iterators, image augmentation, and replay shape troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Replay and Data

Use this sub-skill when an Acme task involves collecting actor experience, writing it to Reverb, reading replay samples into a learner, adapting offline demonstrations, or diagnosing replay/data structure mismatches.

## Read First

- [Replay API](references/replay-api.md): `Adder` contracts, Reverb adder families, signatures, dataset helpers, and expected shapes.
- [Replay workflows](references/workflows.md): choose transition/sequence/episode/structured adders, build Reverb/TFDS/numpy iterators, and connect learner data.
- [Troubleshooting](references/troubleshooting.md): optional dependency failures, Reverb table signature errors, sequence/period pitfalls, extras mismatches, and invalid offline data paths.
- [Replay structure helper](scripts/describe_replay_structure.py): validate a JSON description of observation/action/reward/discount/extras nesting and print an adder-family recommendation without importing Reverb.

## Route Boundaries

- Stay here for `acme.adders.base`, `acme.adders.wrappers`, `acme.adders.reverb.*`, `acme.datasets.reverb`, `acme.datasets.tfds`, `acme.datasets.numpy_iterator`, `acme.datasets.image_augmentation`, and `acme.utils.reverb_utils`.
- Use the sibling `core-workflows` sub-skill for environment-loop basics, wrapper selection, `dm_env` conversion, experiment scaffolding, or actor/learner process layout before replay details matter.
- Use the sibling `jax-agents` or `tf-agents` sub-skill when the question is which algorithm-specific builder, config, or learner expects a particular replay table or iterator shape.

## Fast Choices

- Pick `NStepTransitionAdder` for feed-forward learners that train on `(observation, action, reward, discount, next_observation, extras)` transitions.
- Pick `SequenceAdder` for recurrent learners, sequence losses, overlapping unrolls, or learner code that expects time-major/batched trajectories.
- Pick `EpisodeAdder` for full-episode imitation/offline pipelines or algorithms that need complete trajectories.
- Pick `StructuredAdder` when one actor stream must populate multiple tables or custom item patterns with Reverb `structured_writer` configs.
- For offline demonstrations, adapt data into `types.Transition` batches or Reverb-compatible samples, then expose an iterator matching the learner constructor.
