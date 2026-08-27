---
name: package-apis
description: "Explains VLA-Adapter Prismatic/VLA APIs, robot constants,
  checkpoint layouts, LoRA merge, and HF conversion utilities."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Package Layout/API Reference (external-checkout adapter)

This sub-skill documents the native package layout and public API surface; it
does not implement or vendor that package. The generated skill directory
contains only this documentation, references, and the read-only checkpoint
layout validator. The native `prismatic/`, `vla-scripts/`,
`experiments/robot/`, and conversion scripts remain in the separate checkout.

Before inspecting any native source or installed package, set the absolute root
and enter it:

```bash
export VLA_ADAPTER_REPO_ROOT=/abs/path/to/VLA-Adapter
cd "$VLA_ADAPTER_REPO_ROOT"
python -m pip install -e "$VLA_ADAPTER_REPO_ROOT"
```

External prerequisites include the native checkout, its base Python package
dependencies, a compatible checkpoint, and (only for conversion or model
execution) the matching CUDA/Hugging Face stack. This sub-skill is not
self-contained and does not provide `load`, `load_vla`, action-head,
projector, LoRA-merge, or HF-conversion implementations. It does not load
weights or execute a model.

## Scope

Use this sub-skill to read [references/api-reference.md](references/api-reference.md)
and [references/prismatic-apis-and-conversion.md](references/prismatic-apis-and-conversion.md),
map native entrypoints and checkpoint files, or run the local layout validator.
Treat the API signatures and conversion inventory as reference facts, not
copyable implementations.

Run the skill-local validator by absolute skill path:

```bash
python "$VLA_ADAPTER_SKILL_ROOT/sub-skills/package-apis/scripts/check_checkpoint_layout.py" \
  --checkpoint "$VLA_ADAPTER_REPO_ROOT/outputs/CHECKPOINT" --help
```

The validator only inspects local files. For native operations, use the native
entrypoints from `<absolute-repo-root>` after separately confirming their
prerequisites; this adapter never invokes them.
