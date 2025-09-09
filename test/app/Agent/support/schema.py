from dataclasses import dataclass
from typing import Optional, Any

@dataclass
class SupportRequest:
    message: str

@dataclass
class SupportResponse:
    response: str
    tool_used: Optional[str] = None
    tool_output: Optional[Any] = None
    error_message: Optional[str] = None
