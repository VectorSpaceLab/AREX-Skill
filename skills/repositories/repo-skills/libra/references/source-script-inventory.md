# Source script inventory and bundling decisions

This runtime skill does not link to source checkout scripts at runtime. Useful source behavior was distilled or replaced with bundled self-contained helpers.

## Source repo artifacts

| Source path | Decision | Reason |
|---|---|---|
| `tools/examples/Classification/Libra Example-SVM Query.py` | Reference-only / conceptually adapted | Colab export, external dataset upload instructions, and checkout-dependent `wheat.csv` make it unsuitable as a runtime helper. The skill uses self-contained synthetic smoke scripts instead. |
| `tests/tests.py` | Reference-only for native candidate selection | It exercises core `client` queries but depends on repo data paths and can run long ANN/CNN workloads. Representative behaviors are captured in artifacts and smaller smoke scripts. |
| `tools/materials/common_problems.txt` | Distilled into troubleshooting | Its import/path, install-location, EarlyStopping, TextBlob/GCC, and NLTK notes are summarized in `references/troubleshooting.md`. |
| `docs/html/*.html` | Distilled into API references | The HTML docs are not bundled verbatim; their query guidance is summarized in the root and sub-skill references. |
| `libra/dashboard/LibEDA.py` | Reference-only | It is an app implementation tied to Streamlit and source layout. Runtime skill describes how `dashboard()` works and warns about the hardcoded path. |
| `libra/preprocessing/image_preprocessor.py` | Distilled into `vision-and-generative` | Important schema and side-effect behavior is documented; no source code copy is needed. |
| `libra/query/*.py` | Distilled into API guides | Public methods, signatures, model keys, data contracts, and caveats are documented across the root and sub-skills. |

## Bundled helper scripts

| Bundled skill helper | Decision | Owner | Reason |
|---|---|---|---|
| `scripts/libra_compat.py` | Copy/adapt | root | Shared compatibility shim for pandas warning shims and `FutureWarning` suppression. |
| `scripts/inspect_client_surface.py` | Copy/adapt | root | Shared introspection helper for the full `client` surface. |
| `scripts/smoke_tabular_decision_tree.py` | Copy/adapt | root | Shared tiny CPU smoke test that avoids source checkout data. |
| `sub-skills/tabular-modeling/scripts/inspect_tabular_surface.py` | Copy/adapt | tabular-modeling | Focused tabular-method introspection helper. |
| `sub-skills/tabular-modeling/scripts/smoke_tabular_decision_tree.py` | Copy/adapt | tabular-modeling | Focused tabular smoke test for the decision-tree path. |
| `sub-skills/nlp-and-generation/scripts/prepare_nltk_corpora.py` | Copy/adapt | nlp-and-generation | Safe corpus checker and optional downloader for NLTK-backed workflows. |
| `sub-skills/nlp-and-generation/scripts/smoke_text_generation.py` | Copy/adapt | nlp-and-generation | Safe text-generation helper that checks the API surface without forcing heavy downloads by default. |
| `sub-skills/vision-and-generative/scripts/inspect_image_dataset.py` | Copy/adapt | vision-and-generative | Safe image-layout inspector for classwise/setwise/csvwise dataset routing. |
| `sub-skills/vision-and-generative/scripts/smoke_cnn_layout.py` | Copy/adapt | vision-and-generative | Safe synthetic image-layout smoke check that does not train a model. |
