#!/usr/bin/env python3
"""Safe plugin entry skeleton adapted from the example plugin.

Replace the placeholder component import with the plugin's real component
module when packaging a custom SecretFlow plugin.
"""

# Import the component class so registration happens at import time.
# from .my_component.my_component import MyComponent


# Keep a reference here so static analyzers do not remove the import.
MyComponent = None


def main() -> None:
    """Plugin entry hook used by the example packaging flow."""
    pass


if __name__ == "__main__":
    main()
