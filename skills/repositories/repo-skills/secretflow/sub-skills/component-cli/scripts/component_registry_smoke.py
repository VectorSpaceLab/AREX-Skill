#!/usr/bin/env python3
"""Tiny SecretFlow component-registry smoke helper.

This helper imports the component registry and prints a small summary. It does
not load plugins or touch external services.
"""

from secretflow.component.core import get_comp_list_def


def main() -> int:
    comp_list = get_comp_list_def()
    print(f"component-version: {comp_list.version}")
    print(f"component-count: {len(comp_list.comps)}")
    for comp in comp_list.comps[:5]:
        print(f"{comp.domain}/{comp.name}:{comp.version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
