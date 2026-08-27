from __future__ import annotations

import argparse
from pathlib import Path

import torch
import torch.nn as nn
from LibMTL import Trainer
from LibMTL.config import LibMTL_args, prepare_args
from LibMTL.loss import CELoss
from LibMTL.metrics import AccMetric
from LibMTL.model import resnet18
from LibMTL.utils import set_device, set_random_seed

from .create_dataset import TASKS, office_dataloader


def _add_argument_once(parser, *names, **kwargs):
    existing = {opt for action in parser._actions for opt in action.option_strings}
    if not any(name in existing for name in names):
        parser.add_argument(*names, **kwargs)


def configure_parser(parser=None):
    if parser is None:
        parser = LibMTL_args
    _add_argument_once(parser, "--dataset", default="office-31", type=str, help="office-31, office-home")
    _add_argument_once(parser, "--bs", default=64, type=int, help="batch size")
    _add_argument_once(parser, "--epochs", default=100, type=int, help="training epochs")
    _add_argument_once(parser, "--dataset_path", default="/", type=str, help="dataset path")
    _add_argument_once(parser, "--office_num_workers", default=2, type=int, help="dataloader worker count")
    return parser


def parse_args(argv=None):
    parser = configure_parser(LibMTL_args)
    return parser.parse_args(argv)


def main(params):
    kwargs, optim_param, scheduler_param = prepare_args(params)

    if params.dataset not in TASKS:
        raise ValueError(f"No support dataset {params.dataset}")
    if not params.multi_input:
        raise ValueError("Office benchmark requires --multi_input")

    task_name = TASKS[params.dataset]
    class_num = 31 if params.dataset == "office-31" else 65

    task_dict = {
        task: {
            "metrics": ["Acc"],
            "metrics_fn": AccMetric(),
            "loss_fn": CELoss(),
            "weight": [1],
        }
        for task in task_name
    }

    data_loader, _ = office_dataloader(
        dataset=params.dataset,
        batchsize=params.bs,
        root_path=params.dataset_path,
        num_workers=getattr(params, "office_num_workers", 2),
    )
    train_dataloaders = {task: data_loader[task]["train"] for task in task_name}
    val_dataloaders = {task: data_loader[task]["val"] for task in task_name}
    test_dataloaders = {task: data_loader[task]["test"] for task in task_name}

    class Encoder(nn.Module):
        def __init__(self):
            super().__init__()
            hidden_dim = 512
            self.resnet_network = resnet18(pretrained=True)
            self.avgpool = nn.AdaptiveAvgPool2d((1, 1))
            self.hidden_layer = nn.Sequential(
                nn.Linear(512, hidden_dim),
                nn.BatchNorm1d(hidden_dim),
                nn.ReLU(),
                nn.Dropout(0.5),
            )
            self.hidden_layer[0].weight.data.normal_(0, 0.005)
            self.hidden_layer[0].bias.data.fill_(0.1)

        def forward(self, inputs):
            out = self.resnet_network(inputs)
            out = torch.flatten(self.avgpool(out), 1)
            return self.hidden_layer(out)

    decoders = nn.ModuleDict({task: nn.Linear(512, class_num) for task in task_name})

    officeModel = Trainer(
        task_dict=task_dict,
        weighting=params.weighting,
        architecture=params.arch,
        encoder_class=Encoder,
        decoders=decoders,
        rep_grad=params.rep_grad,
        multi_input=params.multi_input,
        optim_param=optim_param,
        scheduler_param=scheduler_param,
        save_path=params.save_path,
        load_path=params.load_path,
        **kwargs,
    )
    if params.mode == "train":
        officeModel.train(
            train_dataloaders=train_dataloaders,
            val_dataloaders=val_dataloaders,
            test_dataloaders=test_dataloaders,
            epochs=params.epochs,
        )
    elif params.mode == "test":
        officeModel.test(test_dataloaders)
    else:
        raise ValueError(f"No support mode {params.mode}")


def cli_main(argv=None):
    params = parse_args(argv)
    set_device(params.gpu_id)
    set_random_seed(params.seed)
    main(params)
    return 0


if __name__ == "__main__":
    raise SystemExit(cli_main())
