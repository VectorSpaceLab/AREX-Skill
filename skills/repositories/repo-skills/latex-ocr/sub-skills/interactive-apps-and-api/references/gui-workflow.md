# GUI Workflow

## Launching

Install GUI dependencies and run:

```bash
pip install "pix2tex[gui]"
latexocr
```

`latexocr`, `pix2tex_gui`, or `pix2tex --gui` route to the GUI. The GUI creates
a Qt window, loads `LatexOCR`, and supports snipping, drag/drop image files,
clipboard paste, retry, temperature adjustment, and output formatting.

## Screenshot Tool Selection

The GUI checks `SCREENSHOT_TOOL` first. Supported values in the source are:

- `gnome-screenshot`
- `grim` with `slurp`
- `spectacle`
- `pil`

If the default is wrong for the compositor, set the variable before launching:

```bash
SCREENSHOT_TOOL=grim latexocr
```

## Output Formats

The GUI stores the raw prediction and can format it as:

- raw LaTeX;
- `$...$` inline LaTeX;
- `$$...$$` display LaTeX;
- SymPy string via `latex2sympy2`.

It renders display output with bundled MathJax resources and copies formatted
text to the clipboard when the formatted textbox changes.

## Desktop Entry Installer

`pix2tex.setup_desktop` writes or removes a Linux `.desktop` entry. It can
mutate `~/.local/share/applications` and asks before overwrite/removal unless
flags are used. Do not run it without explicit user approval.
