#!/usr/bin/env python3
"""Quick import and backend check for the EasyCV package."""

from importlib.util import find_spec

import torch

import easycv
from easycv.apis import export, single_gpu_test, train_model
from easycv.predictors import ClassificationPredictor, PoseTopDownPredictor, SegmentationPredictor, TorchYoloXPredictor
from easycv.utils.config_tools import CONFIG_TEMPLATE_ZOO

OPTIONAL_MODULES = [
    'easy_predict',
    'modelscope',
    'onnxruntime',
    'pycocotools',
    'xtcocotools',
    'shapely',
    'yacs',
    'prettytable',
]


def main() -> int:
    print(f'easycv={easycv.__version__}')
    print(f'torch={torch.__version__}')
    print(f'cuda_runtime={torch.version.cuda}')
    print(f'cuda_available={torch.cuda.is_available()}')
    print(f'cuda_device_count={torch.cuda.device_count() if torch.cuda.is_available() else 0}')
    print(f'config_templates={len(CONFIG_TEMPLATE_ZOO)}')
    print('apis=train_model,single_gpu_test,export')
    print('predictors=ClassificationPredictor,SegmentationPredictor,PoseTopDownPredictor,TorchYoloXPredictor')
    for name in OPTIONAL_MODULES:
        print(f'{name}={"present" if find_spec(name) else "missing"}')
    if torch.cuda.is_available():
        torch.empty(1, device='cuda')
        print('cuda_tiny_alloc=ok')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
