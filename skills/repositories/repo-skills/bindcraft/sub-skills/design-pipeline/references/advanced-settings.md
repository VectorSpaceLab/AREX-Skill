# Advanced settings and preset selection

The repository's advanced presets all have the same 64-key schema. They are
small configuration JSONs, not interchangeable guarantees. Start with a
preset, copy it into a campaign-owned file, and change only settings justified
by the target and observed failures. The following groups are the operational
surface.

## Key groups

| Group | Keys and effect |
| --- | --- |
| Sequence/model choice | `omit_AAs`, `force_reject_AA`, `use_multimer_design`, `design_algorithm`, `sample_models`. `omit_AAs` is passed to design/MPNN; it is not an absolute guarantee unless `force_reject_AA` also rejects sampled sequences. |
| Template and initialization | `rm_template_seq_design`, `rm_template_seq_predict`, `rm_template_sc_design`, `rm_template_sc_predict`, `predict_initial_guess`, `predict_bigbang`. Masking increases target flexibility. Initial guesses can help difficult targets but can bias validation; `predict_bigbang` is intended for large target-plus-binder systems (the README calls out more than about 600 residues). |
| Iteration schedule | `soft_iterations`, `temporary_iterations`, `hard_iterations`, `greedy_iterations`, `greedy_percentage`. More iterations and more mutations increase time and often memory pressure. `greedy_percentage` is converted to a length-derived mutation count. |
| Design losses | `weights_plddt`, `weights_pae_intra`, `weights_pae_inter`, `weights_con_intra`, `weights_con_inter`, `intra_contact_distance`, `inter_contact_distance`, `intra_contact_number`, `inter_contact_number`, `weights_helicity`, `random_helicity`. Larger weights emphasize that loss; the sign and scale are meaningful, so do not normalize them casually. |
| Optional losses | `use_i_ptm_loss`/`weights_iptm`, `use_rg_loss`/`weights_rg`, and `use_termini_distance_loss`/`weights_termini_loss`. These change the optimization objective rather than post hoc filters. |
| MPNN | `enable_mpnn`, `mpnn_fix_interface`, `num_seqs`, `max_mpnn_sequences`, `sampling_temp`, `backbone_noise`, `model_path`, `mpnn_weights`, `save_mpnn_fasta`. More sequences multiply AF2 complex/monomer validation work. |
| AF2 validation and beta handling | `num_recycles_design`, `num_recycles_validation`, `optimise_beta`, `optimise_beta_extra_soft`, `optimise_beta_extra_temp`, `optimise_beta_recycles_design`, `optimise_beta_recycles_valid`. Recycles increase compute; beta optimization changes settings for detected beta-rich trajectories. |
| Storage and campaign | `save_design_animations`, `save_design_trajectory_plots`, `remove_unrelaxed_trajectory`, `remove_unrelaxed_complex`, `remove_binder_monomer`, `zip_animations`, `zip_plots`, `save_trajectory_pickle`, `max_trajectories`, `enable_rejection_check`, `acceptance_rate`, `start_monitoring`. Pickles and animations can be large; removal flags trade debugging detail for disk. |
| External paths | `af_params_dir`, `dssp_path`, `dalphaball_path`. These must resolve in the launch environment. Do not copy a path from another machine or from a private verification environment. |

`num_recycles_design` controls the hallucination model. Validation recycles
control both complex reprediction and binder-alone prediction. AF2 model
selection is also affected by `use_multimer_design`; see
[pipeline](pipeline.md). Increasing either setting is not automatically better
for every target and can make OOM or wall-time failures more likely.

## Preset families

The 20 checked-in advanced files are a naming matrix rather than 20 unrelated
algorithms:

- `default_4stage_multimer` is the general 4stage multimer starting point. Its
  representative values are 75 soft, 45 temporary, 5 hard, and 15 greedy
  iterations; 1 design recycle and 3 validation recycles; MPNN enabled with
  20 sequences and a maximum of 2 accepted per trajectory; soluble MPNN
  weights; beta optimization enabled; rejection monitoring starts at 600
  trajectories with a 0.01 acceptance target.
- `*_flexible` masks target template sequence during design and prediction.
  The default flexible variants start rejection monitoring earlier (300); do
  not mistake this for a universally safer setting.
- `*_hardtarget` enables `predict_initial_guess`. It is intended for difficult
  target prediction and can inherit the trajectory's binder template; inspect
  the resulting bias rather than treating it as an accuracy correction.
- `*_mpnn` sets `mpnn_fix_interface` false, allowing MPNN to redesign the
  interface. The default MPNN variants also monitor from 300 trajectories.
  `_mpnn_flexible_hardtarget` combines all three modifiers.
- `betasheet_4stage_multimer*` keeps the 4stage multimer route but raises the
  pLDDT design weight, changes contact weights, and applies a negative
  helicity bias in the checked-in presets. Flexible, hard-target, and MPNN
  suffixes have the same meanings as above.
- `peptide_3stage_multimer*` selects `3stage`, uses a more helical helicity
  setting, `greedy_percentage: 5`, no beta optimization, and peptide-oriented
  MPNN/acceptance values. The `_mpnn` peptide variants use 50 sequences rather
  than 10 and allow interface redesign. These presets are not general-purpose
  replacements for globular binder presets.

The Colab UI composes these tags from design protocol, prediction protocol,
interface protocol, and template protocol. Reproduce that selection manually
with the filename matrix; do not rely on notebook-only paths.

## Resource tuning rules

1. Trim the target to the smallest biologically justified region before
   increasing settings. Target length is a major AF2 memory/time driver.
2. Reduce binder length range, recycles, iterations, validation model count
   (through the model-role setting), or `num_seqs` when memory or wall time is
   the bottleneck, but record the change because it changes the experiment.
3. `predict_bigbang` and flexible template settings may help a specific hard
   target while increasing memory or bias. Enable one change at a time.
4. Keep `sample_models: true` unless there is a documented reason to disable
   model sampling; the README recommends sampling to reduce overfitting.
5. Set `max_trajectories` for a bounded pilot or scheduler allocation. A pilot
   is a resource check, not an acceptance claim. For a production campaign,
   use a target number of final designs and monitor disk and acceptance.
6. Keep cleanup flags consistent with the recovery plan. Removing unrelaxed
   PDBs or binder monomers saves space but removes useful debugging evidence;
   pickles are optional and potentially very large.

AF2 weights, MPNN weights, PyRosetta, DSSP, and DAlphaBall remain external
runtime dependencies. A valid JSON schema or successful command construction
does not prove that the selected resources or target will work.
