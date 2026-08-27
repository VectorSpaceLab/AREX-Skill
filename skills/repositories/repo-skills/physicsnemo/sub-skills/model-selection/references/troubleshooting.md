# Model-selection troubleshooting

## Wrong family or wrong import path

- Symptom: a user names a model family that exists in the docs but the import path is wrong.
- Likely cause: the family is not exported from `physicsnemo.models` root.
- Fix: use the family subpackage path and confirm the class exists in the installed package.

## Wrong data shape

- Symptom: the recommended family does not fit the tensor layout.
- Likely cause: regular grid, weather grid, mesh/graph, and point-cloud tasks were conflated.
- Fix: re-check the data-shape axis before recommending a family.

## Optional backend or dependency failure

- Symptom: the model imports in a source file but an example or family fails at runtime.
- Likely cause: graph, mesh, weather, NATTEN, Transformer Engine, or example-specific dependencies are missing.
- Fix: document the extra and mark the route as requiring it.

## Migration / rename issues

- Symptom: the user still has Modulus-era import names or old example names.
- Likely cause: the package was renamed and some paths moved.
- Fix: route through the migration guidance and give the current public package name/import path.

## External-data examples

- Symptom: a domain example appears to be a simple smoke test but fails without datasets or checkpoints.
- Likely cause: the example is a full recipe, not a tiny validation script.
- Fix: label the example as reference-only and point to the minimal tutorial or a bundled smoke instead.
