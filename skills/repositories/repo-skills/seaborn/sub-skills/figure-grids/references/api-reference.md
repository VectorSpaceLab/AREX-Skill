# Figure Grids API Reference

## FacetGrid

Key methods and attributes:

- `FacetGrid(data, row=None, col=None, hue=None, col_wrap=None, sharex=True, sharey=True, height=3, aspect=1, ...)`.
- `.map(func, *args, **kwargs)` maps positional arrays.
- `.map_dataframe(func, *args, **kwargs)` maps with DataFrame subsets and named variables.
- `.facet_data()` yields facet keys and subsets for custom loops.
- `.set_axis_labels(x_var=None, y_var=None)`, `.set_titles(...)`, `.set(...)`, `.tick_params(...)`.
- `.refline(...)` adds reference lines.
- `.add_legend(...)` and `sns.move_legend(g, ...)` manage legends.
- `.figure` is the matplotlib `Figure`; `.axes` is a 2D axes array; `.axes_dict` maps facet keys to axes.

## PairGrid and pairplot

- `pairplot(data, hue=None, vars=None, x_vars=None, y_vars=None, kind="scatter", diag_kind="auto", corner=False, plot_kws=None, diag_kws=None, grid_kws=None)` is a convenience wrapper.
- `PairGrid(data, hue=None, vars=None, x_vars=None, y_vars=None, corner=False, ...)` is lower-level.
- Use `.map_lower()`, `.map_upper()`, `.map_diag()`, `.map_offdiag()`, or `.map()` to customize cells.

## JointGrid and jointplot

- `jointplot(data=None, x=None, y=None, hue=None, kind="scatter", height=6, ratio=5, space=.2, joint_kws=None, marginal_kws=None)` is a convenience wrapper.
- `JointGrid(data=None, x=None, y=None, hue=None, height=6, ratio=5, space=.2, ...)` exposes `.plot()`, `.plot_joint()`, `.plot_marginals()`, `.refline()`, and `.set_axis_labels()`.

## Figure-level Return Objects

`relplot`, `displot`, `catplot`, and `lmplot` return `FacetGrid`-like objects. `clustermap` returns `ClusterGrid`. Use grid methods and `g.figure` for customization.
