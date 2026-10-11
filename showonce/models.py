from dataclasses import dataclass, field
from typing import Any

@dataclass
class Step:
    id: str
    tool: str
    inputs: dict[str, Any] = field(default_factory=dict)
    expected_output: str = ""
    needs_approval: bool = False

@dataclass
class Workflow:
    steps: list[Step]
    contract: list[str]

