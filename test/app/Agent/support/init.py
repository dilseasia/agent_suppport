"""
Support Agent package initialization.
Exposes key classes, schemas, and constants for easy import.
"""

from .tool import SupportAgent
from .schema import SupportRequest, SupportResponse
from .prompt import SUPPORT_PROMPT

__all__ = [
    "SupportAgent",
    "SupportRequest",
    "SupportResponse",
    "SUPPORT_PROMPT",
]
