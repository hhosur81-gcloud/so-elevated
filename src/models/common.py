"""Common base domain model with Tolerant Reader pattern (ENG-0001)."""

import json
from dataclasses import dataclass, field, fields, asdict
from typing import Any, Dict, Type, TypeVar

T = TypeVar("T", bound="EnterpriseBaseModel")


@dataclass
class EnterpriseBaseModel:
    """Base class for all enterprise domain models.
    
    Implements the Tolerant Reader pattern (ENG-0001):
    - Safely ingests raw dictionaries with extra/unknown fields from upstream APIs without throwing.
    - Preserves standard serialization (`to_dict()`, `to_json()`).
    """

    @classmethod
    def from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
        """Create a model instance from a dictionary, safely ignoring unmapped extra fields."""
        if not isinstance(data, dict):
            raise ValueError(f"Expected dictionary for {cls.__name__}, got {type(data).__name__}")

        valid_fields = {f.name for f in fields(cls)}
        filtered_kwargs = {}

        for k, v in data.items():
            if k in valid_fields:
                filtered_kwargs[k] = v

        return cls(**filtered_kwargs)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize model instance to a clean dictionary."""
        result = {}
        for f in fields(self):
            val = getattr(self, f.name)
            if hasattr(val, "to_dict"):
                result[f.name] = val.to_dict()
            elif hasattr(val, "value"):  # Handle Enums
                result[f.name] = val.value
            elif isinstance(val, list):
                result[f.name] = [
                    item.to_dict() if hasattr(item, "to_dict") else (item.value if hasattr(item, "value") else item)
                    for item in val
                ]
            else:
                result[f.name] = val
        return result

    def to_json(self, indent: int = 2) -> str:
        """Serialize model instance to JSON string."""
        return json.dumps(self.to_dict(), indent=indent, default=str)
