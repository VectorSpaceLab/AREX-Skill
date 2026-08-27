# Figure Grid Troubleshooting

## `ax=` Is Ignored

Figure-level functions own their figures. Use axes-level functions when drawing into existing axes, or customize the returned grid.

## Need Exact Figure Size

For figure-level functions, start with `height` and `aspect`; then call `g.figure.set_size_inches(width, height)` for exact final size.

## Cannot Find an Axes

Use `g.ax` only for one-facet grids that expose a single axes. For multi-facet layouts, use `g.axes.flat` or `g.axes_dict`.

## Legend Move Fails

`sns.move_legend(obj, ...)` requires an existing legend on a seaborn grid, matplotlib Axes, or Figure. If no legend exists, add one (`g.add_legend()`) or ensure a semantic mapping such as `hue` created legend data.

## Plot Not Showing

Grid objects still rely on matplotlib display behavior. In scripts save `g.figure.savefig(...)`; in notebooks assign the grid object or end the plotting line with a semicolon.
