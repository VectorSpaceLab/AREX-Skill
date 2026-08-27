# Visualization and error overlays

## Label rendering

```python
render_label(lbl, img=None, cmap=None, cmap_img='gray', alpha=.5,
             alpha_boundary=None, normalize_img=True)
```

For a 2D label image, returns an RGBA array of shape `lbl.shape + (4,)` and
performs no display or file write. With no `img`, it uses an opaque background.
A 2D image is mapped through `cmap_img`; an RGB/RGBA image uses its channels
and appends alpha to RGB. The first two image axes must equal `lbl.shape[:2]`;
other ranks raise `ValueError`. `cmap` may be a name, callable, RGB/RGBA tuple,
or `None` for a random label map. Alpha values are clipped to `[0,1]`, and
`alpha_boundary=None` means the same alpha as labels.

`random_label_cmap(n=2**16,h=(0,1),l=(.4,1),s=(.2,.8),seed=None)` returns a
Matplotlib `ListedColormap`; pass a seed and small `n` for deterministic tests.
Entry zero is reserved for background.

## Polygon plots

```python
draw_polygons(coord, score, poly_idx, grid=(1,1), cmap=None, show_dist=False)
_draw_polygons(polygons, points=None, scores=None, grid=None, cmap=None,
               show_dist=False)
```

`draw_polygons` expects dense `coord=(Ny,Nx,2,R)`, `score=(Ny,Nx)`, and
`poly_idx=(N,2)` in dense tensor coordinates. It maps centers through `grid`
and adds artists to the current Matplotlib axes. `_draw_polygons` accepts
polygons shaped `(2,R)`, optional `(row,column)` points, and scores; it returns
`None`. `show_dist=True` requires points and draws center-to-ray lines. The
legacy `_draw_polygons(grid=...)` argument has no effect and warns. Plotting is
2D and requires optional Matplotlib; it is not a CPU geometry requirement. For this 0.9.2 snapshot, the inspected Matplotlib 3.11.1 environment exposed neither `matplotlib.colormaps.get_cmap` nor the removed `matplotlib.cm.get_cmap` fallback expected by `render.py`; use a compatible Matplotlib release (for example, `<3.11`) or record plotting as an optional skipped surface while core geometry/NMS remains valid.

## Prediction error overlays

```python
render_label_pred(y_true, y_pred, img=None, cmap_img='gray',
                  normalize_img=True, tp_alpha=.6, fp_alpha=.6,
                  fn_alpha=.6, matching_kwargs=dict(thresh=.5))
```

`y_true` and `y_pred` must have identical 2D shape. The result is RGBA of shape
`y_true.shape+(4,)`: correctly matched predicted objects are green, false
positives red, and missing true objects blue. It calls `matching` with
`report_matches=True`; pairs are classified using the selected threshold and
criterion. The function mutates the supplied `matching_kwargs` dictionary by
setting `report_matches=True`, so pass a fresh dict. Colors are random and are
for visual diagnosis only; store numeric metrics and IDs separately.

Run `matching` before plotting so a Matplotlib or shape error cannot hide a
metric failure. For 3D display/projection or OBJ export, route to the
model/deployment sibling rather than treating a 2D RGBA image as a volume.
