# Architecture overview

Deep Motion Editing is organized around one shared motion-data layer and two
neural workflows, with a separate Blender integration:

- **Shared data**: BVH hierarchy/motion parsing and writing, quaternions,
  skeleton loading, forward/inverse kinematics, and foot-contact utilities.
- **Retargeting**: a skeleton-aware model with topology/kinematics modules,
  Mixamo/custom BVH preprocessing, intra- and cross-structural inference,
  evaluation, and training.
- **Style transfer**: content/style loaders for BVH and OpenPose JSON, a
  config-driven generator/discriminator trainer, normalization files, and
  raw/fixed BVH output.
- **Blender**: BVH import, scene/camera/material setup, Eevee/Cycles rendering,
  FBX/BVH skinning, and FBX-to-BVH conversion.

Read the focused route rather than importing every module at once. The source
uses script-directory imports and has legacy NumPy assumptions; a modern
ordinary Python import is not proof that all paths work. The bundled helpers
are standalone preflight/command tools and intentionally do not package the
large checkpoints, data, Blender, or OpenPose.
