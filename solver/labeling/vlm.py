"""Optional hosted/local VLM interface; no implementation or dependency is enabled yet."""

from typing import Protocol


class RoleLabeler(Protocol):
    def label(self, element_summary: dict[str, object]) -> str: ...
