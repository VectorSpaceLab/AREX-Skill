# API Reference

This reference covers the public Python inference surface for Chai-1. Use it when writing scripts or adapting CLI options into Python calls.

## Primary Entry Point

```python
from pathlib import Path
from chai_lab.chai1 import run_inference

candidates = run_inference(
    fasta_file=Path("input.fasta"),
    output_dir=Path("outputs/chai-run"),
    seed=42,
    device="cuda:0",
)
```

Verified signature for Chai Lab `0.6.1`:

```python
run_inference(
    fasta_file: Path,
    *,
    output_dir: Path,
    use_esm_embeddings: bool = True,
    use_msa_server: bool = False,
    msa_server_url: str = "https://api.colabfold.com",
    msa_directory: Path | None = None,
    constraint_path: Path | None = None,
    use_templates_server: bool = False,
    template_hits_path: Path | None = None,
    recycle_msa_subsample: int = 0,
    num_trunk_recycles: int = 3,
    num_diffn_timesteps: int = 200,
    num_diffn_samples: int = 5,
    num_trunk_samples: int = 1,
    seed: int | None = None,
    device: str | None = None,
    low_memory: bool = True,
    fasta_names_as_cif_chains: bool = False,
) -> StructureCandidates
```

## Parameters By Group

### Required IO

| Parameter | Meaning |
| --- | --- |
| `fasta_file` | Path to a Chai FASTA describing the entire complex. The file must exist and contain at least one input. |
| `output_dir` | Directory where Chai writes CIF, score, and optional MSA coverage outputs. It may be absent or empty, but must not contain files. |

### Embeddings, MSA, Templates, Restraints

| Parameter | Default | Meaning |
| --- | --- | --- |
| `use_esm_embeddings` | `True` | Build ESM embedding context for input chains. |
| `use_msa_server` | `False` | Generate MSAs through the configured ColabFold-compatible server. Route setup to `../msa-templates/SKILL.md`. |
| `msa_server_url` | `"https://api.colabfold.com"` | Server URL used when `use_msa_server=True`. |
| `msa_directory` | `None` | Directory containing prepared `.aligned.pqt` MSA files. Mutually exclusive with `use_msa_server=True`. |
| `constraint_path` | `None` | Restraint CSV path. Route schema to `../restraints-glycans/SKILL.md`. |
| `use_templates_server` | `False` | Ask the MSA/template server to search templates. Mutually exclusive with local template hits. |
| `template_hits_path` | `None` | Local template hits `.m8` file. Route schema to `../msa-templates/SKILL.md`. |

### Sampling And Compute

| Parameter | Default | Meaning |
| --- | --- | --- |
| `recycle_msa_subsample` | `0` | Optional MSA subsampling during recycle. |
| `num_trunk_recycles` | `3` | Trunk recycle count. |
| `num_diffn_timesteps` | `200` | Diffusion denoising step count. |
| `num_diffn_samples` | `5` | Candidate structures produced per trunk sample. Must be greater than zero. |
| `num_trunk_samples` | `1` | Independent trunk samples. Must be greater than zero. With values above one, outputs are written under `trunk_0`, `trunk_1`, ... |
| `seed` | `None` | Reproducibility seed. With multiple trunk samples, Chai increments the seed per trunk. |
| `device` | `None` | Torch device string. `None` resolves to `cuda:0`; pass `"cuda:0"` explicitly for clarity. |
| `low_memory` | `True` | Move selected intermediate outputs to CPU to lower GPU memory pressure. |

### Output Chain Naming

| Parameter | Default | Meaning |
| --- | --- | --- |
| `fasta_names_as_cif_chains` | `False` | Use FASTA entity names as CIF chain names. Coordinate this with FASTA naming and restraint chain references. |

## Return Type

`run_inference` returns `StructureCandidates`:

| Field | Meaning |
| --- | --- |
| `cif_paths: list[Path]` | Candidate CIF files, one per diffusion sample across all trunk samples. |
| `ranking_data: list[SampleRanking]` | Ranking/confidence outputs for each candidate. Higher `aggregate_score` is better. |
| `msa_coverage_plot_path: Path | None` | `msa_depth.pdf` path when MSA features are present; otherwise `None`. |
| `pae` | Predicted aligned error tensor with shape `candidate x num_tokens x num_tokens`. |
| `pde` | Predicted distance error tensor with shape `candidate x num_tokens x num_tokens`. |
| `plddt` | Predicted local distance difference test tensor with shape `candidate x num_tokens`. |

Sort candidates by aggregate score:

```python
sorted_candidates = candidates.sorted()
best_cif = sorted_candidates.cif_paths[0]
best_score = sorted_candidates.ranking_data[0].aggregate_score.item()
```

Read per-sample scores saved to disk:

```python
import numpy as np

scores = np.load("outputs/chai-run/scores.model_idx_0.npz")
print(scores.files)
```

## Output Directory Contract

`run_inference` checks `output_dir` before model setup:

```python
if output_dir.exists():
    assert not any(output_dir.iterdir()), f"Output directory {output_dir} is not empty."
```

Use this pattern in scripts:

```python
from pathlib import Path

output_dir = Path("outputs/chai-run")
if output_dir.exists() and any(output_dir.iterdir()):
    raise SystemExit(f"Refusing to overwrite non-empty output directory: {output_dir}")
output_dir.parent.mkdir(parents=True, exist_ok=True)
```

Only delete an existing output directory when the user explicitly asked for cleanup.

## Advanced Context APIs

Use this route for custom contexts rather than ordinary command-line folding:

```python
import torch
from pathlib import Path
from chai_lab.chai1 import make_all_atom_feature_context, run_folding_on_context

feature_context = make_all_atom_feature_context(
    fasta_file=Path("input.fasta"),
    output_dir=Path("outputs/chai-context"),
    use_esm_embeddings=True,
    use_msa_server=False,
    msa_directory=None,
    constraint_path=None,
    use_templates_server=False,
    templates_path=None,
    esm_device=torch.device("cuda:0"),
)

candidates = run_folding_on_context(
    feature_context,
    output_dir=Path("outputs/chai-context"),
    num_trunk_recycles=3,
    num_diffn_timesteps=200,
    num_diffn_samples=5,
    seed=42,
    device=torch.device("cuda:0"),
    low_memory=True,
)
```

Verified signatures for Chai Lab `0.6.1`:

```python
make_all_atom_feature_context(
    fasta_file: Path,
    *,
    output_dir: Path,
    entity_name_as_subchain: bool = False,
    use_esm_embeddings: bool = True,
    use_msa_server: bool = False,
    msa_server_url: str = "https://api.colabfold.com",
    msa_directory: Path | None = None,
    constraint_path: Path | None = None,
    use_templates_server: bool = False,
    templates_path: Path | None = None,
    esm_device: torch.device = torch.device("cpu"),
)
```

```python
run_folding_on_context(
    feature_context: AllAtomFeatureContext,
    *,
    output_dir: Path,
    recycle_msa_subsample: int = 0,
    num_trunk_recycles: int = 3,
    num_diffn_timesteps: int = 200,
    num_diffn_samples: int = 5,
    entity_names_as_chain_names_in_output_cif: bool = False,
    seed: int | None = None,
    device: torch.device | None = None,
    low_memory: bool,
) -> StructureCandidates
```

Key differences from `run_inference`:

- `make_all_atom_feature_context` uses `templates_path`; `run_inference` exposes this as `template_hits_path`.
- `make_all_atom_feature_context` uses `entity_name_as_subchain`; `run_inference` exposes this as `fasta_names_as_cif_chains` and forwards it to output chain naming.
- `run_folding_on_context` expects a `torch.device`, not a string, for `device`.
- Lower-level context APIs are useful for custom embeddings, MSAs, templates, or constraints, but sibling sub-skills own the file formats.

## Common Script Skeleton

```python
from pathlib import Path
from chai_lab.chai1 import run_inference

fasta_file = Path("input.fasta")
output_dir = Path("outputs/chai-run")
if output_dir.exists() and any(output_dir.iterdir()):
    raise SystemExit(f"Refusing to overwrite non-empty output directory: {output_dir}")
output_dir.parent.mkdir(parents=True, exist_ok=True)

candidates = run_inference(
    fasta_file=fasta_file,
    output_dir=output_dir,
    use_esm_embeddings=True,
    num_trunk_recycles=3,
    num_diffn_timesteps=200,
    num_diffn_samples=5,
    num_trunk_samples=1,
    seed=42,
    device="cuda:0",
    low_memory=True,
)

for index, ranking in enumerate(candidates.ranking_data):
    print(index, candidates.cif_paths[index], ranking.aggregate_score.item())
print("best", candidates.sorted().cif_paths[0])
```
