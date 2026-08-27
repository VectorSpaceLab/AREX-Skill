# `boltz predict` CLI Reference

## Shape

```bash
boltz predict DATA [OPTIONS]
```

`DATA` is a YAML/FASTA file or a directory of YAML/FASTA files.

## File and Cache Options

| Option | Use |
| --- | --- |
| `--out_dir PATH` | Directory for `processed/`, `predictions/`, and logs. Default is current directory. |
| `--cache PATH` | Cache for downloaded CCD/molecule data and model checkpoints. Defaults to `~/.boltz` or `BOLTZ_CACHE`. |
| `--checkpoint PATH` | Custom structure checkpoint. Match checkpoint to `--model`. |
| `--affinity_checkpoint PATH` | Custom Boltz-2 affinity checkpoint. |
| `--override` | Reprocess and overwrite existing predictions/affinity outputs. |

`BOLTZ_CACHE` must be absolute when set. Prefer `--cache /absolute/path` in automation.

## Device and Performance Options

| Option | Default | Use |
| --- | --- | --- |
| `--devices INTEGER` | `1` | Number of devices. |
| `--accelerator gpu|cpu|tpu` | `gpu` | Runtime accelerator. CPU is supported but slow. |
| `--num_workers INTEGER` | `2` | DataLoader workers. |
| `--preprocessing-threads INTEGER` | CPU count in source, help may show `1` depending package build | Thread count for preprocessing. |
| `--max_parallel_samples INTEGER` | package default | Parallel diffusion samples; reduce for memory limits. |
| `--no_kernels` | off | Disable specialized triangular-update kernels for compatibility. |

## Sampling and Structure Options

| Option | Default | Use |
| --- | --- | --- |
| `--model boltz1|boltz2` | `boltz2` | Model family. Boltz-2 supports affinity. |
| `--recycling_steps INTEGER` | `3` | Recycling iterations. More can improve quality but costs time. |
| `--sampling_steps INTEGER` | `200` | Diffusion sampling steps for structure prediction. |
| `--diffusion_samples INTEGER` | `1` | Number of candidate structures. |
| `--step_scale FLOAT` | model-specific | Diffusion temperature-like scale; recommended 1–2. |
| `--seed INTEGER` | none | Reproducible random seed. |
| `--method TEXT` | none | Advanced method override; leave unset unless required. |
| `--use_potentials` | off | Enable inference-time potentials for steering/physical plausibility. |

For AlphaFold3-like heavier sampling:

```bash
boltz predict input.yaml --recycling_steps 10 --diffusion_samples 25
```

## Output Detail Options

| Option | Default | Use |
| --- | --- | --- |
| `--output_format pdb|mmcif` | `mmcif` | Structure output format. |
| `--write_full_pae` | off in code, help may mention true | Dump full PAE arrays. |
| `--write_full_pde` | off | Dump full PDE arrays. |
| `--write_embeddings` | off | Dump `s` and `z` embeddings. |

Large arrays can consume significant disk space.

## MSA Server Options

| Option | Default | Use |
| --- | --- | --- |
| `--use_msa_server` | off | Generate MSAs through an MMSeqs2-compatible server. |
| `--msa_server_url TEXT` | `https://api.colabfold.com` | Server endpoint. |
| `--msa_pairing_strategy TEXT` | `greedy` | Pairing strategy; documented values are `greedy` and `complete`. |
| `--msa_server_username TEXT` | none | Basic-auth username; can use `BOLTZ_MSA_USERNAME`. |
| `--msa_server_password TEXT` | none | Basic-auth password; can use `BOLTZ_MSA_PASSWORD`. |
| `--api_key_header TEXT` | `X-API-Key` when key used | API-key header name. |
| `--api_key_value TEXT` | none | API-key value; can use `MSA_API_KEY_VALUE`. |

Use exactly one auth method: basic auth or API key auth. Prefer environment variables for secret values.

## MSA Size Options

| Option | Default | Use |
| --- | --- | --- |
| `--max_msa_seqs INTEGER` | `8192` | Maximum MSA sequences parsed/used. |
| `--subsample_msa` | flag, package help may describe default true | Enable MSA subsampling. |
| `--num_subsampled_msa INTEGER` | `1024` | Number of MSA rows after subsampling. |

## Affinity Options

Affinity is enabled by YAML `properties`, then controlled with:

| Option | Default | Use |
| --- | --- | --- |
| `--sampling_steps_affinity INTEGER` | `200` | Affinity sampling steps. |
| `--diffusion_samples_affinity INTEGER` | `5` in CLI help | Affinity diffusion samples. |
| `--affinity_mw_correction` | off | Apply molecular-weight correction to the affinity value head. |
| `--affinity_checkpoint PATH` | Boltz-2 provided checkpoint | Custom affinity checkpoint. |

## Safe Command Templates

MSA server:

```bash
boltz predict input.yaml --out_dir predictions --use_msa_server --model boltz2
```

Custom MSA:

```bash
boltz predict input.yaml --out_dir predictions --model boltz2
```

Rerun after changing inputs:

```bash
boltz predict input.yaml --out_dir predictions --use_msa_server --override
```

Compatibility retry:

```bash
boltz predict input.yaml --out_dir predictions --use_msa_server --no_kernels
```
