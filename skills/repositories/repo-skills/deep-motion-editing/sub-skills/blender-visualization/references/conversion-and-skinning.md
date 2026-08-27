# FBX conversion and skinning

## FBX to BVH

The repository contains Blender helpers for converting FBX animation to BVH.
They walk input directories in their original form and can write many files;
treat bulk conversion as an explicit user operation. The command builder can
construct a bounded single-file or script invocation, but it does not fetch
FBX assets.

## Automatic skinning

Automatic skinning takes a target character FBX and a retargeted BVH. The
source script imports the BVH, changes scale to match the FBX, assigns a rest
pose, parents mesh/skeleton objects, and removes a temporary BVH. Verify the
FBX character, skeleton alignment, and output directory first. Keep the input
BVH and FBX immutable and use a disposable output copy.

## Manual fallback

If automatic weights fail, import the FBX without animation, merge mesh parts,
import the BVH, align rest pose and skeleton manually, and parent the mesh to
the skeleton with automatic weights. This is a visual correction workflow,
not a deterministic validation step.

Asset licensing, Blender version compatibility, coordinate systems, scale, and
mesh topology are user responsibilities. Do not interpret a successful command
construction as a successful skinning result.
