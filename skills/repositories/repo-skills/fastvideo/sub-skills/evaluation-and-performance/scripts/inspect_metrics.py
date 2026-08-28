#!/usr/bin/env python3
"""List registered FastVideo metrics without downloading models or starting a server."""
def main() -> int:
    import argparse
    argparse.ArgumentParser(description=__doc__).parse_args()
    try:
        from fastvideo.eval.registry import list_metrics
    except ImportError as exc:
        print(f"evaluation registry unavailable: {exc}")
        return 2
    print("\n".join(list_metrics()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
