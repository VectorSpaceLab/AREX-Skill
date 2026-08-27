# Theme and Palette Troubleshooting

## Invalid Palette Name

Validate with `sns.color_palette(name)` before passing the palette into a plot. Avoid misleading palettes such as `jet` unless the user explicitly requires them.

## Qualitative Palette Requested as Colormap

Qualitative palettes are discrete and may not support `as_cmap=True`. Use a sequential/diverging palette for continuous color variables.

## Theme Leaks Into Later Plots

Use context managers for temporary style/palette changes, or reset with `sns.reset_defaults()` / `sns.set_theme()`.

## Dark Mode Has Poor Contrast

Matplotlib dark styles can override palette settings. Set a high-contrast palette after applying the dark style.

## Widget ImportError

Interactive palette choosers require `ipywidgets`. Use noninteractive palette constructors when running in scripts or headless environments.
