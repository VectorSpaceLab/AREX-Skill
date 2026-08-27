# Platform Compilation Recipes

## Purpose

Read this for concrete commands and expected outputs when converting pix2code DSL into scaffold code.

## Web HTML

Use `--platform web` for Bootstrap-style HTML output:

```bash
python sub-skills/dsl-compilation/scripts/compile_gui.py --platform web --input screen.gui --output screen.html --seed 1
```

Expected signal: the output starts with `<html>`, contains a Bootstrap stylesheet reference, and nests DSL rows/columns inside `<main class="container">`.

## Android XML

Use `--platform android` for an Android layout XML scaffold:

```bash
python sub-skills/dsl-compilation/scripts/compile_gui.py --platform android --input screen.gui --output screen.xml --seed 1
```

Expected signal: the output starts with an XML declaration and a vertical `LinearLayout` root. Android placeholder IDs are generated as short alphabetic IDs.

## iOS Storyboard

Use `--platform ios` for a storyboard scaffold:

```bash
python sub-skills/dsl-compilation/scripts/compile_gui.py --platform ios --input screen.gui --output screen.storyboard --seed 1
```

Expected signal: the output starts with an XML declaration, contains a `document` element with `targetRuntime="iOS.CocoaTouch"`, and includes a `viewController` scene.

## Output path behavior

If `--output` is omitted, the bundled helper writes next to the input using the platform extension. Prefer explicit `--output` when writing into temporary or review directories.
