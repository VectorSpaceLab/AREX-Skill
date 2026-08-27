# Plotting CLI reference

The renderer is `dreamerv2.common.plot` (`common/plot.py` inside the
installed package). It is a batch renderer, not an interactive notebook, and
forces Matplotlib's `Agg` backend. It imports pandas, NumPy, and Matplotlib
before argument parsing, so plotting and even `--help` need those packages
available. The legacy module also imports a top-level `common` alias; a bare
`python -m dreamerv2.common.plot` can fail in an installed package. Use the
bundled adapter from arbitrary working directories:

```sh
python /path/to/evaluation/scripts/plot_help.py --renderer-help
python /path/to/evaluation/scripts/plot_help.py --render \
  --indir /logs --outdir /plots --xaxis step --yaxis eval_return
```

`--render` resolves the installed `dreamerv2` package and runs its renderer
without an original-checkout path. The adapter also offers the
standard-library `--validate-layout` checker; it does not copy the long
renderer or rewrite its outputs.

## Required and path flags

| Flag | Default | Meaning |
|---|---:|---|
| `--indir PATH [PATH ...]` | required | One or more roots recursively containing JSONL runs. |
| `--outdir PATH` | required | Destination for `runs.json`, `curves.png`, and `curves.pdf`. |
| `--subdir True\|False` | `True` | Append the first `indir` basename to `outdir` when true. |
| `--indir-prefix PATH` | none | Prefix every supplied `indir` after parsing. |
| `--xaxis NAME` | `step` | JSONL column used for x values. |
| `--yaxis NAME` | `eval_return` | JSONL column used for y values. |
| `--xmult FLOAT` | `1` | Multiply x values after loading. |
| `--maxval FLOAT` | `0` | Replace/clamp infinite and y values; zero means no useful clamp. |

A `True`/`False` value is required for boolean flags. Do not use Python-style
`true`, `false`, `0`, or `1`; the parser indexes the exact strings
`False` and `True`.

## Selection, curves, and layout

| Flag | Default | Meaning |
|---|---:|---|
| `--tasks REGEX [REGEX ...]` | `.*` | Regexes matched against task directory names. |
| `--methods REGEX [REGEX ...]` | `.*` | Regexes matched against method directory names. |
| `--baselines REGEX [REGEX ...]` | `d4pg rainbow_sticky human_gamer impala` | Regexes for discovered baseline method names. |
| `--prefix True\|False` | `False` or auto with multiple roots | Prefix seeds, and when true method names, by input-root index. |
| `--bins FLOAT` | `-1` | Width; `-1` selects task-family defaults. |
| `--agg MODE` | `std1` | Curve aggregation: `none`, `std1`, `per0`, `per5`, or `per25`. |
| `--add NAME [NAME ...]` | `auto seeds` | Extra panels: `none`, `mean`, `median`, `gamer_median`, `gamer_mean`, `record_mean`, `clip_record_mean`, `seeds`, `human_above`, `human_below`, or `auto`. |
| `--cols INT` | `6` | Maximum subplot columns. |
| `--size WIDTH HEIGHT` | `2.5 2.3` | Size per subplot in inches. |

A pattern is a regular expression, not a shell glob. Quote it when it contains
shell metacharacters, for example `--tasks 'atari_(pong|alien)'`.

## Axes and appearance

| Flag | Default | Meaning |
|---|---:|---|
| `--xlim LOW HIGH` | none | X-axis limits. |
| `--ylim LOW HIGH` | none | Y-axis limits. |
| `--ylimticks True\|False` | `True` | Include y-limit values among ticks. |
| `--xlabel TEXT` / `--ylabel TEXT` | none | Axis labels. |
| `--xticks INT` / `--yticks INT` | `6` / `5` | Maximum locator tick counts. |
| `--dpi INT` | `80` | PNG resolution. |
| `--labels OLD NEW [OLD NEW ...]` | none | Even-length label mapping pairs. |
| `--palette NAME [COLORS ...]` | `contrast` | Named palette (`discrete`, `contrast`, `gradient`, `baselines`) or color list. |
| `--legendcols INT` | `4` | Legend columns. |
| `--colors METHOD COLOR [METHOD COLOR ...]` | none | Even-length method/color pairs. |

`--labels` and `--colors` are list-valued pair arguments and must contain an
even number of values. `--tasks`, `--methods`, and `--baselines` consume one
or more values; put the output path and later flags after the whole list or
use a clear command line ordering.

## Loading, binnings, and aggregation

The loader finds all `**/*.jsonl` below each input root and parses each file
as a DataFrame. It reports the number considered and selected. Invalid JSON in
any line except an incomplete final line makes that file invalid; invalid files
are skipped. Rows without both x and y values are dropped. If a requested
column is absent, that run is skipped. Multiple runs of the same task/method
are plotted as separate lines with `--agg none`, or are stacked and summarized
otherwise.

With `--bins -1`, bin widths are task-family based: Atari `1e6`, DMC `1e4`,
Crafter `1e4`, and all other task prefixes `1e5`. Explicit `--bins 0` disables
binning; a positive width creates borders from zero through the maximum x and
uses the NaN-aware mean in each interval. Empty buckets are NaN. When curves
are combined, they are aligned to the longest x grid and shorter runs are
padded with their last y value. This makes comparing stopped runs convenient
but can visually extend a last value; record the run lengths and do not
interpret padding as new observations.

`std1` plots nan-mean with one nan-standard-deviation band. `per0`, `per5`,
and `per25` plot percentile bands `(0,50,100)`, `(5,50,95)`, and
`(25,50,75)`. `none` leaves each seed line separate. Combined `mean` and
`median` panels aggregate across tasks after binning; `seeds` counts finite
values. Gamer/record panels normalize per task using low/high baseline scores.
Missing low or high baselines are reported per task and those task values are
not normalized.

Before plotting, the program prints discovered metric keys, writes
`<outdir>/runs.json` containing records with `task`, `method`, `seed`, `xs`,
and `ys`, then writes `curves.png` and `curves.pdf`. It tries `pdfcrop` and
prints an optional `texlive-extra-utils` hint if unavailable.

## Baseline files and result archives

`load_baselines()` searches the installed module's package-relative
`../scores` directory for `**/*_baselines.json`. For this source layout that is
a `scores/` directory beside the `dreamerv2` package directory (not
necessarily the repository-root `scores/` directory). Each matching file must
be a JSON object shaped as task -> method -> numeric scalar. Baseline method
names are selected by the regexes in `--baselines`. `--prefix True` labels them
with `baseline_` and can help avoid method-name collisions.

The checkout's repository-root `scores/baselines.json` is useful evidence of
this shape, but it is outside the path searched by `dreamerv2/common/plot.py`
and its basename also does **not** satisfy the renderer's `_baselines.json`
glob. The other root `scores/*.json` archives are precomputed curve records or
schedules, not inputs automatically consumed by `load_baselines()`. The
distribution metadata also does not list the score files as package data, so a
packaged installation may have no discoverable baselines at all. Treat a
message such as `No baselines found` as a data/layout fact, not as proof that
the run is wrong. If you need baselines, provide a package-visible file with
the expected suffix and shape, or plot without baseline panels.

When `yaxis` does not contain the substring `return`, the parser clears
baseline patterns. This prevents nonsensical baseline overlays for losses or
replay counters. A regex mismatch similarly yields zero selected baselines;
check method names with the printed `Baselines` statistics and use an exact
or broader expression such as `'.*'` only when appropriate.

## Canonical examples

Plot Atari evaluation returns:

```sh
python /path/to/evaluation/scripts/plot_help.py --render \
  --indir "$HOME/logdir" --outdir "$HOME/plots" \
  --xaxis step --yaxis eval_return --bins 1e6
```

Compare two roots and keep method identities separate:

```sh
python /path/to/evaluation/scripts/plot_help.py --render \
  --indir /logs/seed-group-a /logs/seed-group-b \
  --outdir /plots --subdir False --prefix True \
  --tasks 'atari_(pong|alien)' --methods 'dreamer.*' \
  --baselines 'random' 'human_gamer' --agg per5 --add none
```

Inspect scalar keys without rendering:

```sh
python /path/to/evaluation/scripts/plot_help.py \
  --validate-layout --indir /logs --xaxis step --yaxis eval_return
```
