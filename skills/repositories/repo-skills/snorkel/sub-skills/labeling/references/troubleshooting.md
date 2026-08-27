# Labeling Troubleshooting

Start with `LFAnalysis` whenever the label matrix or label model behaves strangely.

## LF authoring and application issues

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Everything is `-1` | All LFs abstain, the input fields are wrong, or a preprocessor is not producing the expected field. | Inspect `LFAnalysis.label_coverage()` and `lf_summary()`. Check field names and the LF polarity logic. |
| One LF seems duplicated | Two LFs share the same name. | Rename the LF. Unique names are required before application. |
| `@labeling_function` / `@nlp_labeling_function` / `@spark_nlp_labeling_function` raises a missing-parentheses error | The decorator was used without `()` | Write `@labeling_function()` even when no arguments are needed. |
| Preprocessor returns `None` | A preprocessor aborted without returning a data point | Make sure every preprocessor returns the updated data point. |
| LF failures are not visible | `fault_tolerant=False`, or `return_meta=True` was not requested | Enable `fault_tolerant=True` and, for Pandas / list / NumPy appliers, ask for metadata with `return_meta=True`. The metadata fault counts are keyed by LF name. |

## LabelModel and voter issues

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `L_train should have at least 3 labeling functions` | The matrix has fewer than 3 columns | Add more LFs or stay with a voter baseline. |
| `L_train has cardinality ...` | LF outputs exceed the declared class cardinality | Check that LF labels are only `-1` or `0..cardinality-1`, and set `cardinality` correctly. |
| `class_balance has ... entries` | The class-balance prior length does not match `cardinality` | Pass a class-balance vector with exactly one value per class. |
| `Class balance prior is 0 for class(es) ...` | A prior class probability is zero | Use a nonzero prior for every class. |
| `prec_init must have shape ...` | Per-LF precision prior length does not match the number of LFs | Pass one precision value per LF, or use a scalar. |
| `device=cuda but CUDA not available` | CUDA was requested but the runtime has no CUDA | Use `device='cpu'` or install a CUDA-enabled runtime. |
| Training loss becomes `NaN` | Learning rate or initialization is too aggressive | Lower `lr`, reduce regularization surprises, or simplify the label matrix. |
| Predictions are all abstains | The matrix is weakly connected, all LFs disagree, or the tie-break policy is `abstain` | Re-check LF polarity and coverage. Try a voter baseline to see whether the matrix is usable. |

## spaCy / NLP issues

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| spaCy model load fails | The default `en_core_web_sm` model is not installed | Install the model or pass a different `language` value that is available in the environment. |
| A later `NLPLabelingFunction` with different settings raises `ValueError` | The LF class already cached a different spaCy configuration | Reuse the same NLP parameters for that LF class or restart with a fresh process. |
| Token / entity fields are missing | The LF is reading the wrong doc field or the preprocessor did not run | Check `text_field`, `doc_field`, and the LF `pre` list. |

## Dask issues

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `PandasParallelLFApplier` rejects `n_parallel=1` | The parallel applier requires at least 2 partitions | Use `PandasLFApplier` for single-process runs. |
| Dask multiprocessing hangs or errors | The local scheduler choice is not a good fit for the runtime | Try `scheduler='threads'` or a `Client`. Keep the data points serializable and use a small fixture first. |
| Dask LF results look inconsistent | Partition data or preprocessing has side effects | Make the LF and preprocessors pure and deterministic. |

## Spark issues

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Spark imports fail | Java and/or PySpark are missing | Install the optional Spark dependencies before using Spark LFs or the Spark smoke script. |
| Spark starts but cannot resolve the local hostname | The local environment needs a hostname hint | Set `SPARK_LOCAL_HOSTNAME=localhost` before starting Spark. |
| Spark LF execution fails on serialization | The LF or preprocessor closes over unserializable objects | Keep Spark LFs and preprocessors simple, module-level, and serializable. |

## Quick recovery sequence

1. Verify the LF matrix with `LFAnalysis`.
2. Compare against `MajorityLabelVoter`.
3. Check label cardinality and class-balance assumptions.
4. Reduce the data to a tiny in-memory fixture.
5. Retry the relevant smoke script only after the matrix looks sane.
