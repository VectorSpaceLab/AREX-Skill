# Model inference workflows

## 1. Choose a bounded model before a forward call

Use this order for a new request:

1. Decide whether the request is a tensor contract check, reduced coordinate
   sampling, loss diagnosis, confidence inspection, or model selection.
2. Obtain one representative input from the input-representation workflow and
   record `b`, token count `n`, padded atom count `m`, MSA rows `s`, template rows
   `t`, feature widths, and device. If the request starts with an input object,
   use `forward_with_alphafold3_inputs` instead of manually rebuilding fields.
3. Set required constructor widths from the produced tensors. For a reduced
   model, reduce internal dimensions and depths together, set
   `diffusion_num_augmentations=1`, `num_rollout_steps=1`, and use one or two
   sampling steps. Keep `atoms_per_window` no larger than the chosen atom
   budget, while preserving the desired local-window shape.
4. Disable PLM/NLM, optional constraints, and production data acquisition until
   the base path works. Add them one at a time.
5. Run the signature smoke first. Run a tiny forward only after all tensors are
   finite, same-device, and shape-checked.

Do not use the package constructor defaults as an implicit benchmark. Pairwise
attention and diffusion memory grow rapidly with token/atom count, and the
production configuration is not designed for a laptop smoke test.

## 2. Loss-versus-coordinate diagnosis

A common intentional design is that the same `forward` method serves training
and inference. Reproduce and diagnose it without a large model:

- With `atom_pos` or labels present and `return_loss=None`, expect a scalar loss
  or `(loss, LossBreakdown)` when requested.
- With the same tensors but `return_loss=False`, expect coordinates. This is the
  explicit way to sample while labels are attached for comparison.
- With no labels and `return_loss=True`, expect a differentiable zero (and an
  all-zero breakdown if requested), not a learned loss.
- With no labels and `return_loss=False`, expect coordinates; set
  `num_sample_steps=2` or another bounded value for diagnosis; a one-step EDM schedule is degenerate in this implementation.

If a user says “the model returned a loss instead of coordinates,” first inspect
`atom_pos`, `distance_labels`, `resolved_labels`, and `return_loss`; do not blame
`num_sample_steps` until mode selection is corrected. If coordinates are
returned with all zeros, inspect inferred atom masks and negative/padded lengths
before interpreting model quality.

## 3. Direct tensor forward checklist

Before calling `model(...)`:

```text
atom_inputs             [b,m,dai]
atompair_inputs         [b,m,m,dapi] OR [b,nw,w,2w,dapi]
molecule_atom_lens     [b,n], nonnegative valid lengths
molecule_ids            [b,n]
additional_molecule_feats [b,n,5]
is_molecule_types       [b,n,5] bool
additional_token_feats  [b,n,33] when supplied
msa                     [b,s,n,32], msa_mask [b,s]
templates               [b,t,n,n,dt], template_mask [b,t]
```

For each example, check `sum(molecule_atom_lens) <= m`; valid
`molecule_atom_indices` and `distogram_atom_indices` point into the flattened
atom axis; and atom offsets were applied after batching. If a pair representation
is dense, the model windows it. If it is already windowed, verify `w` and `2w`
axes instead of passing an arbitrary reshaped tensor.

Use `hard_validate=True` for a diagnostic call when index ordering and frame
indices need strict checking. Use `verbose=True` only while diagnosing; it
reports stages but does not make a production run safe.

## 4. Recycling, sampling, and confidence

`num_recycling_steps` repeats template/MSA/trunk processing while feeding the
recycled single and pair representations back into the next step. It is not the
number of diffusion steps. Start with `1`; increase after memory and latency are
measured.

`num_sample_steps` is passed to the EDM sampler. Fewer steps are appropriate for
shape/device smoke checks, not for quality claims. `return_all_diffused_atom_pos`
exposes the timestep trajectory and increases memory. For a confidence pass,
request `return_confidence_head_logits=True`; for model-selection input, also
request distogram logits. Keep sample coordinates and logits paired by batch and
sample index.

A low-memory confidence-logit plan is:

1. Use one input, one model, no MSA/templates, reduced widths/depths, one
   diffusion augmentation, and two diffusion sampling steps.
2. Run `return_loss=False` under `torch.no_grad()` with one confidence pass.
3. Assert coordinate shape `[1,m,3]`, `plddt.shape == [1,num_plddt_bins,m]`,
   `pde.shape == [1,num_pde_bins,n,n]`, and `resolved.shape == [1,2,m]`.
4. Only after this works, add PAE/frame indices, then distogram logits, then
   multiple samples/models for ranking.

If memory is still tight, reduce `m`, `n`, internal widths, pairformer/deep
module depths, MSA rows, template rows, and diffusion candidates in that order;
checkpointing trades compute for activation memory but does not change the
quadratic asymptotic cost.

## 5. Checkpoint compatibility workflow

For a package-native saved file:

1. Inspect the file's existence and use `map_location='cpu'` first.
2. Try `Alphafold3.init_and_load(file, map_location='cpu')`.
3. Compare the reconstructed model's `dim_atom_inputs`,
   `dim_atompair_inputs`, `dim_template_feats`, `atoms_per_window`, bin counts,
   optional embedding settings, and package version with the intended input.
4. Use `strict=True` as a compatibility audit. If it fails, classify missing
   keys, unexpected keys, changed dimensions, or an incompatible save format;
   do not paper over the failure by silently loading a partially matched model.
5. Move the validated model to the target device and run the tiny contract
   check before a real sample.

For an externally hosted model, pin a revision and filename, use
`local_files_only=True` when proving cache-only behavior, and explicitly decide
whether network access is allowed. `Alphafold3WithHubMixin` does not remove the
need for constructor/configuration compatibility.

## 6. Confidence and model selection workflow

For one sampled structure, use `ComputeConfidenceScore` when pLDDT/pTM/ipTM
are needed. Supply `asym_id` and `has_frame` at token level, and check that PAE
logits are present; a confidence head that returns `pae=None` cannot produce
pTM/ipTM. For a multimer, inspect ipTM and clash/disorder components rather than
ranking from pLDDT alone.

For multiple candidate models, use `ComputeModelSelectionScore` with one
prepared batch and the returned coordinate/logit tuples. It internally obtains
pLDDT, global PDE, and weighted lDDT. Use `return_details=True` to report both
best gPDE and best lDDT indices; they can differ. If unresolved-protein RASA is
requested, provide its chain and residue masks or let the scorer skip RASA with
an explicit warning.

## 7. Architecture-component selection

Use the smallest component that answers the question:

| Question | Component |
|---|---|
| Atom/pair feature projection, pooling, token initialization | `InputFeatureEmbedder` |
| MSA or template contribution | `MSAModule` / `TemplateEmbedder` |
| Recycled trunk representation | `PairformerStack` |
| Coordinate denoising / local atom attention | `DiffusionModule`, `DiffusionTransformer`, or `ElucidatedAtomDiffusion` |
| Distance logits | `DistogramHead` |
| PAE/PDE/pLDDT/resolved logits | `ConfidenceHead` |
| Confidence/ranking without another forward | `ComputeConfidenceScore`, `ComputeRankingScore`, `ComputeModelSelectionScore` |

Component-level synthetic tensors must obey that component's own dimensions;
do not use component success as evidence that a full heterogeneous input is
valid. Route feature construction and biological semantics to sibling skills.
