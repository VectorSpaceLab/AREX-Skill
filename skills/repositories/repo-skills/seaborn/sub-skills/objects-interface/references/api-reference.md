# Objects Interface API Reference

## Imports

```python
import seaborn.objects as so
```

## Plot Methods

Verified `Plot` method surface:

```python
so.Plot(data=None, *args, **variables)
Plot.on(target)
Plot.add(mark, *transforms, orient=None, legend=True, label=None, data=None, **variables)
Plot.pair(x=None, y=None, wrap=None, cross=True)
Plot.facet(col=None, row=None, order=None, wrap=None)
Plot.scale(**scales)
Plot.share(**shares)
Plot.limit(**limits)
Plot.label(title=None, legend=None, **variables)
Plot.layout(size=<default>, engine=<default>, extent=<default>)
Plot.theme(config)
Plot.save(loc, **kwargs)
Plot.show(**kwargs)
Plot.plot(pyplot=False)
```

`Plot` is immutable-style: methods return a new or updated plot object for further chaining. Keep the chain assigned when building incrementally.

## Object Families

| Family | Public objects | Use for |
| --- | --- | --- |
| Marks | `Dot`, `Dots`, `Line`, `Lines`, `Path`, `Paths`, `Dash`, `Range`, `Bar`, `Bars`, `Area`, `Band`, `Text` | Visual representation of each layer. |
| Stats | `Agg`, `Est`, `Count`, `Hist`, `KDE`, `Perc`, `PolyFit` | Transform data before drawing. |
| Moves | `Dodge`, `Jitter`, `Norm`, `Shift`, `Stack` | Adjust layer positions or normalization. |
| Scales | `Boolean`, `Continuous`, `Nominal`, `Temporal` | Control mapping from data values to visual properties. |
| Base classes | `Mark`, `Stat`, `Move`, `Scale` | Type boundaries for extension/introspection, not usually instantiated directly. |

## Layering Pattern

```python
p = (
    so.Plot(df, x="time", y="value", color="group")
    .add(so.Line(), so.Agg())
    .add(so.Dot(alpha=.5), so.Jitter(width=.1))
    .facet(col="group")
    .label(title="Layered objects plot", x="Time", y="Value")
)
p.save("objects_plot.png")
```

Pass data-independent visual values as mark constructor arguments or direct keyword values. Pass mapped variables as `Plot(...)` or `.add(..., property="column")` variable assignments.

## Rendering and Output

- `.plot()` returns a seaborn Plotter object; use it for advanced integration or inspection.
- `.show()` displays through matplotlib/pyplot and returns `None`.
- `.save(path)` writes a file and returns the `Plot` for chaining.
- `.on(ax_or_figure)` directs rendering to an existing matplotlib target when explicit figure ownership matters.

## Optional SciPy Caveat

`so.KDE(cumulative=True)` requires SciPy. Non-cumulative KDE can use seaborn's fallback implementation, but SciPy is the expected installed-path for full statistical plotting coverage.
