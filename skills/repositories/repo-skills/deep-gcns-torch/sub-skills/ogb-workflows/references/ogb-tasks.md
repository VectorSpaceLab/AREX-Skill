# OGB task matrix and commands

These are distilled command contracts. They are reference-only: commands may
read OGB data and external checkpoints and may run for hours. Do not execute
them as a smoke test. The command blocks below are argument shapes for an
independently staged implementation, not instructions to open or run the
original checkout.

## Common DeeperGCN controls

All PyG task parsers expose some subset of these exact flags:

```text
--use_gpu --device INT --epochs INT --lr FLOAT --dropout FLOAT
--num_layers INT --mlp_layers INT --hidden_channels INT
--block {plain,res,res+[,dense]} --conv gen
--gcn_aggr {max,mean,add,softmax,softmax_sg,softmax_sum,power,power_sum}
--norm NAME --t FLOAT --p FLOAT --y FLOAT
--learn_t --learn_p --learn_y --msg_norm --learn_msg_scale
--model_save_path PATH --save NAME --model_load_path PATH
```

The accepted aggregator list varies slightly by task parser; use the list
printed by that task's `--help`, not a copied list from another task. The live
GENConv supports `max`, `mean`, `add`, `softmax`, `softmax_sg`, and `power` in
the verified CPU API checks. `softmax_sum` and `power_sum` are exposed by
some historical task documentation but require matching implementation support.

### Live GENConv API defaults

The inspected sparse API constructor is:

```text
GENConv(in_dim, emb_dim, aggr='softmax', t=1.0, learn_t=False,
        p=1.0, learn_p=False, y=0.0, learn_y=False,
        msg_norm=False, learn_msg_scale=True, encode_edge=False,
        bond_encoder=False, edge_feat_dim=None, norm='batch',
        mlp_layers=2, eps=1e-7)
```

These are **API** defaults. The OGB task models override several of them from
CLI arguments: task defaults commonly use `gcn_aggr=max`, `mlp_layers=1` or
`2`, task-selected `norm`, and `learn_msg_scale=False` unless its flag is
supplied. Molecular models set `bond_encoder=True` and pass categorical edge
attributes when edge encoding is enabled; protein models pass an explicit edge
feature width for encoded edges.

## Node classification

| Dataset | Data path | Parser defaults and semantics | Metric |
|---|---|---|---|
| `ogbn-arxiv` | One graph, full-batch train/eval; edges are made undirected and optional self-loops are added with `--self_loop` | `--block res+ --conv gen --gcn_aggr max --num_layers 3 --mlp_layers 1 --hidden_channels 128 --norm batch --epochs 500 --lr 0.001 --dropout 0.5 --use_gpu` off | OGB accuracy |
| `ogbn-products` | Random node assignment to `--cluster_number` induced subgraphs; documented default is 10, one subgraph per optimization step; full-batch CPU test | Same core defaults as arxiv, with `--cluster_number 10`; `--self_loop` is optional | OGB accuracy |
| `ogbn-proteins` | Random induced partitions; defaults are 10 training clusters and 5 validation/test clusters, one subgraph at a time; node inputs come from edge features | `--aggr add --cluster_number 10 --valid_cluster_number 5 --block plain --norm layer --hidden_channels 64 --mlp_layers 2 --epochs 1000 --dropout 0.0`; edge and species flags below | OGB ROC-AUC |

Useful documented configurations:

```bash
# arxiv ResGEN (long GPU training; not a smoke)
python <ogb-task-entrypoint> --use_gpu --self_loop --num_layers 28 --block res+ \
  --gcn_aggr softmax_sg --t 0.1

# products partitioned ResGEN
python <ogb-task-entrypoint> --use_gpu --self_loop --num_layers 14 \
  --gcn_aggr softmax_sg --t 0.1

# proteins edge-aware DyResGEN
python <ogb-task-entrypoint> --use_gpu --conv_encode_edge --use_one_hot_encoding \
  --num_layers 112 --block res+ --gcn_aggr softmax --t 1.0 --learn_t \
  --dropout 0.1
```

`ogbn-proteins` adds `--conv_encode_edge`, `--use_one_hot_encoding`,
`--aggr {mean,max,add}`, `--nf_path PATH`, and `--num_evals INT`. Its
non-reversible model consumes an 8-wide edge-derived node feature file; with
one-hot species features it concatenates another 8-wide projection before the
node encoder. `ogbn-arxiv` and `ogbn-products` encode the dataset's numeric
node feature matrix with `--in_channels` inferred at runtime.

## Graph property prediction

### Molecular graphs: `ogbg-molhiv` and `ogbg-molpcba`

Use PyG graph batches with `--batch_size 32`, `--num_workers 0`,
`--feature {full,simple}`, `--conv_encode_edge`, `--add_virtual_node`, and
`--graph_pooling {mean,max,sum}`. Default model settings are
`--dataset ogbg-molhiv --block res+ --conv gen --gcn_aggr max
--num_layers 3 --mlp_layers 1 --hidden_channels 256 --norm batch
--epochs 300 --lr 0.01 --dropout 0.5 --graph_pooling mean`.

`--feature simple` retains only the first two node and edge feature columns;
`full` retains the dataset categorical matrices. `AtomEncoder` embeds the OGB
categorical node attributes. If `--conv_encode_edge` is absent, `BondEncoder`
embeds edge attributes; if it is present, the GENConv edge path receives the
raw categorical edge attributes and the model enables its bond encoder. A
virtual node is a learned zero-initialized graph embedding updated by an MLP
and broadcast to nodes between layers.

Documented long configurations are:

```bash
# molhiv DyResGEN
python <ogb-task-entrypoint> --use_gpu --conv_encode_edge --num_layers 7 \
  --dataset ogbg-molhiv --block res+ --gcn_aggr softmax --t 1.0 \
  --learn_t --dropout 0.2 --lr 0.0001

# molpcba ResGEN with virtual nodes
python <ogb-task-entrypoint> --use_gpu --conv_encode_edge --add_virtual_node \
  --mlp_layers 2 --num_layers 14 --dataset ogbg-molpcba --block res+ \
  --gcn_aggr softmax_sg --t 0.1
```

The evaluator uses the dataset's configured metric and masks NaN labels for
multi-task molecular prediction; do not replace this with plain accuracy.

### `ogbg-ppa`

This graph classification path defaults to `--batch_size 32`,
`--aggr add`, `--block res+`, `--norm layer`, `--hidden_channels 128`,
`--mlp_layers 2`, `--epochs 200`, `--lr 0.01`, `--dropout 0.5`, and
`--graph_pooling mean`. `--aggr {mean,max,add}` controls node initialization
by aggregating connected edge attributes. `--not_extract_node_feature`
replaces that transform with zero node features. The documented 28-layer
configuration is:

```bash
python <ogb-task-entrypoint> --use_gpu --conv_encode_edge --num_layers 28 \
  --gcn_aggr softmax_sg --t 0.01
```

Its evaluator reports classification accuracy. For deep models,
`--num_layers_threshold 14` and `--eval_steps 5` reduce evaluation frequency.

## Link prediction: `ogbl-collab`

The node encoder defaults to `--in_channels 128 --hidden_channels 128`,
`--num_layers 3`, `--block res+`, `--conv gen`, `--gcn_aggr max`,
`--norm batch`, `--dropout 0.0`, and `--self_loop` off. The link predictor
adds `--lp_num_layers 3 --lp_norm none`; it scores an edge by elementwise
multiplying endpoint embeddings, passing the product through an MLP, and
applying sigmoid. `--batch_size` is **65536 edges** (`64 * 1024`), not graph
examples. The evaluator reports Hits@10, Hits@50, and Hits@100 from positive
and negative edge scores.

The training checkpoint convention saves the encoder and predictor separately:
`<name>_valid_best.pth` and `<name>_valid_best_link_predictor.pth` under the
configured save directory. Load both and keep `--hidden_channels`, layer counts,
normalization, and predictor flags aligned.

## Routing boundaries

Generic GENConv/layer construction and reversible primitive APIs belong to
[graph-layers](../../graph-layers/SKILL.md). PPI is a different node-label
workflow with F1 metrics; use [ppi-workflows](../../ppi-workflows/SKILL.md).
Point clouds are not OGB graph batches; use [point-cloud-workflows](../../point-cloud-workflows/SKILL.md).
