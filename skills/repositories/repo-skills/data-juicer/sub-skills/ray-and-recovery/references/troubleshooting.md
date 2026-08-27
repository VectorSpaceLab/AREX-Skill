# Troubleshooting

## Ray will not start
- Confirm the `ray` package is installed.
- Try the bundled smoke helper before debugging the recipe.
- If local startup fails, check whether another Ray process is already using the same resources.

## Compatibility problems
- Pay attention to the installed `pandas` version when running Ray mode.
- Keep the local inspection environment small and reproducible before trying a cluster.

## Path and storage problems
- Check that workers can see the dataset, checkpoint, and event-log paths.
- Avoid mixing local-only paths with remote worker storage unless the path is shared.

## Resume problems
- Make sure the same job identity and partition strategy are being reused.
- If the recipe changed, the saved checkpoint may no longer be valid.

## Tracing problems
- Disable tracing if you only need a basic recovery test.
- Re-enable it after the base Ray execution is stable.
