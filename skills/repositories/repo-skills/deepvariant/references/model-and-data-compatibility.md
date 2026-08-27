# Model and Data Compatibility

Use this reference before choosing a DeepVariant, DeepTrio, pangenome-aware, or custom-model command. Most failures come from a mismatch among assay, model type, reference build, read alignment, region naming, and model metadata.

## Model Type Routing

| Workflow | Typical model types | Route |
| --- | --- | --- |
| Single-sample germline WGS/WES | `WGS`, `WES` | `sub-skills/germline-calling/SKILL.md` |
| Long-read germline | `PACBIO`, `ONT_R104` | `sub-skills/germline-calling/SKILL.md` |
| Hybrid PacBio + Illumina | `HYBRID_PACBIO_ILLUMINA` | `sub-skills/germline-calling/SKILL.md` |
| RNA or MAS-Seq DeepVariant | `RNASEQ`, `MASSEQ` | `sub-skills/germline-calling/SKILL.md` |
| DeepTrio family calling | `WGS`, `WES`, `PACBIO`, `ONT` | `sub-skills/trio-calling/SKILL.md` |
| Pangenome-aware short-read calling | `WGS`, `WES` | `sub-skills/pangenome-aware-calling/SKILL.md` |
| Custom trained model | Match training examples and checkpoint metadata | `sub-skills/training-custom-models/SKILL.md`, then return to calling route |

Do not use extra args or custom models to hide assay mismatches. If the input data technology differs from the model family, stop and ask the user to confirm the intended model or training path.

## Input File Contracts

| Input | Required companions | Checks |
| --- | --- | --- |
| FASTA reference | `.fai`; often `.gzi` for bgzipped FASTA | Contig names must match reads, regions, BED/PAR files, truth data, and pangenome references. |
| BAM | `.bai` or `.csi` | Must be aligned, sorted, and indexed to the same reference build. |
| CRAM | `.crai` plus FASTA `.fai` | CRAM decoding depends on a compatible reference; ensure the FASTA is mounted and visible. |
| Region string | matching FASTA contig names | Prefer literal `chr:start-end` or a BED with the same naming convention. |
| BED/PAR/confident regions | indexed only when required by tool; same reference build | Use for restricted calling, haploid PAR exclusions, or training confidence masks. |
| gVCF output | output path plus stage non-variant TFRecords internally | Expect larger outputs and postprocess resource needs. |
| GBZ pangenome | mounted GBZ path and shared-memory plan | Confirm `--ref_name_pangenome` and `--sample_name_pangenome` when defaults do not match. |
| Custom model | checkpoint/SavedModel plus matching `model.example_info.json` or explicit custom-model JSON | Shape/channel metadata must match example generation. |

## Reference and Contig Rules

- The reference FASTA used for alignment should be the same build passed to DeepVariant.
- Region names must match FASTA/read contig names exactly; `chr20` and `20` are not interchangeable.
- For CRAM, make the decoding FASTA visible inside the container even if the CRAM header contains a URI.
- For haploid X/Y support, use contig names that match the FASTA and supply a reference-matched PAR BED when excluding pseudoautosomal regions.
- For DeepTrio, every supplied child/parent BAM or CRAM must use the same reference and compatible contig naming.
- For pangenome-aware workflows, distinguish the linear FASTA reference from names inside the GBZ pangenome.

## Output and Sample Naming

- Use one final VCF per called sample.
- Request gVCFs when downstream cohort or family merging needs reference blocks.
- DeepTrio requires per-sample output flags for child and every supplied parent.
- Pangenome-aware workflows may produce additional intermediates; plan a writable intermediate directory when debugging or preserving artifacts.
- For reports, decide during the run whether to enable `--vcf_stats_report`, `--runtime_report`, and `--logging_dir`; post-run tools need the relevant outputs retained.

## Custom Model Compatibility

A custom model handoff is ready only when:

1. Training examples, tune examples, and final inference examples share the intended channel list and shape.
2. The checkpoint or SavedModel is paired with compatible `model.example_info.json` metadata or explicit custom-model JSON.
3. The model family and assay match the inference reads.
4. Held-out validation has been performed on data not used for training or tuning.
5. The caller understands whether to disable the small model so all candidates reach the custom CNN.

If any item is unknown, route to `sub-skills/training-custom-models/SKILL.md` before constructing an inference command.

## Quick Preflight

Use the root input checker for lightweight local validation when paths are available:

```bash
python scripts/deepvariant_input_check.py --workflow germline --model-type WGS --ref ref.fa --reads sample.bam --output-vcf out.vcf.gz --regions chr20:1-100000
```

The checker validates path/index/region/output shape only. It does not parse BAM/CRAM headers, inspect FASTA biology, run DeepVariant, or prove model accuracy.
