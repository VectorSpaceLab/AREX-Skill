# Repo Provenance

## Source State

- Repository: ProteinMPNN
- VCS: git
- Branch: `main`
- Commit: `8907e6671bfbfc92303b5f79c4b5e6ce47cdef57`
- Exact tag: none detected
- Working tree state at generation: dirty because the generated `skills/` tree was added
- Remote URL: https://github.com/dauparas/ProteinMPNN
- Package version: not declared; this is a script-style repository without `pyproject.toml`, `setup.py`, or distribution metadata

## Evidence Paths

- `README.md`
- `protein_mpnn_run.py`
- `protein_mpnn_utils.py`
- `helper_scripts/assign_fixed_chains.py`
- `helper_scripts/make_bias_AA.py`
- `helper_scripts/make_bias_per_res_dict.py`
- `helper_scripts/make_fixed_positions_dict.py`
- `helper_scripts/make_pos_neg_tied_positions_dict.py`
- `helper_scripts/make_pssm_input_dict.py`
- `helper_scripts/make_tied_positions_dict.py`
- `helper_scripts/parse_multiple_chains.py`
- `examples/submit_example_1.sh`
- `examples/submit_example_2.sh`
- `examples/submit_example_3.sh`
- `examples/submit_example_3_score_only.sh`
- `examples/submit_example_3_score_only_from_fasta.sh`
- `examples/submit_example_4.sh`
- `examples/submit_example_4_non_fixed.sh`
- `examples/submit_example_5.sh`
- `examples/submit_example_6.sh`
- `examples/submit_example_7.sh`
- `examples/submit_example_8.sh`
- `examples/submit_example_pssm.sh`
- `inputs/PDB_monomers/pdbs/5L33.pdb`
- `inputs/PDB_monomers/pdbs/6MRR.pdb`
- `inputs/PDB_complexes/pdbs/3HTN.pdb`
- `inputs/PDB_complexes/pdbs/4YOW.pdb`
- `inputs/PDB_homooligomers/pdbs/4GYT.pdb`
- `inputs/PDB_homooligomers/pdbs/6EHB.pdb`
- `inputs/PSSM_inputs/3HTN.npz`
- `inputs/PSSM_inputs/4YOW.npz`
- `outputs/example_*_outputs/` as expected-output evidence only
- `vanilla_model_weights/`
- `soluble_model_weights/`
- `ca_model_weights/`
- `colab_notebooks/README.md`
- `colab_notebooks/*.ipynb` as reference-only notebook evidence
- `training/README.md`
- `training/training.py`
- `training/model_utils.py`
- `training/utils.py`
- `training/parse_cif_noX.py`
- `training/submit_exp_020.sh`
- `training/test_inference.sh`
- `training/exp_020/log.txt` as expected-output evidence only

## Live Inspection Facts

- Import checks verified `protein_mpnn_utils`, `protein_mpnn_run`, `numpy`, and `torch` in a private inspection environment.
- `python protein_mpnn_run.py --help` and representative helper `--help` commands were verified.
- A PDB parsing smoke check parsed `inputs/PDB_monomers/pdbs/5L33.pdb` and found chain `A`.
- GPU availability was not required for content extraction; full design/training examples remain classified as GPU or expensive unless explicitly selected by a verifier.

## Refresh Guidance

Refresh this skill if any of these change:

- `protein_mpnn_run.py` CLI flags or output folder behavior.
- Helper script arguments or JSON schema expectations.
- Model weight folder naming or default model names.
- Training data layout, `training.py` flags, or custom checkpoint loading behavior.
- README example workflows, notebooks, or expected output formats.
