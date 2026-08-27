# Bar Comparison Troubleshooting

Use this guide when a grouped, wide comparison, or horizontal ablation bar figure
fails validation, looks crowded, or exports incorrectly.

## Data shape failures

### `mean shape does not match methods/metrics`

Symptoms:

- Bars are missing or repeated.
- Matplotlib raises an index error while looping metrics.
- A validation message says `mean` has shape `(a, b)` but expected
  `(len(methods), len(metrics))`.

Fix:

1. Convert the table to an explicit array before plotting: `mean = np.asarray(mean, dtype=float)`.
2. Confirm rows correspond to methods or ablation variants.
3. Confirm columns correspond to metrics or conditions.
4. If your data are transposed, use `mean = mean.T` intentionally and update the
   schema comment.
5. Apply the same shape correction to `err`, `std`, or confidence intervals.

### Error bars have the wrong shape

Symptoms:

- Matplotlib complains about `yerr` or `xerr` shape.
- Error caps are drawn for the wrong bars.

Fix:

- For vertical multi-metric panels, use `err[:, metric_idx]` inside the metric
  loop, not the full 2D array.
- For horizontal ablation panels, use `err[:, metric_idx]` as `xerr`.
- If errors are asymmetric, store them as a pair `(lower, upper)` per metric and
  pass a 2-row array for the current axis.
- Do not mix per-fold raw results with already-computed means unless you compute
  `mean` and `std` consistently first.

### Ablation codes do not decode

Symptoms:

- Labels are blank or nonsensical.
- Validation says a binary code length differs from the component list.

Fix:

- Every code must have the same length as `components`.
- Only `0` and `1` are valid code characters.
- Map `1` to included component names and `0` to omitted components.
- Use `None` or `No components` for an all-zero row.
- If the intended labels are prose rather than codes, bypass decoding and pass
  the labels directly.

## Annotation failures

### Labels overlap error bars

Cause: labels were placed at the bar height instead of above the error cap.

Fix: for vertical bars place labels at `value + error + pad`; for horizontal
bars place labels at `value + error + pad` along x. Increase axis limits after
adding labels.

### Labels are clipped by the axis

Fix:

1. Compute annotation positions before finalizing limits.
2. Increase top or right margin by at least one label pad.
3. Run `tight_layout` after setting labels and legends.
4. If clipping remains in PDF, save with a small `bbox_inches="tight"` pad only
   after confirming it does not resize panels inconsistently.

### Inside-bar labels are unreadable

Cause: text color does not contrast with the bar fill.

Fix:

- Use luminance to choose white text on dark fills and black text on light fills.
- Add a dark stroke around pale highlight text only for special callouts.
- Move labels above bars when the bar is too short for inside placement.

## Legend failures

### Legend covers the data

Fix: add a dedicated legend-only axis and call `legend_ax.set_axis_off()` before
placing the legend. Use handles from the first data axis to keep colors
consistent.

### Legend has duplicate entries

Cause: every subplot calls `label=...` and all handles are concatenated.

Fix: collect handles only from the first representative axis, or deduplicate by
label with an ordered dictionary before drawing the legend.

### Legend is too wide

Fix options:

- Use `ncols=2` or `ncols=3` in the legend-only axis.
- Shorten method labels with a table note in the caption.
- Wrap long labels manually with `\n`.
- Switch from vertical bars to horizontal bars if labels are central to the
  comparison.

## Color, hatch, and print failures

### Bars are indistinguishable in grayscale

Fix:

- Add `edgecolor="black"` and `linewidth` at least 1.5.
- Add hatches for subtypes or prompt families.
- Use alpha gradients only for ordered ablation completeness, not unrelated
  methods.
- Reserve the darkest blue for the key method and neutrals for background
  baselines.

### Hatches do not appear in the PDF

Fix:

- Ensure each bar has a visible edge color.
- Avoid very thin linewidths.
- Use common hatch patterns (`/`, `\\`, `x`, `-`, `.`) rather than dense custom
  patterns.
- Test both PNG and PDF because hatch density can differ by viewer.

### Alpha gradients look washed out

Fix:

- Keep the strongest/full variant at alpha 1.0.
- Use a minimum alpha around 0.25-0.35 for print.
- Add black edges so pale bars remain visible.
- If the ablation order is not meaningful, use distinct hatches instead of an
  alpha gradient.

## Axis-scale failures

### Tight y-limits look misleading

Fix: include zero when the metric is a count, cost, runtime, or percentage where
absolute magnitude matters. For high-range scores, tighten the range but mention
that the y-axis is truncated in the caption if required by the venue.

### Values are negative but the lower limit is zero

Fix: compute limits from `value - error`, include a small margin below the
minimum, and draw a horizontal zero line when comparisons cross zero.

### Log-scale speed bars fail

Symptoms: `Data has no positive values` or an empty log plot.

Fix:

- Use log scale only for strictly positive speeds, rates, or throughputs.
- If raw inference times are provided, convert to throughput as `1 / time` only
  after checking all times are positive.
- For zeros, use a linear scale with an explicit `0` bar or ask the user how to
  handle censored/timeout values.
- Place annotations multiplicatively above bars, e.g. `value * 1.08`.

## Optional TeX failures

### `RuntimeError: Failed to process string with tex`

Cause: `text.usetex=True` was enabled but a system LaTeX installation is not
available or required packages/fonts are missing.

Fix:

- Disable TeX unless exact TeX rendering is required.
- Use matplotlib mathtext for simple symbols such as `R$^2$`, `↑`, and `↓`.
- If exact TeX is mandatory, install and verify LaTeX outside the plotting
  script, then rerun with `use_tex=True`.
- Keep the non-TeX fallback as the default for portable bundled scripts.

### TeX labels render literally

Fix: when TeX is disabled, avoid commands that mathtext does not support. Use
plain text plus simple math segments rather than full TeX macros.

## Font failures

### Helvetica is missing

Matplotlib may warn that Helvetica is not found and use a fallback. This is not
blocking for the house style.

Fix:

- Set a fallback family such as `['Arial', 'Helvetica', 'DejaVu Sans', 'sans-serif']`.
- Avoid relying on exact font metrics for label placement.
- Re-run layout after font changes.

### Text is too large after fallback

Fix: reduce font sizes for legends and annotations first; keep axis labels
readable. For dense panels, enlarge the figure width rather than shrinking all
fonts aggressively.

## Output-directory and file failures

### `FileNotFoundError` on save

Cause: parent directory does not exist.

Fix: create the parent directory with `Path(output).parent.mkdir(parents=True,
exist_ok=True)` before `savefig`.

### Output file is empty or missing

Fix:

1. Confirm the script uses a headless backend before importing `pyplot` in batch
   contexts.
2. Confirm the selected formats are supported: `png`, `pdf`, `svg`, `eps`,
   `jpg`, `jpeg`, `tif`, or `tiff`.
3. Check that `fig.savefig(...)` runs before `plt.close(fig)`.
4. Verify each output path exists and has nonzero file size.

### Existing files are overwritten unexpectedly

Fix: choose a new basename through the script's `--output` argument or add a
project-level overwrite confirmation before running destructive batch exports.
The bundled template writes deterministic filenames by design.

## When to return to routing

Route to another sub-skill if troubleshooting reveals that the requested figure
is not bar-oriented:

- Heatmap or matrix text-color issues belong to `trend-radar-heatmap-figures`.
- Radar normalization and trend/event annotation issues belong to
  `trend-radar-heatmap-figures`.
- Scatter cloud, manifold, sphere, or arrow-layout issues belong to
  `concept-manifold-diagrams`.
