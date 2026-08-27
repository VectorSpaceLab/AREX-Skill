# Model inference troubleshooting

## Constructor and feature-width failures

| Symptom | Likely cause | Recovery |
|---|---|---|
| `expected ... for atom_inputs feature dimension` | The final atom feature width differs from `dim_atom_inputs`. | Read the adapter's actual last dimension and construct the model with that width; do not pad arbitrary channels without documenting their meaning. |
| The pair feature assertion fails | `atompair_inputs.shape[-1]` differs from `dim_atompair_inputs`, or an integer bond embedding was confused with continuous pair features. | Fix the constructor/input pair; for pre-windowed data also verify `[nw,w,2w]`. |
| Template linear/projection shape error | Template last dimension differs from `dim_template_feats`. | Omit templates for a no-template path, or regenerate templates with the configured feature width. Do not substitute zeros with the wrong width. |
| `num_dist_bins` assertion | `num_dist_bins != len(distance_bins)`. | Pass matching values; likewise keep PAE/PDE bin count expectations consistent with logits and labels. |
| assertion about atom/atompair IDs | IDs were supplied without enabling the corresponding embedding table, or enabled but omitted. | Either remove the IDs and set the embedding count to `None`, or configure the count and pass correctly ranged IDs. |
| modification/constraint assertion | `is_molecule_mod` or `token_constraints` is present without the matching constructor option. | Disable the optional feature for the baseline path, or configure its exact width and semantics. |

## Shape, index, and mask failures

- `molecule_atom_lens` is token-level `[b,n]`; its valid sums determine the
  atom mask. A padded slot may be negative, but a real token must not have an
  accidental negative length. Check `sum(lengths) <= m` for every batch item.
- `molecule_atom_indices` and `distogram_atom_indices` are flattened atom
  positions, not token IDs. After collation, apply each example's atom offset;
  an un-offset second example silently selects atoms from the first example.
- `atom_indices_for_frame` is `[b,n,3]` and must point to valid atoms for the
  corresponding token. Set its validity mask for unresolved/missing frames.
  Use `hard_validate=True` to catch non-ascending frame/representative indices.
- `msa_mask` is `[b,s]`, `template_mask` is `[b,t]`, and token masks are `[b,n]`.
  Do not pass an atom mask as a token mask. MSA/template features must share the
  same `n` as the token axis, even when their row count is zero/omitted.
- `missing_atom_mask=True` means missing. The model builds a valid atom mask
  from lengths and zeros invalid sampled coordinates. If every atom in a token
  is missing, confidence/ranking frame and representative indices may be
  invalid and must be masked.
- Mixed CPU/CUDA tensors commonly fail inside `cdist`, gather, or embeddings.
  Move the model and every tensor in the forward dictionary to one device; keep
  IDs/masks integer/boolean. `forward_with_alphafold3_inputs` moves its collated
  dictionary to the model device, while direct `forward` does not repair a mixed
  dictionary.

## Loss, sampling, and step confusion

If a call returns a scalar when coordinates were expected, inspect mode in this
order:

1. Was `return_loss` omitted? Coordinates/labels cause automatic loss mode.
2. Was `atom_pos` supplied only as a comparison target? Set
   `return_loss=False` to force sampling.
3. Was `return_loss=True` used without labels? A zero loss is an intentional
   control-path result, not a sampled structure.
4. Is the caller confusing `num_recycling_steps` with `num_sample_steps`?
   Recycling changes trunk passes; sample steps change EDM denoising steps.

`num_rollout_steps` is used by training confidence-label rollouts and is not a
replacement for inference `num_sample_steps`. Keep all three explicit when a
training-like diagnostic mixes both paths.

## Confidence and ranking failures

- `ConfidenceHeadLogits.pae` can be `None`; pTM/ipTM require PAE logits. Request
  confidence logits from a sampling call and verify `return_pae_logits` on any
  direct head call.
- pLDDT logits are channel-first `[b,plddt,m]`, while the converted pLDDT score
  is `[b,m]`. PDE/PAE logits are `[b,bins,n,n]`. A transpose mistake can look
  like a valid tensor but breaks bin conversion.
- Confidence logits and coordinates must use the same sample. Do not rank a
  coordinate from one model with logits from another.
- Full-complex ranking needs atom positions/masks and token molecule-type flags;
  single-chain pTM needs only confidence logits plus `asym_id`/`has_frame`.
  Interface ranking needs valid chain tuples matching `asym_id` values.
- A clash penalty of 100 is intentional in `ComputeRankingScore`; it can
  dominate a score. Inspect `return_confidence_score=True` to separate pTM,
  ipTM, disorder, and clash instead of treating the aggregate as calibrated.
- `ComputeModelSelectionScore` may choose different candidates for gPDE and
  lDDT. Report both indices with `return_details=True` and keep batch/sample
  ordering stable.

## Checkpoints and hub loading

| Symptom | Recovery |
|---|---|
| File missing or rejected as a directory | Confirm a regular package-native checkpoint file and use its exact filename. Do not create a replacement by guessing. |
| `KeyError` for `model`, init args, or state dict | The file is not in the package's saved format. Use the producer's documented loader or obtain a compatible package-native export. |
| Missing/unexpected keys or size mismatch | Compare constructor dimensions, bin counts, optional embedding tables, and package version. Retry with `strict=True` for an audit; do not claim compatibility after partial load. |
| CUDA OOM during load or first forward | Load with `map_location='cpu'`, validate a tiny input, then move to CUDA; reduce batch/atoms/depth, enable checkpoint flags, or use a smaller candidate. |
| Device mismatch after successful CPU load | Move model and all input tensors together; a checkpoint's map location does not move later input tensors. |
| Hub call tries to access network | Use a local file or `local_files_only=True`; pin revision/cache/model filename when network is explicitly allowed. |
| Hub load raises an unexpected `strict` keyword error | This release's hub override forwards `strict` to `init_and_load`, while the public loader signature does not accept it. Use direct package-native `init_and_load` for a local saved file, or record hub loading as a release compatibility block. |
| Hub model cannot reconstruct | Verify saved init arguments and package version; `model_kwargs` does not make arbitrary state dictionaries compatible. |

## Optional PLM/NLM failures

PLM/NLM constructors can fail before the first model forward because their
optional Python packages or pretrained caches are absent. ESM2, ProstT5, and
RiNALMo wrappers may fetch weights through their respective model hubs. Recover
without downloads by disabling the relevant constructor option and using normal
MSA/token features. If the feature is required, install the approved optional
dependency and make the weight/cache policy explicit before retrying.

Also check that:

- protein IDs are masked to the PLM's accepted protein range and non-protein
  tokens are masked;
- nucleotide IDs are masked to the RNA/DNA ranges expected by the NLM;
- wrapper output sequence length equals `n` and the model's projected embedding
  width matches `dim_single`;
- optional wrappers remain frozen/no-gradient and are rebuilt when loading a
  checkpoint, since they are excluded from the base model state dictionary.

## Memory and production limits

The trunk has token-pair tensors and the atom/diffusion path has atom-pair
attention. Memory rises with `n²`, `m²`, MSA/template rows, recycling passes,
and diffusion candidate/step counts. The default architecture and augmentation
counts are production-oriented and should not be used as a diagnostic default.

Reduce in this order: input atoms/tokens, batch size, MSA/template rows,
internal widths, module depths/heads, diffusion candidates, recycling steps,
and sample steps. Enable activation checkpoint flags when recomputation is
acceptable. CUDA availability alone does not prove that a production-sized
model fits. A reduced CPU/CUDA smoke proves only import, construction, and
shape/device plumbing.

Do not “fix” OOM by silently moving part of a forward dictionary to CPU: gather,
`cdist`, attention, and diffusion operations require coherent device placement.
Stop and report the reduced budget and the first failing stage when the target
workload remains too large.
