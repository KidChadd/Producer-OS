from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

DEFAULT_FILE_TYPES: dict[str, bool] = {
    "wav": True,
    "mp3": False,
    "flac": False,
}


@dataclass(slots=True)
class WizardState:
    inbox_path: str = ""
    hub_path: str = ""
    action: str = "move"
    dry_run: bool = False
    preserve_vendor: bool = True
    file_types: dict[str, bool] = field(default_factory=lambda: dict(DEFAULT_FILE_TYPES))
    loop_safety: bool = True
    theme: str = "system"
    developer_tools: bool = False

    @classmethod
    def from_config(cls, config: dict[str, Any]) -> "WizardState":
        file_types = dict(DEFAULT_FILE_TYPES)
        loaded_types = config.get("file_types")
        if isinstance(loaded_types, dict):
            for key in DEFAULT_FILE_TYPES:
                value = loaded_types.get(key)
                if isinstance(value, bool):
                    file_types[key] = value
        return cls(
            inbox_path=str(config.get("inbox_path", "")),
            hub_path=str(config.get("hub_path", "")),
            action=str(config.get("action", "move")),
            dry_run=bool(config.get("dry_run", False)),
            preserve_vendor=bool(config.get("preserve_vendor", True)),
            file_types=file_types,
            loop_safety=bool(config.get("loop_safety", True)),
            theme=str(config.get("theme", "system")),
            developer_tools=bool(config.get("developer_tools", False)),
        )

    def to_config_updates(self) -> dict[str, Any]:
        return {
            "inbox_path": self.inbox_path,
            "hub_path": self.hub_path,
            "action": self.action,
            "dry_run": self.dry_run,
            "preserve_vendor": self.preserve_vendor,
            "file_types": dict(self.file_types),
            "loop_safety": self.loop_safety,
            "theme": self.theme,
            "developer_tools": self.developer_tools,
        }
