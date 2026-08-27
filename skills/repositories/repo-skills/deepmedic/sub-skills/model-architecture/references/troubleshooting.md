# Model-configuration troubleshooting

Use the static inspector first, then reproduce an architecture build only in a
prepared DeepMedic runtime. The native config loader calls Python `exec`, and
`ModelParameters` frequently reports an error and exits with status 1 rather
than raising a typed exception. Messages below are preserved from the source
where they are useful for recognizing a failure.

## Parse and loader failures

- **Missing path:** `ModelConfig(abs_path_to_cfg)` opens the exact path. A
  missing file produces the native Python `FileNotFoundError` before model
  validation. Check the path and permissions.
- **Python syntax:** the config is executed as Python. A malformed list,
  unmatched quote, or invalid expression produces a native `SyntaxError`.
  The inspector reports this without executing the file.
- **Deprecated fields:** `initializeClassic0orDelving1` prints
  `ERROR: Deprecated input to the config: [initializeClassic0orDelving1].
  Please update config and use the new corresponding variable convWeightsInit
  ]. Exiting.` (the source punctuation is uneven). `relu0orPrelu1` is similarly
  rejected in favor of `activationFunction`.
- **Missing class count:** the source prints
  `ERROR: Number of classses not specified in the config file, which is
  required.` Add `numberOfOutputClasses`; include background. A foreground
  binary task is normally `2`, not `1`.
- **Missing/invalid channels:** the source prints
  `ERROR: Parameter "numberOfInputChannels" not specified or specified
  smaller than 1.` Set a positive integer and make it agree with every channel
  manifest. A zero value also trips the source assertion
  `Number of input channels should be greater than 0.`
- **Missing normal path:** an absent or empty `numberFMsPerLayerNormal` prints
  `ERROR: The required parameter "numberFMsPerLayerNormal" was either not
  given, or given an empty list.` Supply at least one layer.
- **Normal kernel shape:** an absent kernel list or a list whose length does
  not equal normal depth prints
  `ERROR: The required parameter "kernelDimPerLayerNormal" was not provided,
  or provided incorrectly.` Use one 3-vector per layer. The source explicitly
  warns that kernels should be odd; even kernels are not thoroughly tested.

## Receptive-field and segment failures

The source helper starts at `[1,1,1]` and adds `kernel[d]-1` for every normal
layer. If any configured segment dimension is below the RF, the source first
prints from `check_rec_field_vs_inp_dims`:

```
ERROR: [in function check_rec_field_vs_inp_dims()] : The segment-size (input)
should be at least as big as the receptive field of the model! This was not
found to hold!
```

Then `ModelParameters.errorSegmDimensionsSmallerThanReceptiveF` reports the
network RF, the `train`/`val`/`test` role, and the smaller segment before
exiting. Increase that dimension or reduce kernel/layer depth. Do not use a
validation default smaller than the normal RF. Also check the full model RF
when FC kernels use `VALID`; the source guard itself only checks the normal
path, so a later FC shrink can still produce an unexpectedly small/empty
prediction volume.

For normal depth 3 with `[3,3,3]` kernels, RF is `[7,7,7]`; `[6,7,7]` is
invalid. With all `MIRROR`/`ZERO` padding, spatial dimensions are generally
preserved by the layer geometry, but RF still describes the context consumed
by border handling.

## Subsampled-path failures

When `useSubsampledPathway = True`:

- A flat FM list is interpreted as one subsampled path. Nested FM lists must
  all have the same length; otherwise the source prints
  `ERROR: The parameter "numberFMsPerLayerSubsampled" has been given as a list
  of sublists of integers... currently this functionality requires that same
  number of layers is used in both pathways.`
- If the subsampled kernel list is omitted, it mirrors normal kernels only when
  the subsampled depth equals normal depth. Otherwise the source asks for
  `kernelDimPerLayerSubsampled` and exits.
- If supplied, the subsampled kernel list must contain one 3-vector per shared
  subsampled layer. A malformed list prints
  `ERROR: The parameter "kernelDimPerLayerSubsampled" was not provided, or
  provided incorrectly.`
- A supplied subsampled RF different from the normal RF exits with the source
  message beginning `ERROR: The receptive field of the normal pathway was
  calculated ... Because of limitations in current version, the two pathways
  must have the save size of receptive field.` The typo `save` and the odd
  numeric text are source behavior. Change kernels/depth or omit the
  subsampled FM/kernel overrides to mirror normal.
- A factor not shaped as a 3-vector prints a source error beginning
  `ERROR: The parameter "subsample_factors" must have 3 entries...`; the
  message uses the old name `subsample_factors`, while the current config field
  is `subsampleFactor`. An even factor only emits a warning from
  `subsample_factor_is_even`; use positive odd factors such as `[3,3,3]`.
- Multiple factors create multiple paths. The source may copy the last FM list
  to missing paths, but extra FM lists beyond the number of factors are not a
  useful way to create paths. Keep the counts explicit and equal.

The normal and low-resolution outputs are concatenated after low-resolution
repeat-upsampling and clipping. If padding or kernels cause incompatible
output shapes, model construction may fail later with a TensorFlow shape error;
matching kernels, RF, layer count, and padding across paths avoids this class
of failure.

## FC, list alignment, and residual failures

- The FC path always includes the classifier. If hidden FMs have length `H`,
  `kernelDimPerLayerFC` must have `H+1` entries. The source assertion is:

  `Need one Kernel-Dimensions per layer of FC path, equal to length of
  number-of-FMs-in-FC +1 (for classif layer)`

  The same `H+1` alignment is required in practice for FC padding and dropout;
  their access is not comprehensively validated and a short list can become an
  `IndexError` during graph construction.
- Normal/subsampled dropout lists should be empty or exactly their path depth;
  FC dropout should be empty/default or exactly hidden + classifier depth.
  Rates are interpreted as drop probabilities; `0.0` means no dropout and
  `1.0` drops all inputs.
- A residual list containing `1` prints
  `ERROR: The parameter "layersWithResidualConn" for the [...] pathway was
  specified to include the number 1` and exits. Remove it. Out-of-range or
  duplicate entries are not cleanly rejected by the source; treat them as
  authoring errors rather than relying on them being ignored.
- A residual addition crops the earlier tensor centrally and pads/truncates
  feature maps. It cannot repair arbitrary spatial expansion. After changing
  `VALID` kernels or deleting layers, inspect every residual point.

## Activations, initialization, and lower-rank edge cases

- Invalid `convWeightsInit[0]` prints
  `ERROR: Parameter "convWeightsInit" has been given invalid value.` Use
  `['normal', std]` or `['fanIn', scale]`.
- Invalid activation prints a source error referring to `activ_function` even
  though the current field is `activationFunction`. Accepted values are
  `linear`, `relu`, `prelu`, `elu`, and `selu`. `selu` passes the parser but
  `SeluLayer.apply` raises `NotImplementedError` in this release; use another
  activation unless this is explicitly being fixed and tested.
- Lower-rank layers are split into x/y/z subfilters. Each output branch gets
  roughly one third of the requested maps, so an output width below 3 is not a
  safe lower-rank choice even though the parser does not reject it. Keep
  selected lower-rank layers at least 3 output FMs and validate the resulting
  graph.
- The low-rank layer's dimension helper references the ordinary convolution
  attribute `self._w`, while low-rank construction creates `self._w_x`,
  `self._w_y`, and `self._w_z`. This source inconsistency can surface as an
  `AttributeError` when dimension calculations are requested after selecting a
  lower-rank layer. Treat lower-rank support as conditional in this version;
  do not use it as the first memory-reduction change.

## Checkpoint and memory symptoms

A checkpoint is architecture-specific. Restore failures or implausible output
shapes after changing class count, channel count, path count/factors, FM
widths, kernels, padding, activation, BN setting, or FC depth usually mean
the model config no longer matches the checkpoint. Start a new model or use
the exact original architecture; do not solve a shape mismatch by changing
only the label count.

If a model exhausts GPU memory, first reduce inference segment size (while
keeping it at least the required geometry), then reduce late-layer FMs or FC
hidden widths, remove a subsampled path, or use a tested smaller architecture.
Training segment size affects sampled context/distribution as well as memory;
changing it can change behavior. Lower-rank convolutions may lower parameter
cost but have the edge cases above. This reference does not cover optimizer,
training session, or data-list validation.
