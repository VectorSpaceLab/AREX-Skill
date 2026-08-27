# CLI Reference

## Entry Points

The package installs `pix2tex`, `pix2tex_cli`, `pix2tex_gui`, and `latexocr`.
All route through the same launcher. `latexocr` and `pix2tex_gui` select the GUI
route; `pix2tex` defaults to CLI unless `--gui` is passed.

## Flags

```text
-t, --temperature FLOAT   Softmax sampling frequency.
-c, --config PATH         Model config YAML.
-m, --checkpoint PATH     Model weights path.
--no-cuda                 Force CPU.
--no-resize               Disable auxiliary image-resizer model.
-s, --show                Render predicted LaTeX through local TeX tooling.
-k, --katex               Render in a browser with katex.org.
--gui                     Use GUI route.
file ...                  Image file(s); if omitted, read clipboard/interactive prompt.
```

## Safe Commands

```bash
pix2tex --help
pix2tex --no-cuda --no-resize path/to/equation.png
pix2tex --no-cuda -t 0.05 path/to/equation.png
```

`--help` exits before model loading. Commands with image paths instantiate the
model and may download weights if absent.

## Interactive CLI Notes

Without file arguments, the CLI creates a history file in the user data
directory and enters a prompt. It supports:

- empty input: try clipboard or the previous image;
- `h`, `?`, `help`: print help text;
- `show`, `katex`, `no_resize`: toggle settings;
- `t=0.XX`: set temperature;
- `x`: exit.
