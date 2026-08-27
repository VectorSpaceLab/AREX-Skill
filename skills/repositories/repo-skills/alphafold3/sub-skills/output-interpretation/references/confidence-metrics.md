# AlphaFold 3 Confidence Metrics

AlphaFold 3 writes two confidence JSON types for each prediction:

- `*_summary_confidences.json` contains scalar, per-chain, and chain-pair summaries used for ranking and quick interpretation.
- `*_confidences.json` contains full arrays, including per-atom or per-token values, for detailed analysis and plotting.

Use summary files first for triage and ranking, then full files when a user needs token-level PAE, per-atom pLDDT, contact probabilities, or chain IDs.

## Ranking Score

`ranking_score` is the primary score for choosing the best full-complex prediction. Higher is better. It combines global/interface confidence with penalties and bonuses:

```text
0.8 * ipTM + 0.2 * pTM + 0.5 * fraction_disordered - 100 * has_clash
```

Use `ranking_scores.csv` to compare all seed/sample predictions. The top-level `<job>_model.cif`, `<job>_confidences.json`, and `<job>_summary_confidences.json` correspond to the highest row in this CSV.

Important cautions:

- `ranking_score` is for ranking alternative predictions of the same job, not for absolute biological truth.
- A `has_clash` value can dominate the score because it applies a large penalty.
- If the user cares about one chain or interface, a chain-specific or chain-pair-specific metric can be more relevant than full-complex `ranking_score`.

## Summary Metrics

Common keys in summary confidence JSON include:

- `ptm`: predicted TM-score for the full structure, range 0-1. Values above about 0.5 suggest the overall fold or complex topology may be plausible.
- `iptm`: interface predicted TM-score across interfaces, range 0-1. Values above about 0.8 indicate confident interfaces; below about 0.6 often suggests a failed interface prediction; 0.6-0.8 is a gray zone.
- `fraction_disordered`: fraction of the predicted structure considered disordered.
- `has_clash`: whether the prediction has severe atom clashes. Treat a clashing top-ranked model cautiously even if other metrics look good.
- `chain_ptm`: per-chain pTM values for evaluating individual chains.
- `chain_iptm`: per-chain average interface confidence with the rest of the complex.
- `chain_pair_iptm`: matrix of chain-pair interface confidence. Off-diagonal values apply to interfaces; diagonal values represent per-chain pTM.
- `chain_pair_pae_min`: matrix of minimum predicted aligned error across each chain-pair block. Low off-diagonal values can support a predicted interaction.

For very small chains or short structures, TM-derived metrics can be strict or compressed toward low values; inspect PAE and pLDDT before concluding that every local feature failed.

## Full Confidence Arrays

Full confidence JSON files can be large. Common keys include:

- `atom_plddts`: per-atom pLDDT values on a 0-100 scale.
- `pae`: predicted aligned error matrix with shape `[num_tokens, num_tokens]`; higher values indicate lower confidence in relative placement.
- `contact_probs`: predicted contact probabilities between token pairs, commonly interpreted as contact within 8 Å between representative atoms.
- `token_chain_ids`: chain IDs for each token in token-level arrays.
- `atom_chain_ids`: chain IDs for each atom in atom-level arrays.

Use full arrays when a user asks for residue/token-level confidence, interface heatmaps, chain block extraction, or contact-supported interpretation.

## pLDDT

pLDDT estimates local structural confidence on a 0-100 scale:

- 90-100: high local confidence.
- 70-90: medium confidence.
- 50-70: low confidence.
- 0-50: often disordered or unreliable local geometry.

AlphaFold 3 reports pLDDT per atom rather than only per residue. For ligands and modified residues, the value reflects local confidence relative to polymer context, so do not over-interpret ligand internal geometry from pLDDT alone.

## PAE

PAE estimates the expected error in the position/orientation of token `j` when the prediction is aligned using token `i`. Lower is better. Use PAE to judge domain placement, chain docking, and whether two regions have a stable relative arrangement.

For interface interpretation:

- Low cross-chain PAE supports a confident relative placement.
- High cross-chain PAE with high local pLDDT often means individual chains may be folded but not confidently docked.
- Inspect the chain-pair PAE block instead of only whole-matrix averages when the user cares about a specific pair.

## Chain and Chain-Pair Ranking

For full-complex ranking, use `ranking_score` from `ranking_scores.csv`. For targeted questions:

- Best individual chain fold: compare `chain_ptm` for the chain of interest.
- Best placement of a chain against the rest of the complex: compare `chain_iptm` for that chain.
- Best known interface between two chains: compare off-diagonal `chain_pair_iptm[i][j]` and corroborate with `chain_pair_pae_min[i][j]`.
- Possible binder/non-binder distinction: low `chain_pair_pae_min` can support an interaction, but should be interpreted with biological context and controls.

## Antibody-Antigen Interface Guidance

For antibody-antigen use cases, the relevant ranking metric is often not the full-complex `ranking_score`. If the user asks which sample best predicts a specific antibody-antigen interface:

1. Map antibody and antigen chains to their indices in the summary confidence matrices.
2. Compare off-diagonal `chain_pair_iptm` for the antibody-antigen chain pair across samples.
3. Use `chain_pair_pae_min` for the same pair as supporting evidence; lower values suggest a more confident relative placement.
4. Check `has_clash`, local pLDDT around the interface, and the full PAE block before promoting a sample with a high interface score but obvious artifacts.

Antibody-antigen benchmark metadata in the repository documents how paper-level analyses grouped antibody-antigen interfaces into clusters, but ordinary output interpretation still depends on the chain-pair metrics in the generated summary confidence files.
