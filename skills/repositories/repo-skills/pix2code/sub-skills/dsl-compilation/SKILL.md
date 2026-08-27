---
name: dsl-compilation
description: "Compile and troubleshoot pix2code .gui DSL files into Bootstrap
  HTML, Android XML layout, or iOS Storyboard scaffold output."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# DSL Compilation

Use this sub-skill when the user has a pix2code `.gui` file or generated DSL text and wants platform scaffold output, token validation, or compiler troubleshooting.

## Read first

- [references/dsl-reference.md](references/dsl-reference.md) explains the DSL grammar, nesting tokens, platform token differences, and validation rules.
- [references/platform-compilation.md](references/platform-compilation.md) gives concrete compile recipes and output expectations for web, Android, and iOS.
- [references/troubleshooting.md](references/troubleshooting.md) covers unknown tokens, malformed braces, unstable placeholder text, and output-location surprises.
- [scripts/compile_gui.py](scripts/compile_gui.py) is the bundled self-contained compiler helper; use it instead of relying on original checkout scripts.

## Quick workflow

1. Confirm the input is a `.gui` file or DSL text that uses pix2code tokens.
2. Choose one target platform: `web`, `android`, or `ios`.
3. Run the bundled compiler with a deterministic seed when a stable test output matters:

```bash
python sub-skills/dsl-compilation/scripts/compile_gui.py --platform web --input screen.gui --output screen.html --seed 7
```

4. Inspect the generated file for the platform-specific signal:
   - web: `<html>`, Bootstrap container/row/column markup.
   - Android: XML declaration plus `LinearLayout` root.
   - iOS: Storyboard XML `document` and `viewController` tags.
5. If the compiler reports unknown tokens, compare the DSL against [references/dsl-reference.md](references/dsl-reference.md). Platform vocabularies differ; a token valid for web may not exist for Android or iOS.

## Route by task

| User asks for | Do this |
| --- | --- |
| "Compile this `.gui` to HTML" | Use `compile_gui.py --platform web`; read platform reference if the output needs Bootstrap details. |
| "Compile generated DSL for Android/iOS" | Use the same helper with `--platform android` or `--platform ios`; warn that generated IDs/text are placeholders. |
| "Debug a compiler KeyError" | Read troubleshooting, validate braces and token names, then rerun the helper for a clearer error. |
| "Explain pix2code DSL" | Read `dsl-reference.md`; do not send the user back to original mapping JSON files. |
| "Make exact original compiler behavior" | Note that this helper preserves the original mapping semantics but adds deterministic seeds and diagnostics. For checkout maintenance, original scripts assumed they were run from the `compiler/` directory. |

## Boundaries

This sub-skill owns DSL parsing and platform template rendering. It does not own model sampling from screenshots; route screenshot-to-DSL artifact questions to [../sampling-and-generation/SKILL.md](../sampling-and-generation/SKILL.md). It does not own dataset splitting or model training; route those to [../data-and-training/SKILL.md](../data-and-training/SKILL.md).

## Validation checklist

- The input path exists and uses `.gui` content.
- Braces are balanced and each opening token has a known platform mapping.
- Leaf tokens separated by commas are valid for the selected platform.
- Output extension matches the selected platform: `.html`, `.xml`, or `.storyboard`.
- Runtime instructions use bundled scripts and references only.
