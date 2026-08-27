# Sampling Configuration

REINVENT4 sampling is a CLI run mode with `run_type = "sampling"`. The model file determines the generator implementation at runtime; the config does not contain a separate `model_type` key. Use `model_file` for a `.prior`, `.model`, or `.chkpt` path, or an internal prior-registry key when the runtime has the corresponding prior files available.

## CLI Shape

```bash
reinvent [--config-format toml|json|yaml] [--device cpu|cuda:0] [--seed 123] \
  [--log-filename sampling.log] [--log-level info] sampling.toml
```

Useful flags:

- `FILE`: positional path to the config file.
- `--config-format`: force `toml`, `json`, or `yaml` if the file extension is ambiguous.
- `--device`: override the top-level `device` key; use `cpu` for safe smoke checks and `cuda:0` only when CUDA is available.
- `--seed`: set random seeds for reproducibility.
- `--log-filename`: write logs to a file instead of stderr.
- `--log-level`: choose `verbose`, `debug`, `info`, `warning`, `error`, or `critical`.
- `--dotenv-filename`: load environment variables needed by scoring plugins; rarely needed for pure sampling.
- `--enable-rdkit-log-levels`: expose RDKit logs while debugging chemistry issues.
- `--version`: print installed REINVENT4 version.

`reinvent_datapre` is a separate preprocessing CLI; it does not run sampling.

## Top-Level Keys

```toml
run_type = "sampling"
device = "cpu"
# Optional: write the parsed config as JSON for audit/debugging.
# json_out_config = "sampling.resolved.json"
# Optional: TensorBoard summary directory for supported sampler reports.
# tb_logdir = "tb_sampling"

[parameters]
model_file = "priors/reinvent.prior"
output_file = "sampling.csv"
num_smiles = 100
unique_molecules = true
randomize_smiles = true
```

Common top-level keys:

- `run_type`: must be `"sampling"`.
- `device`: PyTorch device string. `cpu` is portable; `cuda:0` needs a CUDA-capable install and visible GPU.
- `json_out_config`: optional JSON dump of the parsed config.
- `tb_logdir`: optional TensorBoard directory for sampler reporting.
- `seed`: optional config-level seed; `--seed` also works from the CLI.

## `[parameters]` Keys

Required:

- `model_file`: model/prior/checkpoint to sample from.
- `num_smiles`: number of generations. For seed-based models this is per input row.

Optional or defaulted:

- `smiles_file`: seed file. Required for LibInvent, LinkInvent, Mol2Mol, and PepInvent; usually omitted for Reinvent de novo sampling.
- `output_file`: output CSV path; default in the code is `samples.csv`, but explicit paths are safer.
- `unique_molecules`: when true, REINVENT4 filters to valid unique molecules before writing.
- `randomize_smiles`: randomizes input SMILES atom order for non-transformer samplers; transformer-based models force this off internally because they were trained on canonical SMILES.
- `isomeric_smiles`: generate isomeric SMILES for non-transformer samplers; transformer-based models force isomeric output.
- `sample_strategy`: transformer models only, typically `multinomial` or `beamsearch`.
- `temperature`: transformer multinomial sampling temperature; lower is more conservative, higher is more diverse.
- `target_smiles_path`: Mol2Mol likelihood-check path; when set, REINVENT4 writes `target_nll_file`.
- `target_nll_file`: CSV path for Mol2Mol target NLL output when `target_smiles_path` is used.

Optional `[filter]` section:

```toml
[filter]
smarts = ["[N+](=O)[O-]", "[SH]"]
```

This removes sampled molecules matching SMARTS patterns after generation. Use the `scoring` sub-skill for full scoring component design; this filter is only a sampling-time blocklist.

## Model Modes and Seed Files

| Mode | Typical model file | `smiles_file` | Output identity columns |
| --- | --- | --- | --- |
| Reinvent | `reinvent.prior`, trained `.model`, `.chkpt` | Not required for normal de novo generation | `SMILES`, `SMILES_state`, `NLL` |
| LibInvent | `libinvent.prior` | One scaffold per line with attachment points marked by `*` or labels like `[*:0]` and `[*:1]` | Adds `Scaffold`, `R-groups` |
| LinkInvent | `linkinvent.prior` | Two warhead SMILES per line separated by `|`; each side should carry an attachment point | Adds `Warheads`, `Linker` |
| Mol2Mol | `mol2mol_* .prior` | One input molecule per line; optional second column labels are tolerated by readers that use the first column | Adds `Input_SMILES`, `Tanimoto` |
| PepInvent | `pepinvent.prior` | One masked peptide/CHUCKLES-like row per line; masks use `?` and segment separators use `|` | Adds `Masked_input_peptide`, `Fillers` |

The runtime determines the actual mode by loading `model_file`. If you only have a config and want a static safety check, pass the intended mode to the bundled validator with `--model-mode`.

## Internal Prior Keys

REINVENT4 can resolve some dot-prefixed keys through its prior registry when the runtime has prior files installed or `REINVENT_PRIOR_BASE` points to them:

- `.reinvent`
- `.libinvent`
- `.linkinvent`
- `.m2m_high`
- `.m2m_medium`
- `.m2m_mmp`
- `.m2m_scaffold`
- `.m2m_scaffold_generic`
- `.m2m_similarity`

Do not assume public prior files are bundled with the package or this skill. If a config uses local prior paths, verify the files exist before running. If it uses registry keys, validate the key shape but let the installed REINVENT4 runtime resolve the actual file.

## Templates

### Reinvent De Novo

```toml
run_type = "sampling"
device = "cpu"

[parameters]
model_file = "priors/reinvent.prior"
output_file = "sampling_reinvent.csv"
num_smiles = 100
unique_molecules = true
randomize_smiles = true
```

### LibInvent Scaffold Decoration

```toml
run_type = "sampling"
device = "cpu"

[parameters]
model_file = "priors/libinvent.prior"
smiles_file = "scaffolds.smi"
output_file = "sampling_libinvent.csv"
num_smiles = 50
unique_molecules = true
randomize_smiles = true
```

Example `scaffolds.smi` rows:

```text
[*:0]Cc2ccc1cncc(C[*:1])c1c2
[*:0]Cc2cnc1cncc(C[*:1])c1c2
```

### LinkInvent Warhead Linking

```toml
run_type = "sampling"
device = "cpu"

[parameters]
model_file = "priors/linkinvent.prior"
smiles_file = "warheads.smi"
output_file = "sampling_linkinvent.csv"
num_smiles = 25
unique_molecules = true
randomize_smiles = false
```

Example `warheads.smi` row:

```text
Oc1cncc(*)c1|*c1ccoc1
```

### Mol2Mol Analogue Generation

```toml
run_type = "sampling"
device = "cpu"

[parameters]
model_file = "priors/mol2mol_medium_similarity.prior"
smiles_file = "mol2mol.smi"
output_file = "sampling_mol2mol.csv"
num_smiles = 20
sample_strategy = "multinomial"
temperature = 1.0
unique_molecules = true
randomize_smiles = false
```

Use `sample_strategy = "beamsearch"` for deterministic transformer sampling. Avoid large `num_smiles` with Mol2Mol beam search; REINVENT4 warns that values above 300 may be very slow.

### PepInvent Mask Filling

```toml
run_type = "sampling"
device = "cpu"

[parameters]
model_file = "priors/pepinvent.prior"
smiles_file = "pepinvent.smi"
output_file = "sampling_pepinvent.csv"
num_smiles = 10
sample_strategy = "beamsearch"
temperature = 1.0
unique_molecules = true
randomize_smiles = false
```

Example masked row shape:

```text
?|N[C@@H](CO)C(=O)|?|N[C@@H](Cc1ccc(O)cc1)C(=O)
```

## Output CSV Checks

After a successful run:

- Confirm `output_file` exists and has a header.
- Confirm row count matches expectations: Reinvent usually writes up to `num_smiles`; seed-based models target `num_smiles * number_of_seed_rows`, then filtering can reduce rows when `unique_molecules = true` or `[filter]` is used.
- Check `SMILES_state`; many invalid rows indicate model/seed mismatch, too much model drift, or unsuitable seed chemistry.
- Check mode-specific columns: `Scaffold`, `Warheads`, `Input_SMILES`, `Tanimoto`, or `Masked_input_peptide` should appear for the matching generator.
- Inspect `NLL`; extreme or collapsed values can indicate a wrong model, unsuitable seed, or overtrained agent.
