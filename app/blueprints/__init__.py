from .core import main

# Register blueprint routes by importing modules for side effects
from . import helpers, marketplace, tradeflow  # noqa: F401

__all__ = ["main"]
