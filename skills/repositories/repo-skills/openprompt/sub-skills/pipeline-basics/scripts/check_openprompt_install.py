#!/usr/bin/env python3
"""No-download OpenPrompt install/API smoke for pipeline-basics."""

from __future__ import annotations

import importlib
import inspect
import os
import sys
import tempfile
import types

EXPECTED_SIGNATURES = {
    "PromptDataLoader": "(dataset: Union[torch.utils.data.dataset.Dataset, List], template: openprompt.prompt_base.Template, tokenizer_wrapper: Union[openprompt.plms.utils.TokenizerWrapper, NoneType] = None, tokenizer: transformers.tokenization_utils.PreTrainedTokenizer = None, tokenizer_wrapper_class=None, verbalizer: Union[openprompt.prompt_base.Verbalizer, NoneType] = None, max_seq_length: Union[str, NoneType] = 512, batch_size: Union[int, NoneType] = 1, shuffle: Union[bool, NoneType] = False, teacher_forcing: Union[bool, NoneType] = False, decoder_max_length: Union[int, NoneType] = -1, predict_eos_token: Union[bool, NoneType] = False, truncate_method: Union[str, NoneType] = 'tail', drop_last: Union[bool, NoneType] = False, **kwargs)",
    "PromptForClassification": "(plm: transformers.utils.dummy_pt_objects.PreTrainedModel, template: openprompt.prompt_base.Template, verbalizer: openprompt.prompt_base.Verbalizer, freeze_plm: bool = False, plm_eval_mode: bool = False)",
    "PromptForGeneration": "(plm: transformers.utils.dummy_pt_objects.PreTrainedModel, template: openprompt.prompt_base.Template, freeze_plm: bool = False, plm_eval_mode: bool = False, gen_config: Union[yacs.config.CfgNode, NoneType] = None, tokenizer: Union[transformers.tokenization_utils.PreTrainedTokenizer, NoneType] = None)",
    "load_plm": "(model_name, model_path, specials_to_add=None)",
    "InputExample": "(guid=None, text_a='', text_b='', label=None, meta: Union[Dict, NoneType] = None, tgt_text: Union[str, List[str], NoneType] = None)",
    "InputFeatures": "(input_ids: Union[List, torch.Tensor, NoneType] = None, inputs_embeds: Union[torch.Tensor, NoneType] = None, attention_mask: Union[List[int], torch.Tensor, NoneType] = None, token_type_ids: Union[List[int], torch.Tensor, NoneType] = None, label: Union[int, torch.Tensor, NoneType] = None, decoder_input_ids: Union[List, torch.Tensor, NoneType] = None, decoder_inputs_embeds: Union[torch.Tensor, NoneType] = None, soft_token_ids: Union[List, torch.Tensor, NoneType] = None, past_key_values: Union[torch.Tensor, NoneType] = None, loss_ids: Union[List, torch.Tensor, NoneType] = None, guid: Union[str, NoneType] = None, tgt_text: Union[str, NoneType] = None, use_cache: Union[bool, NoneType] = None, encoded_tgt_text: Union[str, NoneType] = None, input_ids_len: Union[int, NoneType] = None, **kwargs)",
}


def ensure_transformers_generation_utils() -> None:
    try:
        import transformers.generation_utils  # noqa: F401
        return
    except ModuleNotFoundError:
        try:
            generation_utils = importlib.import_module("transformers.generation.utils")
        except ModuleNotFoundError as exc:
            raise SystemExit(
                "OpenPrompt needs a transformers release that exposes GenerationMixin. "
                "Install the pinned inspection stack or add the compatibility shim."
            ) from exc
        shim = types.ModuleType("transformers.generation_utils")
        shim.__dict__.update(generation_utils.__dict__)
        sys.modules["transformers.generation_utils"] = shim


def assert_signature(name: str, obj, expected: str) -> None:
    actual = str(inspect.signature(obj))
    if actual != expected:
        raise AssertionError(f"{name} signature mismatch:\nexpected: {expected}\nactual:   {actual}")


def run_signature_smoke() -> None:
    import openprompt
    from openprompt import PromptDataLoader, PromptForClassification, PromptForGeneration
    from openprompt.data_utils import InputExample, InputFeatures
    from openprompt.plms import load_plm

    if getattr(openprompt, "__version__", None) != "1.0.1":
        raise AssertionError(f"Unexpected openprompt version: {getattr(openprompt, '__version__', None)}")

    assert_signature("PromptDataLoader", PromptDataLoader, EXPECTED_SIGNATURES["PromptDataLoader"])
    assert_signature("PromptForClassification", PromptForClassification, EXPECTED_SIGNATURES["PromptForClassification"])
    assert_signature("PromptForGeneration", PromptForGeneration, EXPECTED_SIGNATURES["PromptForGeneration"])
    assert_signature("load_plm", load_plm, EXPECTED_SIGNATURES["load_plm"])
    assert_signature("InputExample", InputExample, EXPECTED_SIGNATURES["InputExample"])
    assert_signature("InputFeatures", InputFeatures, EXPECTED_SIGNATURES["InputFeatures"])

    example = InputExample(guid="sig-demo", text_a="hello", label=1)
    features = InputFeatures(input_ids=[11, 12], attention_mask=[1, 1], token_type_ids=[0, 0], loss_ids=[0, 1], label=1, guid="sig-demo")
    if example.to_dict()["label"] != 1 or features["label"] != 1:
        raise AssertionError("Basic InputExample/InputFeatures construction failed")


class TinyTemplate:
    def wrap_one_example(self, example):
        return [
            [
                {"text": example.text_a, "loss_ids": 0, "shortenable_ids": 0},
                {"text": "<mask>", "loss_ids": 1, "shortenable_ids": 0},
            ],
            {"guid": example.guid, "label": example.label},
        ]


class TinyWrapper:
    def __init__(self, tokenizer, max_seq_length=8, truncate_method="tail", decoder_max_length=-1, predict_eos_token=False, **kwargs):
        self.tokenizer = tokenizer
        self.max_seq_length = max_seq_length
        self.truncate_method = truncate_method
        self.decoder_max_length = decoder_max_length
        self.predict_eos_token = predict_eos_token

    def tokenize_one_example(self, wrapped_example, teacher_forcing=False):
        return {
            "input_ids": [11, 12],
            "attention_mask": [1, 1],
            "token_type_ids": [0, 0],
            "loss_ids": [0, 1],
        }


def run_dataloader_smoke() -> None:
    from openprompt import PromptDataLoader
    from openprompt.data_utils import InputExample

    loader = PromptDataLoader(
        dataset=[InputExample(guid="demo-0", text_a="hello", label=1)],
        template=TinyTemplate(),
        tokenizer=object(),
        tokenizer_wrapper_class=TinyWrapper,
        max_seq_length=8,
        batch_size=1,
    )
    batch = next(iter(loader))
    if batch["label"].item() != 1:
        raise AssertionError(f"Unexpected label batch: {batch['label']}")
    if batch["loss_ids"].tolist() != [[0, 1]]:
        raise AssertionError(f"Unexpected loss_ids batch: {batch['loss_ids']}")


def main() -> None:
    # Prove the smoke is independent of the current working directory and the
    # original source checkout. The active environment must provide the
    # `openprompt` package through a normal install or editable install.
    with tempfile.TemporaryDirectory(prefix="openprompt-pipeline-basics-") as tmpdir:
        os.chdir(tmpdir)
        ensure_transformers_generation_utils()
        run_signature_smoke()
        run_dataloader_smoke()

    print("OpenPrompt pipeline-basics smoke passed")
    print("checks=import, signatures, fake-wrapper PromptDataLoader")


if __name__ == "__main__":
    main()
