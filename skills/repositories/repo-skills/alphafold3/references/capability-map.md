# Capability Map

## Owned by `input-preparation`

- Construct AlphaFold 3 input JSON with `dialect: alphafold3` and supported versions.
- Validate protein, RNA, DNA, ligand, SMILES, CCD, user CCD, MSA, template, and bonded atom pair fields.
- Explain AlphaFold Server JSON conversion behavior and unsupported conversion cases.
- Diagnose schema errors before expensive data-pipeline or inference runs.

## Owned by `running-predictions`

- Build safe Docker or local Python command lines for `run_alphafold.py`.
- Choose `--json_path` versus `--input_dir`, stage flags, model/database paths, HMMER binaries, GPU device, buckets, flash attention, samples, seeds, and optional output flags.
- Plan split CPU data pipeline and GPU inference workflows.
- Explain full database/model parameter requirements, sharded databases, SSD staging, and operational safety.
- Run safe preflight checks without downloading data or starting inference.

## Owned by `output-interpretation`

- Inspect AlphaFold 3 result directories and determine expected versus missing files.
- Explain seed/sample subdirectories, top-ranked files, `ranking_scores.csv`, confidence JSONs, summary confidence JSONs, embeddings, distograms, and compression.
- Choose and explain confidence/ranking metrics such as pLDDT, PAE, pTM, ipTM, chain-pair ipTM, and chain-pair PAE minima.
- Diagnose low-confidence, clashing, missing optional output, or output-collision scenarios.

## Owned by `python-apis`

- Use verified Python internals for safe inspection and tooling.
- Parse and serialize inputs with `folding_input.Input`.
- Construct data pipeline and model configs from Python.
- Understand `process_fold_input`, `ModelRunner`, and inference-result extraction boundaries.
- Inspect generated CCD resources and recover package resource issues when appropriate.

## Root-Level Ownership

- Route tasks to the correct sub-skill.
- Provide installation/import sanity checks and cross-cutting troubleshooting.
- Preserve provenance and staleness signals.
- Warn about model parameter terms, full database size, GPU requirements, and expensive side effects.

## Explicit Gaps

- This skill does not include a runnable replacement for full `run_alphafold.py`; future agents should use the installed package/container runner and this skill’s command builders/checkers.
- This skill does not bundle genetic databases, model parameters, Dockerfiles, or SSD mount/copy scripts.
- This skill does not validate scientific correctness of predictions beyond documented confidence and output interpretation guidance.
- This skill does not promise stable support for internal APIs; `python-apis` distinguishes verified internals from public user workflows.
