# Generative Model Troubleshooting

Use this reference when DGMG or JTVAE planning, input validation, checkpoint loading, reconstruction, or generation fails.

## Import and Install Failures

Symptoms:

- `ModuleNotFoundError: No module named 'dgllife'`, `dgl`, `torch`, `rdkit`, `scipy`, or `numpy`.
- DGL backend or PyTorch import errors happen before model code runs.
- RDKit parses molecules in one environment but fails in another.

Fixes:

- Confirm the active Python environment can import `dgllife`, `dgl`, `torch`, `rdkit`, `scipy`, and `numpy` before using generative APIs.
- Use a CPU smoke check before GPU or multiprocess training. DGMG source examples emphasize CPU multiprocessing; JTVAE can use GPU but does not require it for tiny validation.
- Keep DGL and PyTorch versions compatible. If CUDA is involved, confirm DGL, PyTorch, driver, and CUDA runtime compatibility before training.
- Treat RDKit as version-sensitive for kekulization, stereochemistry, sanitization, and MolTree decomposition. Modern RDKit builds may raise kekulization errors for JTVAE vocab/MolTree inputs that older example environments accepted; validate the user's SMILES/vocab with the bundled helper and only pin or downgrade RDKit when the user explicitly accepts the environment risk.
- Do not place local environment paths or activation commands in public runtime skill content.

## Optional Dependency Failures

Symptoms:

- DGMG monitoring fails because `tensorboardX` or TensorFlow is missing.
- DGMG evaluation scripts fail around synthetic accessibility scoring or plotting/notebook utilities.
- Pretrained loading or default JTVAE vocab/dataset construction tries to access network or cache paths unexpectedly.

Fixes:

- Treat TensorBoard, plotting, notebooks, SA scoring, and pretrained downloads as optional. They are not needed for input validation or constructor smoke checks.
- Ask before running workflows that call `load_pretrained`, `JTVAEVocab()` with no file, or `JTVAEZINC`, because they may download checkpoints or datasets.
- For offline use, require explicit local SMILES files, local vocabulary/training file, and local checkpoints.

## SMILES and Data-Config Failures

Symptoms:

- RDKit reports parse errors or kekulization failures.
- DGMG custom preprocessing silently drops many molecules.
- JTVAE dataset construction fails before the first training step.
- The user passes CSV files, SDF files, or labels to a workflow expecting one SMILES token per line.

Fixes:

- Convert inputs to one-SMILES-per-line text files before using DGMG/JTVAE example-style loaders.
- Run `scripts/validate_generative_inputs.py --smiles-file FILE --max-rows N` on a small sample.
- For CSV parsing, label handling, or graph featurizer debugging, route to the molecule-data-prep sub-skill before returning here.
- Remember DGL-LifeSci generative loaders use only `line.split()[0]`; identifiers and labels after whitespace are ignored.
- Investigate large molecule, unusual valence, formal charge, protonation, and stereochemistry patterns when many molecules are filtered.

## DGMG-Specific Failures

Symptoms:

- `IndexError`, invalid atom type, or invalid bond type during teacher forcing.
- Loaded checkpoint has output-head shape mismatches.
- Generated molecules are invalid, duplicated, or not novel.
- Generation appears to run forever.

Fixes:

- Keep `atom_types` and `bond_types` identical between preprocessing, training, evaluation, and checkpoint loading.
- Remember stop actions are encoded as `len(atom_types)` for add-node decisions and `len(bond_types)` for add-edge decisions.
- Use `rdkit_mol=True` when a generated SMILES string is required; `rdkit_mol=False` avoids RDKit molecule maintenance and may return `None`.
- Bound generation with `max_num_steps`; the example evaluation default is 400 steps.
- Reduce `num_samples`, `num_processes`, and generation timeout for smoke checks.
- Validate generated SMILES and compute validity/uniqueness/novelty after generation; do not assume every sample is valid.
- If custom data produces poor validity, revisit standardization and DGMG reproducibility filtering rather than only tuning model size.

## JTVAE Vocabulary Mismatch

Symptoms:

- `KeyError` from `JTVAEVocab.get_index(...)` while constructing `JTVAEDataset`.
- `RuntimeError` shape mismatch for embedding or decoder weights when loading a checkpoint.
- Reconstruction works for training molecules but fails for a new test file.
- A manually supplied vocabulary has duplicates or invalid fragment strings.

Fixes:

- Build `JTVAEVocab(file_path=train.txt)` from the same training data distribution used by the checkpoint, or preserve the exact vocabulary file/order used during training.
- Validate coverage with `python scripts/validate_generative_inputs.py --smiles-file test.txt --vocab-file vocab.txt --derive-jtvae-vocab`.
- Treat vocabulary order as checkpoint state: the same token set in a different order can corrupt embeddings semantically even if tensor shapes match.
- If using the default `JTVAEVocab()`, be aware it may download default ZINC vocabulary data and may not cover custom chemistry.
- When only a user SMILES file is available and no checkpoint exists, plan vocabulary derivation and training; do not promise reconstruction from an untrained model.

## JTVAE Reconstruction and Generation Failures

Symptoms:

- `reconstruct.py` fails because no model checkpoint is supplied and pretrained loading is unavailable.
- `model.reconstruct(...)` or `sample_prior(...)` returns `None`.
- Stereo accuracy is low or stereochemical outputs differ from inputs.
- `JTVAECollator` or batched graph tensors fail on device movement.

Fixes:

- For reconstruction with a local checkpoint, recreate `JTNNVAE(vocab, hidden_size, latent_size, depth, stereo=...)` with matching hyperparameters before `load_state_dict`.
- Keep tree graphs, molecular graphs, stereo candidate graphs, and index tensors on the same device as the model.
- Set `--use-cpu`/CPU mode for debugging, then switch to GPU only after data and checkpoint loading work.
- Treat `None` outputs as invalid generations; filter and report them rather than passing to downstream pipelines.
- For stereo-sensitive tasks, confirm whether `stereo=True` was used at training and whether the input SMILES encode stereochemistry.

## Checkpoint Shape and API Misuse

Symptoms:

- DGMG checkpoint expects different numbers of atom or bond actions.
- JTVAE checkpoint expects different `hidden_size`, `latent_size`, `depth`, or vocabulary size.
- `load_state_dict` reports missing/unexpected keys.
- Constructor receives feature-size arguments copied from property-prediction models.

Fixes:

- Use verified signatures: `DGMG(atom_types, bond_types, node_hidden_size=128, num_prop_rounds=2, dropout=0.2)` and `JTNNVAE(vocab, hidden_size, latent_size, depth, stereo=True)`.
- Do not pass generic GNN feature dimensions such as `in_feats` or `n_tasks` to these generative constructors.
- Inspect checkpoint metadata when available; if metadata is absent, infer only from documented run settings and tensor shapes, then validate with a tiny load test.
- Do not mix DGMG pretrained checkpoints, JTVAE raw state dicts, and property-prediction checkpoints; their save formats differ.

## Long Training, GPU, and Runtime Issues

Symptoms:

- DGMG training takes hours or days, multiprocessing hangs, or CPU is saturated.
- JTVAE DataLoader workers hang around RDKit/DGL objects.
- GPU out-of-memory appears during JTVAE training.
- Full DGMG evaluation with 100k samples exceeds local time limits.

Fixes:

- Treat original DGMG/JTVAE training and evaluation scripts as long-running reference workflows. Do not launch them without explicit user approval, resource bounds, and an output directory.
- For DGMG, reduce `num_processes` to 1 for debugging and verify process-group settings before multi-process runs.
- For JTVAE, reduce `batch_size`, `num_workers`, and hidden sizes for smoke checks; use `num_workers=0` when diagnosing loader issues.
- Limit reconstruction/generation samples during development, then scale only after inputs, checkpoint loading, and output validation pass.
- Record run settings next to checkpoints so future agents can match constructor hyperparameters.

## Helper Script Failures

Symptoms:

- `validate_generative_inputs.py` cannot import RDKit.
- `--derive-jtvae-vocab` fails while importing DGL-LifeSci JTVAE utilities.
- The helper reports many missing vocabulary tokens from a sample.

Fixes:

- Install/import RDKit before using any generative workflow; the helper cannot validate molecule parseability without it.
- Prefer a maintained RDKit build compatible with the active Python and DGL-LifeSci stack; do not make old RDKit pins part of reusable runtime instructions.
- Use `--derive-jtvae-vocab` only in an environment with `dgllife` and its JTVAE dependencies installed.
- If missing tokens are expected because the sample is a held-out set, rebuild or extend the vocabulary from the intended training data and retrain/reload with matching checkpoint metadata.
- If only the SMILES parse check is needed, omit `--derive-jtvae-vocab` and `--vocab-file`.

## Common Decision Points

Ask the user before proceeding when:

- A workflow would download pretrained checkpoints, default JTVAE vocabulary/data, or built-in datasets.
- The requested run is a full training/evaluation job rather than a tiny smoke check.
- A checkpoint lacks metadata and there are multiple plausible vocabularies or hyperparameter sets.
- The input chemistry includes charged, stereochemical, or very large molecules where DGMG limitations may materially affect results.
