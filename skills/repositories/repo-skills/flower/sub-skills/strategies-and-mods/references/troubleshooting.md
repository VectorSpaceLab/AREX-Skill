# Strategies and mods troubleshooting

## Rounds are skipped unexpectedly

**Symptoms**

- A round never trains or never evaluates.
- Flower logs say training or evaluation will be skipped.

**Likely causes**

- `fraction_train` or `fraction_evaluate` is `0.0`.
- The minimum node counts are higher than the sampled population.

**Recovery**

- Check the strategy constructor values.
- Reduce the minimum node counts or raise the sampling fractions.
- Re-run with `summary()` output visible so the active parameters are obvious.

## Aggregation behaves strangely

**Symptoms**

- Weighted averages look wrong.
- Metrics aggregate to zero or a tiny number.

**Likely causes**

- The expected weighting key is missing from the replies.
- The wrong record key was used for arrays or configs.

**Recovery**

- Confirm the `weighted_by_key` setting.
- Confirm the client replies include the weighting metric.
- Check `arrayrecord_key` and `configrecord_key` if you customized them.

## Mod order confusion

**Symptoms**

- A logger, tracer, or policy mod sees a message state that seems to skip a
  later mod.
- The message changes on the way in but not on the way out.

**Likely causes**

- Application-wide and function-specific mods are wrapping in a different order
  than expected.

**Recovery**

- Remember: application-wide mods wrap the whole app, then function-specific
  mods wrap the selected handler.
- Put a small print or inspection mod at each layer to see the order.
- Keep the order documented in the workflow reference.

## Deprecation or compatibility warnings

**Symptoms**

- `ClientApp` warns about a legacy `client_fn` signature.
- Strategy constructor or wrapper usage feels legacy-specific.

**Likely causes**

- The app is using compatibility code from an older Flower example.

**Recovery**

- Migrate to the modern `Context`-based client signature.
- Prefer the current `ServerApp` / strategy API rather than the deprecated
  compatibility path unless you are intentionally maintaining a legacy example.

## DP or secure-aggregation wrapper mismatch

**Symptoms**

- A privacy wrapper fails to initialize or the example no longer trains.

**Likely causes**

- The wrapper parameters do not match the wrapped strategy's sampling or update
  shape.

**Recovery**

- Verify the wrapped strategy first.
- Check the wrapper-specific clipping/noise arguments.
- Confirm the clients still emit the expected metric and array keys.

## When to stop

If the issue is actually app structure, local runtime routing, or dataset
preparation, hand off to the matching sub-skill instead of debugging the strategy
in isolation.
