# Germline Calling Troubleshooting

Use this reference to diagnose setup and command-construction problems before running `run_deepvariant`. Full Docker/Singularity execution, image pulls, GPU checks, and native genomics validation should happen only with user approval and real data access.

## Missing Indexes

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| DeepVariant cannot open FASTA index or reports reference access failure. | `--ref` is missing `.fai` or the `.fai` is not mounted. | Generate with `samtools faidx ref.fa` or mount the existing `ref.fa.fai`; for bgzipped FASTA, keep the index beside the exact reference path used inside the container. |
| Reads cannot be queried or error mentions no index. | BAM is missing `.bai`, CRAM is missing `.crai`, or index basename does not match container path. | Create or mount `sample.bam.bai`, `sample.bai`, `sample.cram.crai`, or equivalent; verify the path visible inside Docker/Singularity. |
| VCF/gVCF output exists but index is missing. | Run failed before postprocess indexing, output path is not writable, or output was not bgzipped. | Check `postprocess_variants.log` under `--logging_dir`; ensure output path ends in `.vcf.gz` or `.g.vcf.gz` and parent is writable. |
| Region BED is not found. | BED parent directory is not mounted or the command uses a host path inside the container. | Bind the BED parent and use the container path in `--regions`. |

## Reference, Reads, and Region Mismatch

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| No calls or unexpectedly few calls for requested regions. | `--regions` contig names are not present in both reference and reads, or reads were aligned to a different reference naming convention. | Compare FASTA `.fai` contig names and read header contigs; use `chr20` vs `20` consistently; realign or convert only with validated tooling. |
| Error indicates no common contigs or insufficient reference coverage. | Reference and reads are incompatible. | Use the exact reference build used for alignment or a compatible no-alt/decoy build with expected shared contigs. |
| CRAM input fails despite FASTA being present. | CRAM index or reference path is missing inside the container, or a lower-level CRAM reference flag was changed. | Mount CRAM, `.crai`, FASTA, and `.fai`; verify that the dry-run `make_examples` command uses the intended `--ref` for CRAM decoding. |
| BED regions are ignored or fail. | BED uses a different reference naming convention or is not mounted. | Convert BED contig names/coordinates to match `--ref`, and bind the BED parent directory. |

## Docker and Singularity Mounts

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Input file exists on host but DeepVariant says it does not exist. | Host directory was not bound to the path used in `--ref`, `--reads`, `--regions`, or model flags. | Bind every host input parent with Docker `-v host:container` or Singularity `-B host:container`, then use container paths in flags. |
| Output directory is empty or command cannot write outputs. | Output parent is not mounted or not writable by the container user. | Create host output directory first and bind it to `/output`; write VCF, gVCF, logs, and intermediates under that mount. |
| Singularity fails with Python/library compatibility errors. | Host environment variables leak into the container. | Add `--cleanenv`; bind only required paths; avoid relying on host Python packages. |
| Command uses `$(pwd):$(pwd)` and fails on another machine. | Working-directory bind pattern depends on exact host path. | Prefer explicit `/input`, `/reference`, `/output`, and `/model` container paths for portable instructions. |

## GPU Confusion

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| GPU is not used. | CPU image was used, Docker `--gpus 1` was omitted, or Singularity `--nv` was omitted. | Use `google/deepvariant:1.10.0-gpu` plus Docker `--gpus 1`, or Singularity `--nv` with the `-gpu` image. |
| User expects multiple GPUs to speed up one sample. | `call_variants` can use at most one GPU in the standard pipeline; other stages are CPU-bound. | Use one GPU for one sample, or parallelize independent samples outside this command after planning resource isolation. |
| GPU driver/runtime installation is requested. | Host-level mutation is required. | Treat as unsafe; ask for explicit approval and prefer user-managed installation instructions rather than automatic mutation. |

## Wrong Model Type or Assay

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| WES command runs on whole genome or WGS command runs on capture data. | Model type does not match assay. | Use `WGS` for Illumina WGS and `WES` for Illumina exome/capture; pass capture BED via `--regions` for WES. |
| ONT or PacBio results are unexpectedly poor. | Wrong long-read model, chemistry mismatch, or non-HiFi/non-R10.4 data. | Use `PACBIO` for PacBio HiFi and `ONT_R104` for ONT R10.4.1 simplex/duplex; clarify unsupported chemistry before running. |
| Hybrid command receives separate PacBio and Illumina BAMs. | `run_deepvariant --reads` expects one reads path. | Prepare a compatible merged/sorted/indexed input first, or use a workflow designed for separate evidence if available. |
| RNA-seq command produces inappropriate genome-wide calls. | Calling was not restricted to expressed or target regions. | Use `RNASEQ`, `--disable_small_model=true`, and a BED/region set matching expressed regions and evaluation needs. |
| MAS-Seq or RNA-seq guidance is copied to DNA WGS. | Transcript-assay model assumptions were reused for DNA data. | Re-select model type from assay; use `WGS`, `WES`, `PACBIO`, or `ONT_R104` for DNA data as appropriate. |

DeepVariant's released models are primarily human germline diploid models unless a specific model and workflow say otherwise. For non-human, pooled, cancer, somatic, metagenomic, or non-diploid use, do not promise standard accuracy; require custom validation or route to a suitable workflow.

## Haploid and PAR Misuse

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Heterozygous calls remain in non-PAR chrX/chrY for an XY sample. | `--haploid_contigs` was omitted or contig names do not match the reference. | Use `--haploid_contigs="chrX,chrY"` for GRCh38-style references or `"X,Y"` for GRCh37-style references. |
| PAR regions are incorrectly forced haploid. | `--par_regions_bed` was omitted or from a different reference build. | Provide a reference-specific PAR BED matching `--ref`; mount it under the path used in the command. |
| XX sample loses expected heterozygous X calls. | Haploid flags were copied from an XY command. | Remove `--haploid_contigs` unless the sample/region is intentionally haploid. |
| Haploid flags appear in dry-run `make_examples` but final VCF still looks diploid. | `postprocess_variants` logs or flags were not inspected, or the PAR BED excluded the region. | Inspect dry-run and `postprocess_variants.log`; verify contig names and PAR intervals. |

## gVCF Expectations

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| User expected gVCF but only VCF exists. | `--output_gvcf` was omitted. | Add `--output_gvcf=/output/sample.g.vcf.gz`; expect both gVCF and `.tbi` after successful postprocess. |
| gVCF is much larger or slower than expected. | Low-depth data and small GQ bins create more reference blocks; postprocess gVCF can be memory/runtime heavy. | Decide whether gVCF is truly needed; tune `gvcf_gq_binsize` through `--make_examples_extra_args` only after understanding downstream requirements. |
| User expects `MED_DP` but gVCF has only `MIN_DP`. | `include_med_dp` was not enabled. | Add `--make_examples_extra_args="include_med_dp=true"` and validate with `--dry_run=true`. |
| gVCF records appear for no-call or low-confidence regions. | gVCF includes reference blocks and unknown genotypes by design. | Explain that gVCF is not just variants; use VCF for variant-only calls and gVCF for cohort workflows. |

## Custom Model and Small Model Problems

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Error says custom model files do not exist. | `--customized_model` points to the wrong checkpoint prefix or SavedModel directory. | For checkpoint prefix, verify `.data-00000-of-00001` and `.index`; for SavedModel, verify `saved_model.pb` in the directory. |
| Error says `model.example_info.json` is missing. | r1.10 needs model metadata for model-specific example generation. | Put `model.example_info.json` in the model directory or pass `--customized_model_json`; ask whoever trained the model what flags/channels it requires. |
| Custom model runs but results look nonsensical. | Model metadata, assay, channel list, reference build, or data preparation mismatch. | Route to custom training guidance; validate model provenance and example-info compatibility before inference. |
| User wants to bypass small model. | Debugging, custom model, RNA-seq, hybrid review, or reproducibility requirement. | Add `--disable_small_model=true`; note that this may increase runtime. |
| Custom small model is provided without thresholds. | Small-model behavior may be inappropriate. | Use explicit threshold extra args such as `small_model_snp_gq_threshold` and `small_model_indel_gq_threshold`, or disable the small model. |

## Extra-Args Formatting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Stage flag is ignored or parsed incorrectly. | Extra args are separated by spaces or booleans are not `true`/`false`. | Use comma-separated `flag=value` pairs inside one shell-quoted string. |
| Value contains comma or spaces. | Shell or wrapper split the value unexpectedly. | Quote the nested value and verify with `--dry_run=true`; consider stage-by-stage commands for complex customization. |
| User sets a flag already controlled by the wrapper. | Extra arg overrides a wrapper value, possibly changing behavior. | Use dry-run output to inspect final command; prefer explicit wrapper flags when available. |
| `make_examples_extra_args` is used to change CRAM reference behavior. | Lower-level behavior is being modified from the wrapper. | Require dry-run inspection and route persistent stage-level policy to `../pipeline-stages/SKILL.md`. |

## Triage Order

1. Run the bundled command builder for static validation and mount planning.
2. If safe and approved, run the container command with `--dry_run=true`.
3. Inspect the printed stage commands for model-specific flags, gVCF wiring, small-model settings, haploid/PAR propagation, phasing behavior, and output paths.
4. Only then run full DeepVariant on user data, starting with a small `--regions` target when feasible.
5. If failures occur, inspect per-stage logs under `--logging_dir` and decide whether to route to lower-level `../pipeline-stages/SKILL.md` troubleshooting.
