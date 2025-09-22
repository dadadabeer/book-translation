"""
Book Translation Package

A Python package for translating books using SEA-LION AI models.
"""

__version__ = "1.0.0"
__author__ = "Book Translation Project"

from .client import get_client
from .formatter import format_book_output, format_translated_text

__all__ = [
    "get_client",
    "format_book_output",
    "format_translated_text"
]
