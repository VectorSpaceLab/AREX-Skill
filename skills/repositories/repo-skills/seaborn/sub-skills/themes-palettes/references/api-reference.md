# Theme and Palette API Reference

## Theme and Context Functions

```python
sns.set_theme(context="notebook", style="darkgrid", palette="deep", font="sans-serif", font_scale=1, color_codes=True, rc=None)
sns.axes_style(style=None, rc=None)
sns.set_style(style=None, rc=None)
sns.plotting_context(context=None, font_scale=1, rc=None)
sns.set_context(context=None, font_scale=1, rc=None)
sns.set_palette(palette, n_colors=None, desat=None, color_codes=False)
sns.reset_defaults()
sns.reset_orig()
sns.set(...)
```

Use `axes_style`, `plotting_context`, and `color_palette` as context managers when changes should be temporary.

## Palette Functions

```python
sns.color_palette(palette=None, n_colors=None, desat=None, as_cmap=False)
sns.hls_palette(...)
sns.husl_palette(...)
sns.mpl_palette(...)
sns.dark_palette(...)
sns.light_palette(...)
sns.diverging_palette(...)
sns.blend_palette(...)
sns.xkcd_palette(...)
sns.crayon_palette(...)
sns.cubehelix_palette(...)
sns.set_color_codes(...)
sns.palplot(palette)
```

- Categorical data needs distinct colors; use `deep`, `muted`, `pastel`, `bright`, `dark`, `colorblind`, HLS/HUSL, or qualitative matplotlib palettes.
- Sequential numeric data needs ordered luminance; use `rocket`, `mako`, cubehelix, matplotlib sequential maps, `light_palette`, or `dark_palette`.
- Diverging data needs a meaningful center; use `diverging_palette` or a diverging matplotlib colormap.
- `as_cmap=True` returns a matplotlib colormap for continuous mappings.

## Interactive Widgets

`choose_colorbrewer_palette`, `choose_cubehelix_palette`, `choose_light_palette`, `choose_dark_palette`, and `choose_diverging_palette` require `ipywidgets` and an interactive notebook-like environment.
