#!/usr/bin/env python3
"""Safe Fengshen model-zoo import checker.

This script checks installed-package imports and compatibility symbols only. It
never calls from_pretrained, downloads models, runs training, compiles CUDA
extensions, or mutates checkpoints.
"""

from __future__ import annotations

import argparse
import contextlib
import importlib
import importlib.metadata as metadata
import io
import json
import os
import sys
import traceback
from dataclasses import dataclass, asdict
from typing import Iterable, Sequence


@dataclass
class CheckResult:
    name: str
    status: str
    required: bool
    detail: str = ""
    module: str | None = None
    attributes: list[str] | None = None


def _version(dist_name: str) -> str | None:
    try:
        return metadata.version(dist_name)
    except metadata.PackageNotFoundError:
        return None


def _import_quiet(module_name: str, verbose: bool = False):
    if verbose:
        return importlib.import_module(module_name)
    capture_out = io.StringIO()
    capture_err = io.StringIO()
    with contextlib.redirect_stdout(capture_out), contextlib.redirect_stderr(capture_err):
        return importlib.import_module(module_name)


def check_module(
    name: str,
    module_name: str,
    attrs: Sequence[str] = (),
    *,
    required: bool,
    verbose: bool = False,
    show_traceback: bool = False,
) -> CheckResult:
    try:
        module = _import_quiet(module_name, verbose=verbose)
        missing = [attr for attr in attrs if not hasattr(module, attr)]
        if missing:
            return CheckResult(
                name=name,
                status="fail",
                required=required,
                module=module_name,
                attributes=list(attrs),
                detail="missing attributes: " + ", ".join(missing),
            )
        return CheckResult(
            name=name,
            status="ok",
            required=required,
            module=module_name,
            attributes=list(attrs),
            detail="imported",
        )
    except Exception as exc:  # noqa: BLE001 - diagnostic script should report all import failures.
        detail = f"{type(exc).__name__}: {exc}"
        if show_traceback:
            detail = detail + "\n" + traceback.format_exc(limit=8)
        return CheckResult(
            name=name,
            status="fail",
            required=required,
            module=module_name,
            attributes=list(attrs),
            detail=detail,
        )


def check_symbol(
    name: str,
    module_name: str,
    attr: str,
    *,
    required: bool,
    verbose: bool = False,
    show_traceback: bool = False,
) -> CheckResult:
    return check_module(
        name,
        module_name,
        [attr],
        required=required,
        verbose=verbose,
        show_traceback=show_traceback,
    )


def build_checks(args: argparse.Namespace) -> list[CheckResult]:
    # Make accidental HF calls fail fast if a future import path ever adds a
    # config lookup. Current checks do not call from_pretrained.
    if not args.allow_online:
        os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
        os.environ.setdefault("HF_HUB_OFFLINE", "1")

    required_specs: list[tuple[str, str, tuple[str, ...]]] = [
        (
            "fengshen top-level exports",
            "fengshen",
            (
                "LongformerConfig",
                "LongformerModel",
                "RoFormerConfig",
                "RoFormerModel",
                "T5Config",
                "T5EncoderModel",
                "UbertPipelines",
                "UbertModel",
            ),
        ),
        (
            "longformer package",
            "fengshen.models.longformer",
            ("LongformerConfig", "LongformerTokenizer", "LongformerModel"),
        ),
        (
            "roformer package",
            "fengshen.models.roformer",
            ("RoFormerConfig", "RoFormerTokenizer", "RoFormerModel"),
        ),
        (
            "megatron-t5 package",
            "fengshen.models.megatron_t5",
            ("T5Config", "T5Tokenizer", "T5EncoderModel", "T5ForConditionalGeneration"),
        ),
        (
            "fengshen auto package",
            "fengshen.models.auto",
            ("AutoConfig", "AutoTokenizer", "AutoModel", "AutoModelForSequenceClassification"),
        ),
    ]

    optional_specs: list[tuple[str, str, tuple[str, ...]]] = [
        ("zen1 package", "fengshen.models.zen1", ("ZenConfig", "ZenModel", "ZenForSequenceClassification", "ZenNgramDict")),
        ("zen2 package", "fengshen.models.zen2", ("ZenConfig", "ZenModel", "ZenForQuestionAnswering", "ZenNgramDict")),
        ("deberta-v2 modeling", "fengshen.models.deberta_v2.modeling_deberta_v2", ("DebertaV2Model", "DebertaV2ForMaskedLM")),
        ("deltalm config", "fengshen.models.deltalm.configuration_deltalm", ("DeltalmConfig",)),
        ("deltalm modeling", "fengshen.models.deltalm.modeling_deltalm", ("DeltalmModel", "DeltalmForConditionalGeneration")),
        ("deltalm tokenizer", "fengshen.models.deltalm.tokenizer_deltalm", ("DeltalmTokenizer",)),
        ("llama config", "fengshen.models.llama.configuration_llama", ("LlamaConfig",)),
        ("llama modeling", "fengshen.models.llama.modeling_llama", ("LlamaModel", "LlamaForCausalLM")),
        ("taiyi clip package", "fengshen.models.clip", ("TaiyiCLIPModel", "TaiyiCLIPProcessor", "TaiyiCLIPEmbedder")),
        ("transfo-xl denoise config", "fengshen.models.transfo_xl_denoise.configuration_transfo_xl_denoise", ("TransfoXLDenoiseConfig",)),
        ("transfo-xl denoise modeling", "fengshen.models.transfo_xl_denoise.modeling_transfo_xl_denoise", ("TransfoXLDenoiseModel",)),
        ("transfo-xl denoise tokenizer", "fengshen.models.transfo_xl_denoise.tokenization_transfo_xl_denoise", ("TransfoXLDenoiseTokenizer",)),
        ("transfo-xl paraphrase helper", "fengshen.models.transfo_xl_paraphrase", ("paraphrase_generate",)),
        ("transfo-xl reasoning helper", "fengshen.models.transfo_xl_reasoning", ("deduction_generate", "abduction_generate")),
        ("bart modeling", "fengshen.models.bart.modeling_bart", ("BartForTextInfill", "CBartLightning")),
        ("albert modeling", "fengshen.models.albert.modeling_albert", ("AlbertModel", "AlbertForMaskedLM")),
        ("unimc package", "fengshen.models.unimc", ("UniMCPipelines",)),
        ("uniex package", "fengshen.models.uniex", ("UniEXPipelines",)),
        ("tcbert modeling", "fengshen.models.tcbert.modeling_tcbert", ("TCBertModel", "TCBertPredict")),
        ("ubert package", "fengshen.models.ubert", ("UbertPipelines", "UbertModel", "UbertDataset")),
        ("deepvae config", "fengshen.models.deepVAE.configuration_della", ("DellaModelConfig",)),
        ("deepvae modeling", "fengshen.models.deepVAE.deep_vae", ("DeepVAE", "Della")),
        ("davae modeling", "fengshen.models.DAVAE.DAVAEModel", ("DAVAEModel", "EncDecAAE")),
        ("gavae modeling", "fengshen.models.GAVAE.GAVAEModel", ("GAVAEModel",)),
        ("ppvae modeling", "fengshen.models.PPVAE.pluginVAE", ("PPVAEModel", "PluginVAE")),
    ]

    results: list[CheckResult] = []
    for spec in required_specs:
        results.append(check_module(*spec, required=True, verbose=args.verbose, show_traceback=args.traceback))

    results.append(
        check_symbol(
            "transformers cached_path compatibility",
            "transformers",
            "cached_path",
            required=True,
            verbose=args.verbose,
            show_traceback=args.traceback,
        )
    )
    results.append(
        check_symbol(
            "transformers softmax_backward_data compatibility",
            "transformers.pytorch_utils",
            "softmax_backward_data",
            required=True,
            verbose=args.verbose,
            show_traceback=args.traceback,
        )
    )

    if not args.required_only:
        for spec in optional_specs:
            results.append(check_module(*spec, required=False, verbose=args.verbose, show_traceback=args.traceback))

    return results


def summarize(results: Iterable[CheckResult]) -> dict[str, object]:
    result_list = list(results)
    required_failures = [r for r in result_list if r.required and r.status != "ok"]
    optional_failures = [r for r in result_list if not r.required and r.status != "ok"]
    return {
        "python": sys.version.split()[0],
        "distributions": {
            "fengshen": _version("fengshen"),
            "transformers": _version("transformers"),
            "torch": _version("torch"),
            "sentencepiece": _version("sentencepiece"),
            "deepspeed": _version("deepspeed"),
        },
        "required_ok": not required_failures,
        "optional_ok": not optional_failures,
        "required_failures": len(required_failures),
        "optional_failures": len(optional_failures),
        "checks": [asdict(r) for r in result_list],
    }


def print_text(summary: dict[str, object]) -> None:
    print("Fengshen model-zoo import check")
    print(f"Python: {summary['python']}")
    print("Distributions:")
    for name, version in summary["distributions"].items():
        print(f"  {name}: {version or 'not installed'}")
    print(f"Required checks: {'OK' if summary['required_ok'] else 'FAILED'}")
    print(f"Optional checks: {'OK' if summary['optional_ok'] else 'some failed'}")
    print("")
    for item in summary["checks"]:
        mark = "OK" if item["status"] == "ok" else "FAIL"
        level = "required" if item["required"] else "optional"
        print(f"[{mark}] {level}: {item['name']}")
        if item.get("detail") and item["detail"] != "imported":
            detail = str(item["detail"]).replace("\n", "\n      ")
            print(f"      {detail}")


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check installed Fengshen model-zoo imports without downloads, training, CUDA builds, or checkpoint mutation."
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text.")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero when optional family imports fail.")
    parser.add_argument("--required-only", action="store_true", help="Skip optional family imports and check only core required surface.")
    parser.add_argument("--allow-online", action="store_true", help="Do not set Hugging Face offline environment variables. The script still does not call from_pretrained.")
    parser.add_argument("--verbose", action="store_true", help="Do not silence stdout/stderr produced during imports.")
    parser.add_argument("--traceback", action="store_true", help="Include short tracebacks in failure details.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    results = build_checks(args)
    summary = summarize(results)
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print_text(summary)

    if not summary["required_ok"]:
        return 2
    if args.strict and not summary["optional_ok"]:
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
