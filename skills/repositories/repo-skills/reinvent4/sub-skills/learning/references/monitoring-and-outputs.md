# Monitoring and Outputs

REINVENT4 learning runs produce TensorBoard logs, model/checkpoint files, regular logs, and for staged learning one CSV per stage. Use these outputs to decide whether a TL/RL run is healthy before continuing to later workflow steps.

## TensorBoard configuration

Set `tb_logdir` at the top level of the config, next to `run_type` and `device`:

```toml
run_type = "staged_learning"
device = "cpu"
tb_logdir = "tb_RL"
```

Then launch:

```bash
tensorboard --logdir tb_RL
```

For staged learning, REINVENT4 appends the zero-based stage index to the directory passed to the runner, producing directories such as `tb_RL_0`, `tb_RL_1`, and `tb_RL_2`. For transfer learning, event files are written directly under the configured TL log directory.

## Transfer learning outputs

Primary files:

- `output_model_file`: the final trained agent model.
- Intermediate checkpoints: written according to `save_every_n_epochs` and useful for selecting an earlier epoch.
- TensorBoard event files: loss curves, validity/duplicate/diversity signals, sampled molecule images, and optional similarity plots.
- Optional JSON config output: if `json_out_config` is present, REINVENT4 writes a serialized form of the resolved config.

TL TensorBoard signals to inspect:

- `A_Mean NLL loss / Training Loss`: should generally decrease.
- `A_Mean NLL loss / Sample Loss`: should track training loss; a widening gap can indicate overfitting.
- `A_Mean NLL loss / Validation Loss`: requires `validation_smiles_file`; use it to choose a checkpoint.
- `B_Fraction valid SMILES`: low validity means the agent drifted too far from the prior.
- `C_Fraction duplicate SMILES`: rising duplication suggests memorization or low diversity.
- `D_Internal Diversity of sample`: should not collapse during focused training.
- `E_Average iSIM similarity`: available when iSIM tracking is enabled.

Post-TL review checklist:

1. Confirm the output model and checkpoint files exist.
2. Sample from the TL model before RL; check valid rate, duplicate rate, and chemistry resemblance.
3. Prefer a checkpoint with good validation loss and acceptable diversity over the final epoch if overfitting is visible.
4. Preserve the original prior; do not overwrite it with TL output.

## Staged learning outputs

Primary files:

- Stage checkpoint files from each `chkpt_file` and also on graceful interruption via Ctrl-C.
- Stage CSV files named from `summary_csv_prefix` and stage number, for example `rl_run_1.csv`, `rl_run_2.csv`.
- TensorBoard stage directories such as `tb_RL_0` and `tb_RL_1`.
- Main log file if `--log-filename` is supplied to `reinvent`.
- Optional remote responder events when `[responder]` is configured and environment variables are available.

RL CSV columns:

- `Agent`: negative log-likelihood assigned by the current agent.
- `Prior`: negative log-likelihood assigned by the fixed prior.
- `Target`: augmented NLL used by the DAP objective.
- `Score`: total aggregated score after scoring and penalties.
- `SMILES`: generated molecule.
- `SMILES_state`: validity state (`1` valid, `2` duplicate, `3` invalid).
- Conditional generator inputs: `Input_Scaffold` and `R-groups` for LibInvent, `Warheads` and `Linker` for LinkInvent, `Input_SMILES` for Mol2Mol, and peptide-specific input/filler columns for Pepinvent.
- `Scaffold`: present when a diversity filter records scaffold memory.
- Component pairs: `<component name>` and `<component name> (raw)` for transformed and raw values.
- Metadata columns: `<metadata key> (<component name>)` when a scoring component returns auxiliary metadata.
- `step`: RL step/epoch index.

RL TensorBoard signals to inspect:

- `Loss`: DAP training objective.
- `Loss (likelihood averages) / prior NLL`, `agent NLL`, `augmented NLL`: agent and prior should not diverge rapidly.
- `Average total score`: should increase and eventually plateau.
- `Fraction of valid SMILES`: low values imply invalid generation or incompatible conditional inputs.
- `Fraction of duplicate SMILES`: spikes can indicate mode collapse.
- Component scalar names and raw values: stuck-zero components usually mean bad transforms, impossible filters, or broken scoring inputs.
- `Number of unique scaffolds`: should not collapse when diversity is desired.
- `Number of scaffolds found more than N times`: high values imply overfilled diversity buckets.
- `iSIM: Average similarity`: optional diversity trend when `tb_isim = true`.

## Continuation and checkpointing

- To continue RL manually, set `[parameters].agent_file` to a previous stage checkpoint and keep `prior_file` as the original compatible prior.
- Set `use_checkpoint = true` only when the checkpoint contains a staged-learning diversity filter state that should be reused.
- `purge_memories = true` clears diversity filter memories after each stage; set `false` when cross-stage memory should suppress rediscovery.
- Checkpoint names should be unique per stage to avoid overwriting state needed for recovery or analysis.

## Review thresholds

Use these as qualitative gates rather than hard scientific guarantees:

- TL is suspicious if validation loss rises while training loss falls, valid SMILES drops below about 90%, or duplicate fraction rises sharply.
- RL is suspicious if `Score` plateaus near zero, all molecules become duplicates, agent NLL moves far from prior NLL quickly, or a hard filter component is always zero.
- Curriculum stages should have achievable `max_score` thresholds. If stage 1 never reaches `max_score`, stage 2 will never start unless `max_steps` terminates the entire run.
- Expensive scoring stages should be preceded by a cheaper dry-run stage or scoring-only validation on representative SMILES.
