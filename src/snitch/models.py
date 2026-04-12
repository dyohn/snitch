from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict


@dataclass
class SastResult:
    filename: str
    filepath: Path
    finding: Dict[str, Any]  # {"where", "what", "why", "fix"}
