---
name: custom-keywords-and-assets
description: "Route Porcupine keyword inventories, trained wake-word assets, and
  language/platform model selection."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# custom-keywords-and-assets

Use this sub-skill when the task is about choosing, training, or packaging Porcupine keyword/model assets instead of writing the audio-processing loop.

## Owns
- Built-in keyword inventory and keyword-file naming.
- Custom wake-word training and the resulting asset handoff.
- Language-specific `.pv` model selection.
- Platform/resource matching for the supported SDK families.
- AccessKey, quota, and network constraints around training.

## Route elsewhere
- SDK-specific capture/process/release loops go to the relevant SDK sub-skill.
- Binary-to-C-array conversion and MCU embedding go to the sibling `../c-and-embedded/` skill.
- Broad install/import or package-wide troubleshooting stays with the root Porcupine skill.

## References
- [`references/keyword-and-model-assets.md`](references/keyword-and-model-assets.md)
- [`references/training-api-reference.md`](references/training-api-reference.md)
- [`references/troubleshooting.md`](references/troubleshooting.md)
