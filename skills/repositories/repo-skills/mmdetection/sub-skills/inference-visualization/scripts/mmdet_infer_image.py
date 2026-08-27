#!/usr/bin/env python3
"""Safe image/folder inference helper for MMDetection 3.x public APIs."""

from __future__ import annotations

import argparse
import ast
from typing import Any

from mmdet.apis import DetInferencer
from mmdet.evaluation import get_classes


def _literal(value: str | None) -> Any:
    if value is None:
        return None
    try:
        return ast.literal_eval(value)
    except (ValueError, SyntaxError) as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Run MMDetection image, folder, or URL inference with DetInferencer.')
    parser.add_argument('inputs', help='Image path, image URL, or image folder.')
    parser.add_argument(
        'model',
        help='Model alias, config file, or .pth checkpoint with embedded config metadata.')
    parser.add_argument('--weights', default=None, help='Checkpoint path or URL.')
    parser.add_argument('--device', default=None, help='PyTorch device string, e.g. cpu or cuda:0.')
    parser.add_argument(
        '--out-dir',
        default='outputs',
        help='Directory for preds/ and vis/ outputs. Use empty string to disable file output.')
    parser.add_argument('--batch-size', type=int, default=1, help='Inference batch size.')
    parser.add_argument('--pred-score-thr', type=float, default=0.3, help='Score threshold for drawn predictions.')
    parser.add_argument(
        '--palette',
        default='none',
        choices=['none', 'coco', 'voc', 'citys', 'random'],
        help='Visualization palette priority override.')
    parser.add_argument('--show', action='store_true', help='Display visualization in a GUI window.')
    parser.add_argument('--return-vis', action='store_true', help='Return visualization arrays in memory.')
    parser.add_argument('--return-datasamples', action='store_true', help='Return DetDataSample objects instead of JSON dicts.')
    parser.add_argument('--print-result', action='store_true', help='Print inference result dictionary.')
    parser.add_argument('--no-save-vis', action='store_true', help='Do not save visualization images.')
    parser.add_argument(
        '--save-pred',
        action='store_true',
        help='Save JSON predictions under out-dir/preds/. DetInferencer defaults to not saving predictions.')
    parser.add_argument(
        '--texts',
        default=None,
        help='Open-vocabulary text prompt. Prefix with "$:" to expand dataset classes, e.g. "$: coco".')
    parser.add_argument('--stuff-texts', default=None, help='Open panoptic stuff text prompt.')
    parser.add_argument(
        '--custom-entities',
        action='store_true',
        help='Treat text prompts as explicit entity names for supported models.')
    parser.add_argument(
        '--tokens-positive',
        type=_literal,
        default=None,
        help='Grounding DINO token spans as a Python literal, or -1 when supported.')
    parser.add_argument(
        '--chunked-size',
        type=int,
        default=None,
        help='Set model.test_cfg.chunked_size for prompt-heavy open-vocabulary models.')
    return parser.parse_args()


def _expand_texts(texts: str | None) -> Any:
    if texts is None:
        return None
    if texts.startswith('$:'):
        dataset_name = texts[2:].strip()
        return [tuple(get_classes(dataset_name))]
    return texts


def main() -> None:
    args = _parse_args()

    model = args.model
    weights = args.weights
    if model.endswith('.pth') and weights is None:
        weights = model
        model = None

    inferencer = DetInferencer(
        model=model,
        weights=weights,
        device=args.device,
        palette=args.palette,
    )

    if args.chunked_size is not None:
        inferencer.model.test_cfg.chunked_size = args.chunked_size

    inferencer(
        inputs=args.inputs,
        batch_size=args.batch_size,
        return_vis=args.return_vis,
        show=args.show,
        no_save_vis=args.no_save_vis,
        pred_score_thr=args.pred_score_thr,
        return_datasamples=args.return_datasamples,
        print_result=args.print_result,
        no_save_pred=not args.save_pred,
        out_dir=args.out_dir,
        texts=_expand_texts(args.texts),
        stuff_texts=args.stuff_texts,
        custom_entities=args.custom_entities,
        tokens_positive=args.tokens_positive,
    )


if __name__ == '__main__':
    main()
