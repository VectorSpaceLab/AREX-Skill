"""Self-contained Office benchmark runtime for LibMTL."""

from .main import cli_main, main
from .create_dataset import office_dataloader

__all__ = ["cli_main", "main", "office_dataloader"]
