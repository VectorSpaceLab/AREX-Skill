# Graphormer extension recipes

Use these recipes to add or diagnose Graphormer fairseq user-dir components without reopening source examples. They are safe design patterns only; they do not start training or download data.

## Extension checklist

1. Work inside a Graphormer-compatible user-dir package containing `models/`, `tasks/`, and `criterions/`.
2. Add new registration code in a non-private Python file: avoid filenames beginning with `_` or `.`.
3. Use unique registry names. fairseq rejects duplicate model, task, criterion, and architecture names.
4. Ensure every decorator executes during `--user-dir` import. For models and tasks, fairseq imports all non-private files under `models/` and `tasks/`; Graphormer imports criterions from the top-level package.
5. Use a fresh Python process for registry checks after edits.
6. Run `scripts/summarize_graphormer_registries.py --user-dir <graphormer-package-dir> --format text` and verify your new names appear.
7. Route data contracts to the dataset sub-skill and training schedules to the training sub-skill.

## Recipe: add a GraphMLP-like graph model

The GraphMLP pattern is the minimal documented extension style: a `FairseqEncoderModel` wraps an encoder, transforms node features, pools over nodes, and returns graph-level logits in a shape compatible with existing graph prediction criterions.

Create a file such as `graphormer/models/my_graph_model.py`:

```python
import torch
import torch.nn.functional as F
from fairseq.models import FairseqEncoder, FairseqEncoderModel, register_model, register_model_architecture
from graphormer.modules import GraphNodeFeature

@register_model("my_graph_model")
class MyGraphModel(FairseqEncoderModel):
    def __init__(self, args, encoder):
        super().__init__(encoder)
        self.args = args
        self.encoder_embed_dim = args.encoder_embed_dim

    @staticmethod
    def add_args(parser):
        parser.add_argument("--encoder-layers", type=int, metavar="N")
        parser.add_argument("--encoder-embed-dim", type=int, metavar="N")
        parser.add_argument("--max-nodes", type=int, metavar="N")

    @classmethod
    def build_model(cls, args, task):
        my_graph_model_architecture(args)
        return cls(args, MyGraphEncoder(args))

    def forward(self, batched_data, perturb=None, **kwargs):
        return self.encoder(batched_data, perturb=perturb, **kwargs)

class MyGraphEncoder(FairseqEncoder):
    def __init__(self, args):
        super().__init__(dictionary=None)
        self.max_nodes = args.max_nodes
        self.encoder_embed_dim = args.encoder_embed_dim
        self.num_classes = args.num_classes
        self.atom_encoder = GraphNodeFeature(
            num_heads=1,
            num_atoms=args.num_atoms,
            num_in_degree=args.num_in_degree,
            num_out_degree=args.num_out_degree,
            hidden_dim=args.encoder_embed_dim,
            n_layers=args.encoder_layers,
        )
        self.layers = torch.nn.ModuleList(
            [torch.nn.Linear(args.encoder_embed_dim, args.encoder_embed_dim) for _ in range(args.encoder_layers)]
        )
        self.graph_pred_linear = torch.nn.Linear(args.encoder_embed_dim, args.num_classes)

    def forward(self, batched_data, perturb=None, **unused):
        h = self.atom_encoder(batched_data)  # batch x (nodes + graph_token) x hidden
        if perturb is not None:
            h[:, 1:, :] = h[:, 1:, :] + perturb
        for layer in self.layers:
            h = F.relu(layer(h))
        graph_rep = h[:, 1:, :].sum(dim=1)  # simple node sum; choose pooling deliberately
        logits = self.graph_pred_linear(graph_rep)
        return logits.unsqueeze(1)  # batch x 1 x num_classes, so criterions can use logits[:, 0, :]

@register_model_architecture("my_graph_model", "my_graph_model")
def my_graph_model_architecture(args):
    args.encoder_layers = getattr(args, "encoder_layers", 5)
    args.encoder_embed_dim = getattr(args, "encoder_embed_dim", 256)
    args.max_nodes = getattr(args, "max_nodes", 512)
```

Key compatibility points:

- Set `self.encoder_embed_dim` on the model if it may be used with `graph_prediction_with_flag`.
- Accept `perturb=None` and add it only to real node positions, not to the graph token.
- Return `batch x 1 x num_classes` or another documented `batch x tokens x num_classes` tensor where `[:, 0, :]` is the graph-level output.
- Require `num_classes > 0`; the task default is a sentinel, not a usable output size.
- Use `GraphNodeFeature` only when input data has Graphormer-preprocessed `x`, `in_degree`, and `out_degree` fields.

## Recipe: add an architecture for existing `graphormer`

Create a non-private model file that imports the base model registration first, then registers a new architecture name:

```python
from fairseq.models import register_model_architecture
from graphormer.models.graphormer import base_architecture

@register_model_architecture("graphormer", "graphormer_tiny")
def graphormer_tiny_architecture(args):
    args.encoder_embed_dim = getattr(args, "encoder_embed_dim", 256)
    args.encoder_layers = getattr(args, "encoder_layers", 6)
    args.encoder_attention_heads = getattr(args, "encoder_attention_heads", 8)
    args.encoder_ffn_embed_dim = getattr(args, "encoder_ffn_embed_dim", 512)
    args.dropout = getattr(args, "dropout", 0.1)
    args.attention_dropout = getattr(args, "attention_dropout", 0.1)
    args.act_dropout = getattr(args, "act_dropout", 0.0)
    args.activation_fn = getattr(args, "activation_fn", "gelu")
    args.encoder_normalize_before = getattr(args, "encoder_normalize_before", True)
    args.apply_graphormer_init = getattr(args, "apply_graphormer_init", True)
    args.share_encoder_input_output_embed = getattr(args, "share_encoder_input_output_embed", False)
    args.no_token_positional_embeddings = getattr(args, "no_token_positional_embeddings", False)
    args.pre_layernorm = getattr(args, "pre_layernorm", False)
    base_architecture(args)
```

Use the architecture as `--arch graphormer_tiny` after the user-dir imports successfully. Keep model-level defaults separate from dataset/task defaults such as `num_classes`, `max_nodes`, and feature vocabulary sizes.

## Recipe: add a graph prediction criterion

A graph prediction criterion normally consumes graph-token logits and targets from the task:

```python
import torch
from fairseq import metrics
from fairseq.criterions import FairseqCriterion, register_criterion
from fairseq.dataclass.configs import FairseqDataclass

@register_criterion("my_graph_loss", dataclass=FairseqDataclass)
class MyGraphLoss(FairseqCriterion):
    def forward(self, model, sample, reduce=True):
        logits = model(**sample["net_input"])
        graph_logits = logits[:, 0, :]
        targets = model.get_targets(sample, [graph_logits])[: graph_logits.size(0)]
        loss = torch.nn.functional.mse_loss(graph_logits.float(), targets.float(), reduction="sum")
        sample_size = graph_logits.size(0)
        return loss, sample_size, {"loss": loss.detach(), "sample_size": sample_size}

    @staticmethod
    def reduce_metrics(logging_outputs):
        loss_sum = sum(log.get("loss", 0) for log in logging_outputs)
        sample_size = sum(log.get("sample_size", 0) for log in logging_outputs)
        metrics.log_scalar("loss", loss_sum / sample_size, sample_size, round=6)

    @staticmethod
    def logging_outputs_can_be_summed():
        return True
```

For a FLAG-compatible criterion, either read `sample["perturb"]` and call `model(..., perturb=perturb)`, or document that the criterion is not valid with `graph_prediction_with_flag`.

## Recipe: add a task

Use a task when the `sample` structure changes or when setup needs extra configuration. A graph prediction task should produce samples shaped like:

```python
{
    "nsamples": <batch-size-or-count>,
    "net_input": {"batched_data": <dict-with-graphormer-fields>},
    "target": <target-tensor>,
}
```

Register a task with a dataclass config:

```python
from dataclasses import dataclass, field
from fairseq.tasks import FairseqDataclass, FairseqTask, register_task

@dataclass
class MyTaskConfig(FairseqDataclass):
    num_classes: int = field(default=-1, metadata={"help": "number of outputs"})

@register_task("my_graph_task", dataclass=MyTaskConfig)
class MyGraphTask(FairseqTask):
    @classmethod
    def setup_task(cls, cfg, **kwargs):
        assert cfg.num_classes > 0, "Must set task.num_classes"
        return cls(cfg)

    def load_dataset(self, split, combine=False, **kwargs):
        raise NotImplementedError("Provide a NestedDictionaryDataset-compatible split")

    @property
    def source_dictionary(self):
        return None

    @property
    def target_dictionary(self):
        return None
```

If you only need a new dataset source for `graph_prediction`, route to dataset customization instead of creating a new task.

## Recipe: extend Graphormer3D safely

Graphormer3D uses a different input and output contract from graph-level property prediction. Keep these invariants unless also replacing `is2re` and `mae_deltapos`:

- Inputs: `atoms` and `tags` shaped `(batch, nodes)`, `pos` shaped `(batch, nodes, 3)`, and `real_mask` shaped `(batch, nodes)`.
- Output tuple: `(eng_output, node_output, node_target_mask)` where energy is per graph, node output is `(batch, nodes, 3)`, and node target mask is `(batch, nodes, 1)`.
- Architecture defaults live under the `graphormer3d_base` architecture name, not the graph-level `graphormer_base` names.
- The `mae_deltapos` criterion needs model update counts, energy target `relaxed_energy`, and node target `deltapos`.

## Registry verification workflow

After editing registration files, run the registry helper in a new process:

```bash
python scripts/summarize_graphormer_registries.py --user-dir <graphormer-package-dir> --format text
python scripts/summarize_graphormer_registries.py --user-dir <graphormer-package-dir> --format json --include-all
```

Use `--require-complete` when you want a nonzero exit if any built-in Graphormer registry names are missing. For a custom extension, inspect the full JSON and confirm your custom registry name appears in the expected registry class.
