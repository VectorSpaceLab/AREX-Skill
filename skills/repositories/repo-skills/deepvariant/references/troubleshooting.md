# DeepVariant Cross-Cutting Troubleshooting

Use this reference for failures that span multiple DeepVariant workflows. For workflow-specific details, continue into the nearest sub-skill troubleshooting file.

## Install and Runtime Failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `run_deepvariant` or `run_deeptrio` is not found in Python. | DeepVariant does not expose package console scripts for these production runners. | Use a released Docker/Singularity image or Bazel-built binary; see `install-and-runtime.md`. |
| Python import works but stage execution fails with TensorFlow or compiled extension errors. | Lightweight inspection import is not a full runtime. | Do not treat import success as runnable DeepVariant. Use official containers or build the compiled runtime intentionally. |
| Docker command cannot read inputs. | Host path was not mounted at the container-visible path used in flags. | Rebuild the command so every `--ref`, `--reads`, BED, model, output, log, and intermediate path is under a mounted container directory. |
| Docker permission or daemon error. | User lacks Docker privileges or the daemon/runtime is unavailable. | Ask before changing host configuration; offer Singularity/Apptainer if available. |
| GPU command cannot see devices. | NVIDIA container runtime, image, or driver configuration is missing or incompatible. | Confirm CPU fallback is acceptable or ask before runtime/driver changes. Do not install drivers silently. |

## Data and Index Failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Missing `.fai`, `.bai`, `.crai`, `.tbi`, or `.csi` errors. | Required index companion is absent or not mounted. | Generate/locate the index outside this skill only with approval, then mount parent directories. |
| Region is ignored or fails. | Region contig names differ from FASTA/read naming. | Compare region/BED contigs with FASTA `.fai`; use `chr20` vs `20` consistently. |
| CRAM decoding fails. | CRAM reference is missing, mismatched, or inaccessible inside container. | Mount the same FASTA used for alignment and ensure `.fai` is present. |
| DeepTrio parent or child outputs are missing. | Per-sample flags are incomplete or duo/trio mode is mixed. | Route to `sub-skills/trio-calling/SKILL.md` and require one output VCF per supplied sample. |
| Pangenome-aware run fails before stage execution. | GBZ path/name/shared-memory setup is wrong. | Route to `sub-skills/pangenome-aware-calling/SKILL.md`; check `--pangenome`, `--ref_name_pangenome`, `--sample_name_pangenome`, mounts, and shared memory. |

## Model and Workflow Mismatch

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Unexpected low quality, many no-calls, or odd candidate counts. | Assay/model type mismatch or reference/read mismatch. | Reconfirm sequencing technology, model type, reference build, and regions before rerunning. |
| Custom model fails or produces shape/channel errors. | `model.example_info.json`, channel list, checkpoint, and examples do not match. | Route to `sub-skills/training-custom-models/SKILL.md` and validate metadata before inference. |
| gVCF output is missing or huge. | `--output_gvcf` was omitted or gVCF/reference-block outputs are expectedly large. | Add gVCF only when needed for merging; plan disk and postprocess resources. |
| Haploid or PAR behavior looks wrong. | `--haploid_contigs` or `--par_regions_bed` does not match sample sex/reference. | Verify sample karyotype assumptions, contig names, and PAR BED build. |

## Extra Args and Stage Routing

Wrapper `*_extra_args` are powerful but easy to misuse. Route to `sub-skills/pipeline-stages/SKILL.md` when a user asks to modify:

- `make_examples` internals such as channels, candidate positions, realigner, `use_ref_for_cram`, training/calling mode, or pangenome stage flags.
- `call_variants` internals such as checkpoint/model behavior and batch/inference options.
- `postprocess_variants` internals such as `--postprocess_cpus`, non-variant TFRecords, and gVCF output pairing.

Do not override wrapper-set paths through extra args unless the user intentionally wants a stage-by-stage custom workflow.

## Reporting and Verification Limits

- A generated command preview is not a completed DeepVariant run.
- A skipped native test is not a pass.
- A lightweight helper can catch missing files and obvious path/index mistakes, but it cannot validate biological correctness, BAM/CRAM headers, model accuracy, or cloud/runtime availability.
- If the user asks for evidence that a workflow works on their data, request approval to run the smallest safe dry run or native command with explicit paths and time/resource bounds.
