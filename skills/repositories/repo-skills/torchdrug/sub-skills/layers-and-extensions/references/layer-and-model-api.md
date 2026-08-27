# Layer and Model API Reference

This reference summarizes public TorchDrug layer/model entry points, aliases, and parameter choices for architecture selection. It is self-contained; verify local installation details with `../scripts/inspect_layers.py` when needed.

## Import Map and Aliases

Use `from torchdrug import layers, models` for the public aliases below.

| Family | Preferred public names | Aliases | Use when |
| --- | --- | --- | --- |
| GCN | `models.GraphConvolutionalNetwork`, `layers.GraphConv` | `models.GCN`, `layers.GCNConv` | Homogeneous graph convolution with optional edge features. |
| GAT | `models.GraphAttentionNetwork`, `layers.GraphAttentionConv` | `models.GAT` | Attention-weighted neighbor aggregation. |
| GIN | `models.GraphIsomorphismNetwork`, `layers.GraphIsomorphismConv` | `models.GIN`, `layers.GINConv` | Strong molecular graph baseline and WL-style aggregation. |
| RGCN | `models.RelationalGraphConvolutionalNetwork`, `layers.RelationalGraphConv` | `models.RGCN`, `layers.RGCNConv` | Multi-relation graphs with `edge_list[:, 2]` relation ids. |
| MPNN | `models.MessagePassingNeuralNetwork`, `layers.MessagePassing` | `models.MPNN`, `layers.MPConv` | Edge-conditioned molecular message passing requiring edge features. |
| SchNet | `models.SchNet`, `layers.ContinuousFilterConv` | `layers.CFConv` | Continuous-filter/geometric messages with distance-like edge features. |
| ChebNet | `models.ChebyshevConvolutionalNetwork`, `layers.ChebyshevConv` | `models.ChebNet` | Chebyshev polynomial graph convolutions with order `k`. |
| NeuralFP | `models.NeuralFingerprint`, `layers.NeuralFingerprintConv` | `models.NFP`, `layers.NFPConv` | Neural fingerprint-style molecular features. |
| GearNet | `models.GeometryAwareRelationalGraphNeuralNetwork`, `layers.GeometricRelationalGraphConv` | `models.GearNet` | Protein residue graphs with relation and optional angle geometry. |
| GraphAF | `models.GraphAutoregressiveFlow` | `models.GraphAF` | Autoregressive molecular graph flow using a base representation model and prior. |
| InfoGraph | `models.InfoGraph`, `models.MultiviewContrast` | none | Self-supervised graph representation losses around another model. |
| Knowledge graph | `models.TransE`, `models.DistMult`, `models.ComplEx`, `models.RotatE`, `models.SimplE`, `models.NeuralLogicProgramming`, `models.KBGAT` | `models.NeuralLP` | Knowledge-graph completion/reasoning. |
| Protein sequence | `models.ProteinConvolutionalNetwork`, `models.ProteinResNet`, `models.ProteinLSTM`, `models.ProteinBERT`, `models.EvolutionaryScaleModeling` | `models.ProteinCNN`, `models.ESM` | Protein sequence/residue representation before task heads. |

## Convolution Layer Constructors

- `layers.MessagePassingBase.forward(graph, input)` calls `message_and_aggregate(graph, input)` and then `combine(input, update)`.
- `layers.GraphConv(input_dim, output_dim, edge_input_dim=None, batch_norm=False, activation="relu")` adds self-loops and optionally linearly projects `graph.edge_feature` when `edge_input_dim` is set.
- `layers.GraphAttentionConv(input_dim, output_dim, edge_input_dim=None, num_head=1, negative_slope=0.2, concat=True, batch_norm=False, activation="relu")` requires `output_dim % num_head == 0`.
- `layers.GraphIsomorphismConv(input_dim, output_dim, edge_input_dim=None, hidden_dims=None, eps=0, learn_eps=False, batch_norm=False, activation="relu")` uses an MLP after summing neighbor/self messages.
- `layers.RelationalGraphConv(input_dim, output_dim, num_relation, edge_input_dim=None, batch_norm=False, activation="relu")` asserts `graph.num_relation == num_relation` and aggregates relation-specific channels.
- `layers.GeometricRelationalGraphConv(input_dim, output_dim, num_relation, edge_input_dim=None, batch_norm=False, activation="relu")` is the GearNet-adjacent relational layer variant.
- `layers.MessagePassing(input_dim, edge_input_dim, hidden_dims=None, batch_norm=False, activation="relu")` is edge-conditioned and keeps `output_dim == input_dim`.
- `layers.ContinuousFilterConv(input_dim, output_dim, edge_input_dim=None, hidden_dim=None, cutoff=5, num_gaussian=100, batch_norm=False, activation="shifted_softplus")` is SchNet-style and expects usable edge distances/features.
- `layers.ChebyshevConv(input_dim, output_dim, edge_input_dim=None, k=1, batch_norm=False, activation="relu")` concatenates Chebyshev orders up to `k` before a linear projection.

## Representation Model Constructors

All graph representation models below are `nn.Module` + `core.Configurable` and use `forward(graph, input, all_loss=None, metric=None)` unless noted. They return a dictionary containing at least `node_feature` and usually `graph_feature`.

- `models.GCN(input_dim, hidden_dims, edge_input_dim=None, short_cut=False, batch_norm=False, activation="relu", concat_hidden=False, readout="sum")` stacks `layers.GraphConv`; `readout` is `"sum"` or `"mean"`.
- `models.GAT(input_dim, hidden_dims, edge_input_dim=None, num_head=1, negative_slope=0.2, short_cut=False, batch_norm=False, activation="relu", concat_hidden=False, readout="sum")` stacks `layers.GraphAttentionConv`; each hidden dimension must divide cleanly by `num_head`.
- `models.GIN(input_dim, hidden_dims, edge_input_dim=None, num_mlp_layer=2, eps=0, learn_eps=False, short_cut=False, batch_norm=False, activation="relu", concat_hidden=False, readout="sum")` stacks `layers.GraphIsomorphismConv`; often a strong molecular default.
- `models.RGCN(input_dim, hidden_dims, num_relation, edge_input_dim=None, short_cut=False, batch_norm=False, activation="relu", concat_hidden=False, readout="sum")` stacks `layers.RelationalGraphConv`; pass `num_relation=graph.num_relation`.
- `models.MPNN(input_dim, hidden_dim, edge_input_dim, num_layer=1, num_gru_layer=1, num_mlp_layer=2, num_s2s_step=3, short_cut=False, batch_norm=False, activation="relu", concat_hidden=False)` uses edge-conditioned messages, GRU updates, and Set2Set graph readout; `output_dim` is twice the node feature dimension used by Set2Set.
- `models.SchNet(input_dim, hidden_dims, edge_input_dim=None, cutoff=5, num_gaussian=100, short_cut=True, batch_norm=False, activation="shifted_softplus", concat_hidden=False)` uses continuous-filter convolutions and sum readout.
- `models.ChebNet(input_dim, hidden_dims, edge_input_dim=None, k=1, short_cut=False, batch_norm=False, activation="relu", concat_hidden=False, readout="sum")` stacks Chebyshev convolutions.
- `models.GearNet(input_dim, hidden_dims, num_relation, edge_input_dim=None, num_angle_bin=None, short_cut=False, batch_norm=False, activation="relu", concat_hidden=False, readout="sum")` uses geometric relational convolutions; when `num_angle_bin` is not `None`, it also builds edge updates from spatial line graphs.

## Other Model Families

- `models.GraphAF(model, prior, use_edge=False, num_layer=6, num_mlp_layer=2, dequantization_noise=0.9)` wraps a representation model for autoregressive graph flows; when `use_edge=True`, calls require an `edge` argument.
- `models.InfoGraph(model, num_mlp_layer=2, activation="relu", loss_weight=1, separate_model=False)` adds graph-node or distillation mutual-information losses through `all_loss` / `metric`.
- `models.MultiviewContrast(model, crop_funcs, noise_funcs, num_mlp_layer=2, activation="relu", tau=0.07)` applies paired graph transforms and contrastive loss around a base model.
- `models.TransE(num_entity, num_relation, embedding_dim, max_score=12)`, `models.DistMult(num_entity, num_relation, embedding_dim, l3_regularization=0)`, `models.ComplEx(...)`, `models.RotatE(...)`, and `models.SimplE(...)` score `(h_index, t_index, r_index)` knowledge-graph triples.
- `models.NeuralLP(num_relation, hidden_dim, num_step, num_lstm_layer=1)` performs neural logic programming over relation graphs.
- `models.KBGAT(num_entity, num_relation, embedding_dim, hidden_dims, max_score=12, **kwargs)` extends GAT-like representations for knowledge graphs.
- `models.ProteinCNN(input_dim, hidden_dims, kernel_size=3, stride=1, padding=1, activation="relu", short_cut=False, concat_hidden=False, readout="max")` and `models.ProteinResNet(..., activation="gelu", readout="attention")` encode residue sequences.
- `models.ProteinLSTM(input_dim, hidden_dim, num_layers, activation="tanh", layer_norm=False, dropout=0)` returns sequence/residue features.
- `models.ProteinBERT(input_dim, hidden_dim=768, num_layers=12, num_heads=12, intermediate_dim=3072, activation="gelu", hidden_dropout=0.1, attention_dropout=0.1, max_position=8192)` is a transformer-style protein encoder.
- `models.ESM(path, model="ESM-1b", readout="mean")` wraps a local FAIR-ESM checkpoint path; avoid triggering downloads in agent workflows.

## Readouts, Samplers, and Graph Construction

- `layers.MeanReadout(type="node")`, `layers.SumReadout(type="node")`, and `layers.MaxReadout(type="node")` reduce node, edge, or residue features by `node2graph`, `edge2graph`, or `residue2graph`.
- `layers.AttentionReadout(input_dim, type="node")` learns scalar attention weights before summing per graph.
- `layers.Set2Set(input_dim, type="node", num_step=3, num_lstm_layer=1)` returns graph features with dimension `2 * input_dim`.
- `layers.Softmax(type="node")` and `layers.Sort(type="node", descending=False)` operate independently within each graph in a packed batch.
- `layers.NodeSampler(budget=None, ratio=None)` and `layers.EdgeSampler(budget=None, ratio=None)` implement GraphSAINT-style sampling; at least one of `budget` or `ratio` is required.
- `layers.GraphConstruction(node_layers=None, edge_layers=None, edge_feature="residue_type")` applies node and edge modules to create a new packed graph; valid built-in `edge_feature` values are `"residue_type"`, `"gearnet"`, or `None`.
- `layers.SpatialLineGraph(num_angle_bin=8)` constructs a spatial line graph and discretizes angles into relation ids; it requires node positions on the graph.

## Selection Rules

- Use `GIN` over `RGCN` for ordinary molecular graphs unless relation ids in `edge_list[:, 2]` have semantic meaning beyond bond features.
- Use `edge_input_dim` only when `graph.edge_feature` exists and its final dimension equals the value passed to the layer/model.
- Use `num_relation` only with graphs whose `edge_list` has relation ids and whose `graph.num_relation` is set consistently.
- Use `concat_hidden=True` when downstream heads should see all layer outputs; then `model.output_dim` becomes the sum of hidden dimensions.
- Use `readout="mean"` for size-normalized graph features and `readout="sum"` when graph size should contribute to the representation.
- For protein GearNet pipelines, construct residue/edge geometry first with `GraphConstruction` and optionally pass line-graph angle bins through `SpatialLineGraph`; route full protein recipes to the protein workflow sub-skill.
