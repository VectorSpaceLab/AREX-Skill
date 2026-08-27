#!/usr/bin/env python3
"""Find unique characters or phonemes in datasets from a Coqui TTS config."""

from __future__ import annotations

import argparse
import json
import os
import shutil
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence, Tuple


def _get(obj: Any, key: str, default: Any = None) -> Any:
    if isinstance(obj, dict):
        return obj.get(key, default)
    try:
        return obj[key]
    except Exception:
        return getattr(obj, key, default)


def _load_config(path: str) -> Any:
    from TTS.config import load_config

    return load_config(path)


def _load_items(config: Any, eval_split: bool) -> List[Dict[str, Any]]:
    from TTS.tts.datasets import load_tts_samples

    train, eval_items = load_tts_samples(
        _get(config, "datasets"),
        eval_split=eval_split,
        eval_split_max_size=_get(config, "eval_split_max_size"),
        eval_split_size=_get(config, "eval_split_size", 0.01),
    )
    return list(train) + ([] if eval_items is None else list(eval_items))


def _text_from_item(item: Any) -> str:
    if isinstance(item, dict):
        return str(item.get("text") or "").strip()
    if isinstance(item, (list, tuple)) and item:
        return str(item[0]).strip()
    return ""


def _language_from_items(items: Sequence[Dict[str, Any]]) -> str | None:
    languages = [str(item.get("language") or "").strip() for item in items if isinstance(item, dict)]
    languages = [lang for lang in languages if lang]
    if not languages:
        return None
    unique = sorted(set(languages))
    if len(unique) > 1:
        raise ValueError(
            "Phoneme inventory currently expects one language per run. "
            f"Found languages: {', '.join(unique)}. Split the config per language or use per-language runs."
        )
    return unique[0]


def _choose_phonemizer(config: Any, items: Sequence[Dict[str, Any]]) -> Tuple[Any, str, str]:
    from TTS.tts.utils.text.phonemizers import DEF_LANG_TO_PHONEMIZER, get_phonemizer_by_name

    language = _get(config, "phoneme_language") or _language_from_items(items)
    if not language:
        raise ValueError("Phoneme mode requires config.phoneme_language or dataset language to be set.")

    phonemizer_name = _get(config, "phonemizer")
    if phonemizer_name == "multi_phonemizer":
        raise ValueError("multi_phonemizer configs should be split into one language per unique-symbol run.")
    if not phonemizer_name:
        try:
            phonemizer_name = DEF_LANG_TO_PHONEMIZER[language]
        except KeyError as exc:
            raise ValueError(
                f"No default phonemizer is registered for language '{language}'. "
                "Set config.phonemizer explicitly or use character mode."
            ) from exc

    if phonemizer_name == "espeak" and not (shutil.which("espeak-ng") or shutil.which("espeak")):
        raise RuntimeError(
            "Phonemizer 'espeak' requires system executable espeak-ng or espeak. "
            "Install one of them, choose a different phonemizer, or run --mode chars."
        )

    try:
        phonemizer = get_phonemizer_by_name(phonemizer_name, language=language)
    except Exception as exc:
        raise RuntimeError(
            f"Could not initialize phonemizer '{phonemizer_name}' for language '{language}': {exc}. "
            "Check optional phonemizer dependencies such as gruut/espeak/espeak-ng."
        ) from exc
    return phonemizer, str(phonemizer_name), str(language)


def _summarize(symbols: Iterable[str]) -> Dict[str, Any]:
    counter = Counter(symbols)
    unique = sorted(counter.keys())
    lower_unique = sorted({s for s in unique if s.lower() == s})
    forced_lower = sorted({s.lower() for s in unique})
    return {
        "count": len(unique),
        "symbols": "".join(unique),
        "lower_symbols": "".join(lower_unique),
        "forced_lower_symbols": "".join(forced_lower),
        "frequencies": dict(sorted(counter.items(), key=lambda kv: (kv[0]))),
    }


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config-path", required=True, help="Path to a Coqui TTS config.")
    parser.add_argument("--mode", choices=["chars", "phonemes"], default="chars", help="Inventory raw characters or phonemized symbols.")
    parser.add_argument("--eval-split", action="store_true", help="Use Coqui eval splitting when loading samples. Default is no split to avoid tiny-data failures.")
    parser.add_argument("--no-eval-split", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--sample-limit", type=int, default=0, help="Limit number of loaded samples analyzed after loading; 0 means all.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text output.")
    args = parser.parse_args(list(argv) if argv is not None else None)

    config_path = Path(os.path.expanduser(args.config_path))
    if not config_path.is_file():
        print(f"Config file does not exist: {config_path}")
        return 2

    try:
        config = _load_config(str(config_path))
        eval_split = bool(args.eval_split and not args.no_eval_split)
        items = _load_items(config, eval_split=eval_split)
        if args.sample_limit and args.sample_limit > 0:
            items = items[: args.sample_limit]
        texts = [_text_from_item(item) for item in items]
        if args.mode == "chars":
            summary = _summarize(ch for text in texts for ch in text)
            metadata = {"mode": "chars", "num_items": len(items)}
        else:
            phonemizer, phonemizer_name, language = _choose_phonemizer(config, items)
            phones: List[str] = []
            for text in texts:
                phonemized = phonemizer.phonemize(text, separator="", language=language).replace("|", "")
                phones.extend(list(phonemized))
            summary = _summarize(phones)
            metadata = {"mode": "phonemes", "num_items": len(items), "phonemizer": phonemizer_name, "language": language}
    except Exception as exc:
        print(f"Unique-symbol scan failed: {type(exc).__name__}: {exc}")
        return 2

    result = {**metadata, **summary}
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
    else:
        print(f"Mode: {metadata['mode']}")
        print(f"Items analyzed: {metadata['num_items']}")
        if metadata["mode"] == "phonemes":
            print(f"Phonemizer: {metadata['phonemizer']} language={metadata['language']}")
        label = "phonemes" if metadata["mode"] == "phonemes" else "characters"
        print(f" > Number of unique {label}: {summary['count']}")
        print(f" > Unique {label}: {summary['symbols']}")
        print(f" > Unique lower {label}: {summary['lower_symbols']}")
        print(f" > Unique all forced to lower {label}: {summary['forced_lower_symbols']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
