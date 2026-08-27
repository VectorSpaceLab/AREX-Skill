# Result-analysis workflows

These recipes help you compare saved evo results, export tables, or clean up labels before aggregation.

Create a scratch output directory first:

```bash
mkdir -p out
```

## 1. Compare a set of saved results

```bash
evo_res results/*.zip --use_filenames
```

Use this when you want the embedded statistics printed side by side and the filenames to serve as labels.

## 2. Merge results into one summary

```bash
evo_res results/*.zip --merge --save_plot out/merged_results.pdf
```

This is useful when the results are comparable and you want a single aggregate summary.

## 3. Export a table

```bash
evo_res results/*.zip --save_table out/results.csv
```

If you need a different export shape, first tune the `table_export_*` settings with `evo_config`.

## 4. Rename the embedded estimate label safely

```bash
python scripts/rename_result_estimate.py input.zip renamed-output.zip new_estimate_name
```

Use this when one saved result needs a clearer `est_name` before comparison.

## 5. Run the synthetic result smoke helper

```bash
python scripts/result_smoke.py
```

This helper creates tiny result objects in memory, saves and reloads result archives, and exercises merge plus table export without depending on repo fixtures.

## 6. Handling different metric titles

If you are comparing archives from different metric families or different title text, use:

```bash
evo_res results/*.zip --ignore_title
```

The title warning is there to protect you from silently mixing incompatible numbers.

## 7. What the original demos covered

The repo's result demo shell scripts are interactive and assume the source-tree demo data. This sub-skill distills their behavior into noninteractive commands and the bundled smoke helper.
