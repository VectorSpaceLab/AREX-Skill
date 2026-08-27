# Reversible OGB proteins and optional DGL RevGAT

## RevGNN proteins path

The efficient proteins model is selected with `--backbone rev` and uses
`RevGCN`, a stack of invertible group-additive coupling layers. The documented
parser defaults are:

```text
--dataset ogbn-proteins --cluster_number 10 --valid_cluster_number 5
--aggr add --nf_path init_node_features_add.pt
--backbone rev --group 2 --num_layers 3 --num_steps 3
--mlp_layers 2 --hidden_channels 64 --block plain --conv gen
--gcn_aggr max --norm layer --epochs 2000 --lr 0.01 --dropout 0.0
--num_evals 1 --use_gpu (off unless supplied)
```

The reversible model also accepts `--conv_encode_edge`,
`--use_one_hot_encoding`, `--msg_norm`, `--learn_msg_scale`, `--t`, `--p`,
`--y`, and their learnable switches. The command blocks below are argument
shapes for an independently staged implementation, not instructions to open or
run the original checkout. The documented large configurations are:

```bash
# RevGNN-Wide: documented 448 layers x 224 channels
python <ogb-task-entrypoint> --use_gpu --conv_encode_edge --use_one_hot_encoding \
  --block res+ --gcn_aggr max --num_layers 448 --hidden_channels 224 \
  --lr 0.001 --backbone rev --dropout 0.2 --group 2

# RevGNN-Deep: documented 1001 layers x 80 channels
python <ogb-task-entrypoint> --use_gpu --conv_encode_edge --use_one_hot_encoding \
  --block res+ --gcn_aggr max --num_layers 1001 --hidden_channels 80 \
  --lr 0.001 --backbone rev --dropout 0.1 --group 2
```

Do not execute these as validation. They require the full proteins dataset,
feature cache, compatible CUDA/PyG extensions, and substantial GPU memory.

### Shape and feature invariants

1. `hidden_channels % group == 0`; the coupling splits node state into
   `group` chunks of width `hidden_channels / group`.
2. Each coupling branch is a `GENBlock` operating on one chunk. Its edge
   feature dimension is `hidden_channels`.
3. The model loads `--nf_path`, normally an 8-wide edge-aggregated node
   feature tensor. Without `--use_one_hot_encoding`, it projects width 8 to
   `hidden_channels`; with it, an 8-wide species projection is concatenated,
   and the input projection expects width 16.
4. Raw protein edge attributes are width 8 and are linearly encoded to
   `hidden_channels`. The reversible path repeats that encoded edge embedding
   `group` times, then the coupling implementation chunks it per branch.
5. The coupling wrapper is called with node state, `edge_index`, a shared
   dropout mask, and edge embeddings. Extra tensor arguments must have a
   feature dimension divisible by `group` and must be chunked consistently.
6. The wrapper reconstructs activations during backward. `num_bwd_passes=1`
   is the intended default; extra backward passes need an explicit increase.
   Stochastic branches require RNG preservation if exact reconstruction is
   needed; otherwise use deterministic branch behavior.

The reference test path generates the evaluation partitions once, averages
predictions over `--num_evals`, reports ROC-AUC, and loads the same
`model_state_dict` checkpoint format. The README documents 448-layer and
1001-layer ROC-AUC values and memory recommendations (32 GB for single-view
runs, 48 GB for the 448-layer multi-view example). These are **documented
results**, not verified here. The bundled smoke can only validate a tiny
coupling-style tensor operation; it does not profile RevGNN memory.

## Optional DGL RevGAT arxiv path

This is a separate implementation using DGL graph storage and a custom RevGAT.
It requires DGL, OGB's DGL dataset adapter, a CUDA-capable PyTorch/DGL pair,
and the full `ogbn-arxiv` graph. The selected inspection environment omitted
DGL, so this route is optional and unverified. Only run its parser/help check
after explicitly preparing that backend; never install it or download data from
this skill.

Relevant exact parser flags include:

```text
--cpu --gpu INT --seed INT --n-runs INT --n-epochs INT
--use-labels --n-label-iters INT --mask-rate FLOAT
--no-attn-dst --use-norm --lr FLOAT --n-layers INT --n-heads INT
--n-hidden INT --dropout FLOAT --input-drop FLOAT --attn-drop FLOAT
--edge-drop FLOAT --wd FLOAT --log-every INT --plot-curves --save-pred
--save NAME --backbone rev --group INT --kd_dir PATH
--mode {teacher,student} --alpha FLOAT --temp FLOAT
```

Teacher and student argument shapes from the documentation are shown below; they
are not instructions to open or run the original checkout:

```bash
# teacher: writes best predictions under --kd_dir
python <dgl-task-entrypoint> --use-norm --use-labels --n-label-iters=1 \
  --no-attn-dst --edge-drop=0.3 --input-drop=0.25 --n-layers 5 \
  --dropout 0.75 --n-hidden 256 --save kd --backbone rev --group 2 \
  --mode teacher

# student: consumes teacher prediction artifacts from --kd_dir
python <dgl-task-entrypoint> --use-norm --use-labels --n-label-iters=1 \
  --no-attn-dst --edge-drop=0.3 --input-drop=0.25 --n-layers 5 \
  --dropout 0.75 --n-hidden 256 --save kd --backbone rev --group 2 \
  --alpha 0.95 --temp 0.7 --mode student
```

Teacher mode saves `best_pred_run<N>.pt`; student mode loads the matching run
from `--kd_dir`. `--n-label-iters > 0` requires `--use-labels`. The model uses
`n_heads=3` by default, so intermediate hidden width is `n_heads * n_hidden`;
that width must remain compatible with `group`. `--edge-drop` and dropout
increase reproducibility and memory sensitivity. The README's teacher and
student accuracy averages are **documented results** only; no DGL path is
verified by the tiny CPU smoke.
