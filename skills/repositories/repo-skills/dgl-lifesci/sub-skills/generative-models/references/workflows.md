# Generative Model Workflows

Use this reference to plan DGL-LifeSci molecular generation tasks without copying or running the original long example scripts. Treat the source train/eval/pretrain scripts as evidence for argument contracts and expected outputs, not as bundled runtime helpers.

## Workflow Selection

| User goal | Prefer | Why | Route away when |
| --- | --- | --- | --- |
| Generate molecules directly as atom/bond graph decisions | DGMG | `DGMG` models an autoregressive graph-building process over atom and bond types. | The user needs molecule reconstruction from an input molecule or latent-space VAE sampling. |
| Reconstruct molecules or sample from a latent chemical space | JTVAE/JTNNVAE | `JTNNVAE` encodes a molecular graph plus junction tree and decodes through vocabulary tokens. | The user only needs graph featurizers, supervised predictors, or generic pretrained GNNs. |
| Validate tiny input files before a generative run | Bundled validator | It checks RDKit parseability, duplicates, and optional JTVAE vocabulary coverage without training. | The user needs full molecule cleaning, labels, graph feature matrices, or splits. |

## DGMG Planning

Verified public constructor:

```python
from rdkit import Chem
from dgllife.model import DGMG

model = DGMG(
    atom_types=['O', 'Cl', 'C', 'S', 'F', 'Br', 'N'],
    bond_types=[Chem.rdchem.BondType.SINGLE,
                Chem.rdchem.BondType.DOUBLE,
                Chem.rdchem.BondType.TRIPLE],
    node_hidden_size=128,
    num_prop_rounds=2,
    dropout=0.2,
)
```

Important call modes:

- `model(actions=decision_sequence, compute_log_prob=True)` returns log likelihood for a teacher-forced DGMG decision sequence.
- `model(actions=decision_sequence, rdkit_mol=True)` returns the generated SMILES for a known decision sequence.
- `model(rdkit_mol=True, max_num_steps=400)` samples from the model and returns a SMILES string when generation succeeds.
- `model(rdkit_mol=False)` can return `None`; ask for `rdkit_mol=True` when the user needs generated molecules.

DGMG dataset planning:

1. Start from train/validation text files with one SMILES per line.
2. Validate parseability and duplicates with `scripts/validate_generative_inputs.py`.
3. Determine atom symbols and RDKit bond types represented in the training/validation set.
4. Document known limitations before training: protonation and chirality can be ignored; charged nitro fragments may be transformed or filtered; very large molecules make generation slow.
5. For custom data, plan preprocessing that standardizes molecules, checks whether DGMG can reproduce canonical/random decision sequences, and writes processed `*_DGMG_train.txt`, `*_DGMG_val.txt`, and `*_atom_and_bond_types.pkl`-style artifacts in a project-owned output directory.

DGMG example-style arguments to preserve when adapting a project script:

| Purpose | Argument pattern | Notes |
| --- | --- | --- |
| Train on built-in datasets | `-d ChEMBL|ZINC -o random|canonical` | Built-in dataset use may download files. |
| Train on custom data | `-d NAME -o random|canonical -tf train.txt -vf val.txt` | Train and validation files are required. |
| Parallel CPU training | `-np NUM_PROCESSES` | Source examples default to many processes; reduce for local smoke checks. |
| Evaluation with checkpoint | `-d NAME -o ORDER -p checkpoint.pth` | Checkpoint should hold a `model_state_dict`. |
| Evaluation with pretrained DGMG | `-d ZINC -o canonical -pr` | First use may download a checkpoint. |
| Generation limits | `-ns NUM_SAMPLES -mn MAX_NUM_STEPS -gt SECONDS` | Keep `num_samples` tiny for smoke tests. |

DGMG outputs to expect:

- Training logs and settings under a run directory.
- Best validation checkpoint, commonly `checkpoint.pth` with `model_state_dict`.
- Evaluation `generated_smiles.txt` and `generation_stats.txt` containing validity, uniqueness among valid molecules, and novelty among unique molecules.
- Optional visualizations/notebooks are not required for a runtime agent workflow.

## JTVAE/JTNNVAE Planning

Verified public constructor:

```python
from dgllife.model import JTNNVAE
from dgllife.utils import JTVAEVocab

vocab = JTVAEVocab(file_path='train_smiles.txt')
model = JTNNVAE(vocab, hidden_size=450, latent_size=56, depth=3, stereo=True)
```

Core data/API surfaces:

- `JTVAEVocab(file_path=None)` loads the default DGL-LifeSci JTVAE vocabulary, which can trigger a dataset download.
- `JTVAEVocab(file_path='train.txt')` derives vocabulary tokens from MolTree decomposition of one-SMILES-per-line training data.
- `JTVAEDataset(data_file, vocab, cache=False, training=True)` builds MolTree/molecular graph items from a SMILES file.
- `JTVAEZINC('train'|'test', vocab, cache=False)` uses the bundled ZINC subset and can download data.
- `JTVAECollator(training=True|False)` batches training or reconstruction/evaluation data.
- `JTNNVAE(...).reset_parameters()` initializes weights before training from scratch.
- `JTNNVAE(...).reconstruct(tree_graph, mol_graph, prob_decode=False)` reconstructs from prepared non-training dataset items.
- `JTNNVAE(...).sample_prior(prob_decode=False)` samples one molecule from the prior; `sample_eval()` repeats stochastic decoding from one latent draw.

JTVAE two-phase training plan:

1. Build or select a vocabulary from the same training distribution that will be used for the model.
2. Pretrain without KL regularization to a `pre_model/model.iter-*` checkpoint.
3. Continue VAE training from a pretraining checkpoint, with KL weight `beta`/`-z` controlling reconstruction/diversity trade-off.
4. Reconstruct with a matching checkpoint, vocabulary, `hidden_size`, `latent_size`, `depth`, and stereo flag.
5. Keep batch size and workers low for smoke checks; full runs are long and may require GPU.

JTVAE example-style arguments to preserve when adapting a project script:

| Purpose | Argument pattern | Notes |
| --- | --- | --- |
| Pretrain from custom SMILES | `pretrain.py -tr train.txt -s pre_model` | `JTVAEVocab(file_path=train.txt)` derives tokens from training data. |
| VAE train from checkpoint | `vaetrain.py -tr train.txt -m pre_model/model.iter-2 -s vae_model -z 0.001` | Check hyperparameters match the checkpoint. |
| Reconstruct custom test file | `reconstruct.py -tr train.txt -te test.txt -m vae_model/model.iter-6` | Training path provides vocabulary; test path provides reconstruction inputs. |
| CPU smoke run | add `-cpu -nw 0 -b SMALL -me 1` | Use only for plumbing validation, not model quality. |
| Default ZINC/pretrained | omit custom paths where supported | May download dataset/vocab/checkpoints. Ask before networked runs. |

JTVAE outputs to expect:

- Pretraining checkpoints under `pre_model/model.iter-*`.
- VAE checkpoints under `vae_model/model.iter-*` or `model.iter-EPOCH-ITER`.
- Reconstruction logs with running and final accuracy.
- Generated samples from model methods can be `None` when decoding or sanitization fails; downstream code must filter invalid outputs.

## Safe Execution Classes

| Class | Examples | Default stance |
| --- | --- | --- |
| Safe offline validation | Run the bundled input validator on a small text/vocab fixture; instantiate tiny `DGMG` or `JTNNVAE` constructors if dependencies are installed. | Safe to run when the user provided files or synthetic fixtures. |
| Network/download dependent | `JTVAEVocab()` with no file, `JTVAEZINC`, `load_pretrained('DGMG_ZINC_canonical')`, default reconstruction with pretrained JTVAE. | Ask before running; document cache/output directory. |
| Long-running training/eval | DGMG train/eval with many processes or 100k samples; JTVAE pretrain/VAE train; full reconstruction over ZINC. | Do not launch without explicit approval, resource bounds, and output location. |
| Reference-only source scripts | Original example `train.py`, `eval.py`, `pretrain.py`, `vaetrain.py`, `reconstruct.py`, and DGMG SA scoring utility. | Use as design evidence; adapt only the small relevant contract into project-owned scripts. |

## Minimal Smoke Checks

DGMG constructor/teacher-forcing smoke idea:

```python
from rdkit import Chem
from dgllife.model import DGMG

model = DGMG(
    atom_types=['O', 'Cl', 'C', 'S', 'F', 'Br', 'N'],
    bond_types=[Chem.rdchem.BondType.SINGLE, Chem.rdchem.BondType.DOUBLE, Chem.rdchem.BondType.TRIPLE],
    node_hidden_size=1,
    num_prop_rounds=1,
)
assert model(actions=[(0, 2), (1, 3), (0, 0), (1, 0), (2, 0), (1, 3), (0, 7)], rdkit_mol=True) == 'CO'
```

JTVAE constructor/vocabulary smoke idea:

```python
from dgllife.model import JTNNVAE
from dgllife.utils import JTVAEVocab

vocab = JTVAEVocab(file_path='tiny_train.txt')
model = JTNNVAE(vocab, hidden_size=1, latent_size=2, depth=3)
```

Use the validator first when `tiny_train.txt` comes from a user. If the task needs graph featurizer or dataset shape debugging beyond JTVAE-specific fields, route to `molecule-data-prep`.
