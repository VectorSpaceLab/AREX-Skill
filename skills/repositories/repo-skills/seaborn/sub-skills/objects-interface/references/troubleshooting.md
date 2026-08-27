# Objects Interface Troubleshooting

## Unknown Variable or Property

Symptoms: error about an undefined variable, unknown semantic property, or missing column.

Recovery: verify columns in the DataFrame, distinguish variable mappings (`color="column"`) from fixed values (`color="C0"` in a mark), and add layer-specific data only when the layer has its own DataFrame.

## Transform in the Wrong Place

Stats and moves are passed after the mark in `.add(mark, stat_or_move, ...)`. If output is not aggregated, stacked, jittered, or normalized, check that the transform object is passed to `.add()` rather than constructed unused.

## No Display or File Output

`Plot` chains do not render until `.plot()`, `.show()`, or `.save(...)`. In scripts and CI, prefer `.save(path)` with a noninteractive backend.

## SciPy Missing for Cumulative KDE

Install `seaborn[stats]` or avoid cumulative KDE. If density estimation is optional, use `Hist` or a non-cumulative KDE path.

## Objects vs Classic Functions

If the user asks for a one-line `sns.histplot` or `sns.boxplot`, do not force `objects`. Use objects when composition/layering or property grammars are central.
