# VADv2 boundaries

The repository README states that VADv2 core model/config code is provided in the `VADv2/` directory and is intended to integrate into the VAD v1 framework for training and inference. Treat it as an extension layer, not as a separately verified package.

## Safe integration approach

1. Keep the v1 legacy dependency family and plugin import conventions until VADv2's own compatibility requirements are checked.
2. Inspect VADv2 config/model additions and compare registry names with the v1 plugin.
3. Add only the VADv2 files needed by the selected config; do not mix v1 and v2 heads accidentally.
4. Parse the config first, then verify custom registries and native operators before attempting a CUDA model build.
5. Use the v1 [training-evaluation](../../training-evaluation/SKILL.md) route for launch/eval only after the VADv2 config contract is resolved.

## Known limits

The construction evidence did not run VADv2 training, evaluation, or full model construction. No claim is made about released VADv2 checkpoints, exact runtime compatibility, or benchmark reproduction. Preserve unknowns rather than copying assumptions from VAD v1.
