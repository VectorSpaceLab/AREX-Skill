# Lightning workflows

Use this reference when you want the same training recipe as the PyTorch examples, but wrapped in a `LightningModule` and `Trainer`.

## LightningModule pattern

A compact Lightly SSL module usually has four moving parts:

1. build the backbone and task head in `__init__`
2. define `forward` for one input view
3. unpack the views in `training_step` and compute the loss
4. return the optimizer in `configure_optimizers`

```python
class SimCLR(pl.LightningModule):
    def __init__(self):
        super().__init__()
        resnet = torchvision.models.resnet18(weights=None)
        self.backbone = nn.Sequential(*list(resnet.children())[:-1])
        self.projection_head = SimCLRProjectionHead(512, 2048, 2048)
        self.criterion = NTXentLoss()

    def forward(self, x):
        features = self.backbone(x).flatten(start_dim=1)
        return self.projection_head(features)

    def training_step(self, batch, batch_idx):
        views, _, _ = batch
        x0, x1 = views
        z0 = self.forward(x0)
        z1 = self.forward(x1)
        loss = self.criterion(z0, z1)
        self.log("train_loss", loss, prog_bar=True)
        return loss

    def configure_optimizers(self):
        return torch.optim.SGD(self.parameters(), lr=0.06)
```

Notes:
- Unpack the view container first. For multi-crop methods, the view list may contain more than two tensors.
- Keep `forward` focused on a single view so it is easy to reuse in evaluation or synthetic smoke checks.
- If you change the backbone output size, update the projection head input dimension before you debug anything else.

## Trainer and dataloader knobs

The most useful knobs for Lightly recipes are:

- `batch_size`: set per device for single-process training, or per rank in distributed training.
- `drop_last=True`: keep this on for contrastive and batch-norm-sensitive recipes.
- `num_workers`: scale it carefully; the effective worker count grows with the number of ranks.
- `accelerator`: use `"cpu"` for smoke tests and `"gpu"` when CUDA is available.
- `devices`: use `1` for one device or `"auto"` when you want portable code.
- `strategy`: use `"ddp"` for distributed training.
- `sync_batchnorm=True`: helpful for multi-GPU batch norm.
- `use_distributed_sampler=True`: the modern Lightning 2.x flag for distributed data loading.
- `default_root_dir` / `callbacks=[ModelCheckpoint(...)]`: configure where checkpoints go instead of relying on implicit paths.

Example trainer shape:

```python
trainer = pl.Trainer(
    max_epochs=10,
    accelerator="gpu" if torch.cuda.is_available() else "cpu",
    devices="auto",
    strategy="ddp" if torch.cuda.device_count() > 1 else "auto",
    sync_batchnorm=torch.cuda.device_count() > 1,
    use_distributed_sampler=torch.cuda.device_count() > 1,
)
```

## Adapting a CIFAR-style example

If a recipe starts from a download-ready dataset, keep the training structure and swap only the data source:

- replace the download dataset with a local image-folder dataset
- keep the same transform family
- keep the same loss and optimizer wiring
- keep the same `training_step` shape

A good migration path is:

1. verify the synthetic helper or a tiny local folder first
2. switch the dataset to the real image directory
3. add checkpointing
4. only then turn on GPU or DDP

## Checkpointing and version drift

Be careful with Lightning version changes:

- older examples may use `replace_sampler_ddp=True`
- newer Lightning uses `use_distributed_sampler=True`
- `devices="auto"` and `accelerator="gpu"` are the most portable defaults for modern code

If a checkpoint path does not appear where you expect, check the callback configuration, the root directory, and whether the process that writes the file is the rank-zero process.
