from __future__ import annotations

from importlib import resources
from pathlib import Path

import torch
import torchvision.transforms as transforms
from PIL import Image
from torch.utils.data import DataLoader, Dataset
from torch.utils.data import RandomSampler, SequentialSampler

TASKS = {
    "office-31": ["amazon", "dslr", "webcam"],
    "office-home": ["Art", "Clipart", "Product", "Real_World"],
}


def _split_root(dataset: str):
    if dataset not in TASKS:
        raise ValueError(f"unsupported office dataset: {dataset}")
    return resources.files(__package__).joinpath("data_txt", dataset)


class OfficeDataset(Dataset):
    def __init__(self, dataset: str, root_path: str | Path, task: str, mode: str):
        if dataset not in TASKS:
            raise ValueError(f"unsupported office dataset: {dataset}")
        if task not in TASKS[dataset]:
            raise ValueError(f"unsupported office task {task!r} for {dataset}")
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])
        split_file = _split_root(dataset).joinpath(f"{task}_{mode}.txt")
        with split_file.open("r", encoding="utf-8") as fh:
            self.img_list = [line.strip() for line in fh if line.strip()]
        self.root_path = Path(root_path)
        self.dataset = dataset
        self.task = task
        self.mode = mode

    def __getitem__(self, i):
        img_path, label = self.img_list[i].split(maxsplit=1)
        y = int(label)
        img = Image.open(self.root_path / img_path).convert("RGB")
        return self.transform(img), y

    def __len__(self):
        return len(self.img_list)


def office_dataloader(dataset: str, batchsize: int, root_path: str | Path, num_workers: int = 2):
    tasks = TASKS[dataset]
    data_loader = {}
    iter_data_loader = {}
    for task in tasks:
        data_loader[task] = {}
        iter_data_loader[task] = {}
        for mode in ["train", "val", "test"]:
            shuffle = mode == "train"
            drop_last = mode == "train"
            txt_dataset = OfficeDataset(dataset, root_path, task, mode)
            data_loader[task][mode] = DataLoader(
                txt_dataset,
                num_workers=num_workers,
                pin_memory=True,
                batch_size=batchsize,
                shuffle=shuffle,
                drop_last=drop_last,
            )
            iter_data_loader[task][mode] = iter(data_loader[task][mode])
    return data_loader, iter_data_loader
