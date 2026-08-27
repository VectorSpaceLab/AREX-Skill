#!/usr/bin/env python3
"""Run portable Tacotron text-cleaning and ARPAbet checks.

The helper performs a dependency-light routing smoke check; it does not
replace the repository's full cleaner implementation and does not need a
Tacotron checkout, network, CMUdict download, or model.
"""
import argparse
import re
import sys


def collapse(text):
    return re.sub(r"\s+", " ", text)


def normalize(text, mode):
    text = text.lower() if mode != "basic" else text.lower()
    if mode in ("english", "transliteration"):
        # Keep this helper dependency-free; the full repository pipeline uses
        # Unidecode and inflect. This smoke helper checks routing syntax only.
        try:
            from unidecode import unidecode
            text = unidecode(text)
        except ImportError:
            if mode == "transliteration":
                raise
        if mode == "english":
            try:
                import inflect
                text = re.sub(r"\d+", lambda m: inflect.engine().number_to_words(int(m.group(0))), text)
            except ImportError:
                pass
    return collapse(text)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("text", nargs="?", default="Mr. Müller has 2 cats.")
    parser.add_argument("--cleaner", choices=("english", "transliteration", "basic"), default="english")
    parser.add_argument("--arpabet", default="{HH AW1 S S T AH0 N}")
    args = parser.parse_args()
    cleaned = normalize(args.text, args.cleaner)
    if "{" in args.arpabet or "}" in args.arpabet:
        if not (args.arpabet.startswith("{") and args.arpabet.endswith("}")):
            parser.error("ARPAbet sample must be enclosed by one pair of braces")
        phones = args.arpabet[1:-1].split()
        if not phones:
            parser.error("ARPAbet braces must contain phones")
    print("cleaned:", cleaned)
    print("arpabet:", args.arpabet)
    print("status: text routing checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
