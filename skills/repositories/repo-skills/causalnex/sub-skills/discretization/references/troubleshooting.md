# Discretization Troubleshooting

## Constructor and parameter validation

- `... is not a recognised method`: choose one of the supported methods.
- `method expects num_buckets`: provide `num_buckets` for `uniform` or `quantile`.
- `method expects outlier_percentile`: provide a value in `[0, 0.5)` for `outlier`.
- `method expects numeric_split_points`: supply split points for `fixed`.
- `method expects percentile_split_points`: supply split points for `percentiles`.

## Split-point issues

- `numeric_split_points must be monotonically increasing`: sort the list before calling `Discretiser`.
- `percentile_split_points must be between 0 and 1`: pass true percentiles rather than percentages.
- `percentile_split_points must be monotonically increasing`: sort the percentile list.

## Tree-based issues

- `mode, ... is not valid`: use `single` or `multi`.
- If the multi-feature tree skips a feature, set `split_unselected_feat=True` or discretize that feature with `single` mode.
- `target_continuous=True` is not supported by the MDLP path used here; keep the target discrete.

## Optional MDLP issues

- `ImportError` from `MDLPSupervisedDiscretiserMethod`: install `mdlp-discretization~=0.3.3`.
- Build failures usually mean the environment needs `Cython` or a C/C++ toolchain.
- If the optional package is hard to build, continue with `Discretiser` or tree-based splits instead of blocking the whole workflow.
