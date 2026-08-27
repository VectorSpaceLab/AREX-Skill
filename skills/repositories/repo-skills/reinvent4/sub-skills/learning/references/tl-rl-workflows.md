# TL and Staged RL Workflows

This reference distills the REINVENT4 learning run modes for future agents. It is self-contained: use it to prepare configs, validation plans, and handoffs without opening original repository examples.

## Transfer learning (`run_type = "transfer_learning"`)

Transfer learning retrains a prior or checkpoint on a focused SMILES set and writes a new agent model. Use it when the user has known actives, target-relevant compounds, or a chemical series but no fully validated objective function.

Minimal TL shape:

```toml
run_type = "transfer_learning"
device = "cpu"
tb_logdir = "tb_TL"

[parameters]
input_model_file = "priors/reinvent.prior"
smiles_file = "train.smi"
validation_smiles_file = "valid.smi"
output_model_file = "tl_agent.model"
num_epochs = 50
save_every_n_epochs = 10
batch_size = 50
sample_batch_size = 100
num_refs = 100
tb_isim = false
```

Important TL parameters:

- `input_model_file`: prior or checkpoint to adapt. The model type determines accepted SMILES format and tokenizer.
- `smiles_file`: training data; REINVENT4 reads the first column for Reinvent and Mol2Mol, while LibInvent/LinkInvent training data uses two fragment columns.
- `validation_smiles_file`: optional but strongly recommended because REINVENT4 does not split train/validation automatically.
- `output_model_file`: final model, suitable for sampling or as `agent_file` in staged learning.
- `num_epochs`: training length. Start low for an exploratory run and choose a checkpoint based on validation loss and generated chemistry.
- `save_every_n_epochs`: writes intermediate checkpoints; useful for choosing an earlier less-overfit model.
- `sample_batch_size`, `num_refs`, `tb_isim`: monitoring and similarity diagnostics. Use `num_refs = 0` for large reference sets to avoid expensive similarity histograms.
- `[scheduler]`: optional learning-rate scheduler arguments. Defaults are valid; only expose this when the user explicitly needs optimizer tuning.

Mol2Mol TL requires pair construction thresholds:

```toml
[parameters.pairs]
type = "tanimoto"
lower_threshold = 0.7
upper_threshold = 1.0
min_cardinality = 1
max_cardinality = 199
```

Use TL output safely:

1. Run static validation with `scripts/check_learning_config.py`.
2. If the user approves training, run `reinvent transfer_learning.toml` or `reinvent --device cpu transfer_learning.toml` for CPU fallback.
3. Inspect TensorBoard loss curves and sample from `output_model_file` before using it as an RL agent.
4. If valid SMILES rate drops or structures collapse to memorized actives, reduce epochs or use an earlier checkpoint.

## Staged learning (`run_type = "staged_learning"`)

REINVENT4 uses `staged_learning` for both single-stage RL and curriculum learning. RL samples molecules, scores them, and updates the agent with Direct Augmented Prior (`dap`) while the prior remains fixed.

Minimal single-stage RL shape:

```toml
run_type = "staged_learning"
device = "cpu"
tb_logdir = "tb_RL"

[parameters]
prior_file = "priors/reinvent.prior"
agent_file = "priors/reinvent.prior"
summary_csv_prefix = "rl_run"
batch_size = 64
randomize_smiles = true

[learning_strategy]
type = "dap"
sigma = 128
rate = 0.0001

[diversity_filter]
type = "IdenticalMurckoScaffold"
bucket_size = 25
minscore = 0.4

[[stage]]
chkpt_file = "stage1.chkpt"
termination = "simple"
max_score = 0.7
min_steps = 25
max_steps = 500

[stage.scoring]
type = "geometric_mean"
filename = "stage1_scoring.toml"
filetype = "toml"
```

Required RL sections:

- `[parameters]`: `prior_file`, `agent_file`, `summary_csv_prefix`, `batch_size`, optional conditional `smiles_file`, and continuation controls.
- `[learning_strategy]`: `type = "dap"`, `sigma`, and `rate`. Lower `sigma` for conservative learning; higher `sigma` increases score pressure and divergence risk.
- `[[stage]]`: `max_steps` is required; `termination = "simple"` is the standard criterion. `min_steps` delays early termination until enough steps have run. `max_score` advances or stops when average score reaches the threshold.
- `[stage.scoring]`: inline components or an external scoring config. If `filename` is used, make it relative to the config working directory and include `filetype = "toml"` or `"json"`.

Conditional generator notes:

- LibInvent: set `prior_file`, `agent_file`, and `smiles_file` with one scaffold per line containing attachment points.
- LinkInvent: set `smiles_file` with two warheads per line separated by `|`.
- Mol2Mol/Pepinvent: set `smiles_file`, usually `sample_strategy = "multinomial"`, and a practical `distance_threshold`.
- Transformer-based generators force canonical/isomeric handling and may override `randomize_smiles = true` at runtime.

## Diversity filter and intrinsic penalty

Diversity controls prevent scaffold collapse. Use either a diversity filter or intrinsic penalty; a global `[diversity_filter]` takes precedence over `[intrinsic_penalty]`.

Recommended global diversity filter:

```toml
[diversity_filter]
type = "IdenticalMurckoScaffold"
bucket_size = 25
minscore = 0.4
minsimilarity = 0.4
penalty_multiplier = 0.5
```

Available diversity filter types:

- `IdenticalMurckoScaffold`: common default; penalizes overfilled identical Murcko scaffold buckets.
- `IdenticalTopologicalScaffold`: stricter topology-based scaffold memory.
- `ScaffoldSimilarity`: penalizes scaffolds above `minsimilarity` to existing bucket entries.
- `PenalizeSameSmiles`: penalizes repeated exact SMILES with `penalty_multiplier`.

Per-stage diversity filters can be placed under `[stage.diversity_filter]`, but a global `[diversity_filter]` overwrites stage-specific settings. If a curriculum needs different diversity behavior per stage, omit the global filter.

Intrinsic penalty shape:

```toml
[intrinsic_penalty]
type = "IdenticalMurckoScaffoldRND"
penalty_function = "Sigmoid"
bucket_size = 25
minscore = 0.4
learning_rate = 0.0001
```

Supported penalty functions are `Step`, `Sigmoid`, `Linear`, `Tanh`, and `Erf`. Treat intrinsic penalty as advanced; prefer the standard diversity filter unless the user explicitly requests novelty rewards.

## Inception memory

Inception is optional guidance from good seed molecules. It is most useful for Reinvent-style RL and early convergence.

```toml
[inception]
smiles_file = "good_seed_molecules.smi"
memory_size = 100
sample_size = 10
```

Rules of thumb:

- If `smiles_file` is omitted or not readable, the inception memory can populate from the first sampled batch, which is weaker guidance.
- Keep `sample_size` smaller than `memory_size` and much smaller than `batch_size`.
- Use seed molecules that are valid for the prior vocabulary; invalid seeds can fail setup.

## TL followed by staged RL

Use this when the user has both known relevant molecules and a scoring objective.

1. Prepare train/validation SMILES and run TL from the relevant prior.
2. Sample from the TL model and check valid SMILES, duplicate fraction, novelty, and resemblance to the training chemistry.
3. Validate scoring components with a scoring-only run or the scoring sub-skill before any RL.
4. Configure staged learning with the same generator type:

```toml
[parameters]
prior_file = "priors/reinvent.prior"
agent_file = "tl_agent.model"
summary_csv_prefix = "tl_then_rl"
```

5. Use a first stage with cheap structural/property filters and a second stage with stricter or expensive scoring:

```toml
[[stage]]
chkpt_file = "stage1.chkpt"
termination = "simple"
max_score = 0.6
min_steps = 25
max_steps = 200

[stage.scoring]
type = "geometric_mean"
filename = "stage1_scoring.toml"
filetype = "toml"

[[stage]]
chkpt_file = "stage2.chkpt"
termination = "simple"
max_score = 0.75
min_steps = 25
max_steps = 300

[stage.scoring]
type = "geometric_mean"
filename = "stage2_scoring.toml"
filetype = "toml"
```

Safety checks before running:

- `prior_file` and `agent_file` must load as the same model type; REINVENT4 raises an inconsistent model type error otherwise.
- Every `filename` under `[stage.scoring]` must exist relative to the run location.
- Use `--device cpu` when CUDA availability is uncertain.
- Confirm output filenames do not overwrite a valuable model, checkpoint, or CSV from a previous campaign.
