# OmegaFold Model Architecture Notes

OmegaFold is release inference code for high-resolution de novo protein structure prediction from a primary sequence. The public programmatic path is `make_config(model_idx) -> OmegaFold(cfg) -> model.forward(prepared_inputs, fwd_cfg=...)`.

## Module Map

| Component | Location in model | Role during inference |
| --- | --- | --- |
| OmegaPLM | `model.omega_plm` | Protein language model that embeds pseudo-MSA token inputs. |
| PLM projectors | `plm_node_embedder`, `plm_edge_embedder` | Project raw PLM node/edge features into OmegaFold widths. |
| Input edge embedder | `input_embedder` | Adds sequence/relative-position features to pair representation. |
| Recycle embedder | `recycle_embedder` | Injects previous cycle node, edge, atom14 coordinate, and frame information. |
| GeoFormer | `omega_fold_cycle.geoformer` | Updates node and pair representations with geometry-aware blocks. |
| Structure module | `omega_fold_cycle.structure_module` | Decodes updated representations into atom14 coordinates and frames. |
| Confidence head | `omega_fold_cycle.confidence_head` | Produces per-residue pLDDT-like confidence values. |

`OmegaFold.forward` loops over prepared cycle dictionaries. For each cycle it embeds the pseudo-MSA, recycles the previous state, runs a GeoFormer/structure/confidence cycle, computes `confidence_overall`, and either keeps the best-confidence result or the last result depending on `predict_with_confidence`.

## Config Choices That Matter

`make_config(1)` and `make_config(2)` share most architecture settings. The exposed difference is:

| Config | `struct_embedder` | Weight family |
| --- | --- | --- |
| `make_config(1)` | `False` | Model 1 weights, typically `release1.pt`. |
| `make_config(2)` | `True` | Model 2 weights, typically `release2.pt`. |

Agents should keep config id and weights aligned. A config/weight mismatch usually appears as `load_state_dict` missing or unexpected keys, not as a clear semantic error.

Important memory/performance fields:

| Field | Meaning |
| --- | --- |
| `geo_num_blocks=50` | Large geometry stack; long sequences need substantial memory. |
| `node_dim=256`, `edge_dim=128` | Main tensor widths; pair tensors scale roughly with residue count squared. |
| `struct.*` | Structure module and confidence-head dimensions; usually do not edit. |
| `fwd_cfg.subbatch_size` | Runtime sharding knob, not a static config field. Lower values reduce memory and increase runtime. |
| `fwd_cfg.num_recycle` | Runtime recycle/cycle count that should match prepared FASTA cycle data. |

## Forward Data Flow

1. `pipeline.fasta2inputs` prepares a list of cycle dictionaries with tokenized `p_msa` and `p_msa_mask` tensors.
2. `OmegaFold.forward` reads the primary sequence from the first cycle's first pseudo-MSA row.
3. `create_initial_prev_dict(num_res)` creates zeroed recycled features and default frames.
4. `deep_sequence_embed(p_msa, p_msa_mask, fwd_cfg)` runs OmegaPLM, projects node/edge features, and applies edge embedding.
5. `recycle_embedder` combines current features with the previous cycle's node/edge/coordinate/frame state.
6. `omega_fold_cycle` runs GeoFormer, the structure module, and the confidence head.
7. `confidence.get_all_confidence` computes a scalar confidence score from per-residue confidence and CA coordinates.
8. The selected result exposes atom14 coordinates and confidence for downstream PDB writing.

## Practical API Guidance

- Treat `OmegaFold` as an inference module. Keep it in `eval()` mode and wrap prediction in `torch.no_grad()`.
- Do not change architecture fields unless you also control compatible weights.
- Prefer lowering `fwd_cfg.subbatch_size` before changing model internals when memory is the issue.
- Keep input tensors and the model on the same device. `pipeline.fasta2inputs(..., device=device)` can move prepared tensors for you.
- Use the CLI sub-skill when the user only wants a PDB from a FASTA; use this sub-skill when the user needs Python integration, model inspection, or custom orchestration.
