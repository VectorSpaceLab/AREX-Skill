# Workflows

## Add a new model op
1. Subclass `ModelBaseOp`.
2. Decorate the class with `@register`.
3. Implement `get_output_keys()`, `preprocess()`, `postprocess()`, and `__call__()`.
4. Add the new op to a config under `paddlecv/configs/unittest/`.
5. Validate the graph with `scripts/check_name.py`.

## Add a connector op
1. Subclass `ConnectorBaseOp`.
2. Define the input arity and the output key(s).
3. Keep the connector pure: transform intermediate data only.
4. Exercise it with a unittest config such as a crop, rotate, matcher, or tracker graph.

## Add an output op
1. Subclass `OutputBaseOp`.
2. Decide whether the op saves images, writes JSON, returns results, or all three.
3. Make sure the final keys line up with the model/connector outputs that feed the output op.

## Validate a config graph
```bash
python skills/disco/paddlecv/sub-skills/custom-ops/scripts/check_name.py --config paddlecv/configs/unittest/test_custom_op.yml
```

This prints the registered output keys first, then checks that the YAML `Inputs` values exist in the operator registry.

## Debugging strategy
- Start from the operator class that owns the failing output key.
- Confirm the class is imported and registered.
- Check the operator's `get_output_keys()` against the keys returned at runtime.
- Walk the YAML from top to bottom and verify every edge name.

## Common test families
- `test_custom_op.yml` for a custom model op plus output route
- `test_cls_connector.yml`, `test_bbox_crop.yml`, `test_poly_crop.yml` for connector behavior
- `test_fragment_composition.yml`, `test_key_frame_extraction.yml`, `test_table_matcher.yml` for specialized connectors
- `test_ppstructure_filter.yml`, `test_ppstructure_result_concat.yml` for PP-Structure graph helpers
