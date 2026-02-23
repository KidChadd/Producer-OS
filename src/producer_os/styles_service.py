"""Style resolution and `.nfo` writing for Producer OS (v2).

This module encapsulates the logic for reading bucket and category
styles from a JSON file, resolving missing styles with sensible
fallbacks, and writing `.nfo` sidecar files to style folders in
FL Studio.

The style JSON is expected to have the following structure::

    {
      "categories": {
        "Samples": {"Color": "$123456", "IconIndex": 10, "SortGroup": 0},
        ...
      },
      "buckets": {
        "808s": {"Color": "$ff0000", "IconIndex": 12, "SortGroup": 1},
        ...
      }
    }

When resolving a style for a bucket the service attempts several
fallbacks in order:

1. Exact bucket match (case sensitive).
2. Case-insensitive bucket match (first match wins).
3. Category fallback (case insensitive).
4. A hard default neutral style when nothing matches.

Missing styles do not stop execution. A warning is printed once
per missing bucket/category but the system continues using the
default style.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Set


DEFAULT_STYLE: Dict[str, Any] = {
    "Color": "$7f7f7f",  # neutral grey
    "IconIndex": 0,
    "SortGroup": 0,
}


@dataclass
class StyleService:
    """Resolve bucket styles and write `.nfo` sidecar files."""

    styles: Dict[str, Dict[str, Dict[str, Any]]]

    # Bookkeeping for missing style warnings
    _reported_missing: Set[str] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        self._reported_missing = set()
        self.styles.setdefault("categories", {})
        self.styles.setdefault("buckets", {})

    def _lookup_bucket(self, bucket: str, case_insensitive: bool = True) -> Optional[Dict[str, Any]]:
        buckets = self.styles.get("buckets", {})
        if bucket in buckets:
            return buckets[bucket]
        if case_insensitive:
            lower = bucket.lower()
            for name, style in buckets.items():
                if name.lower() == lower:
                    return style
        return None

    def _lookup_category(self, category: str) -> Optional[Dict[str, Any]]:
        categories = self.styles.get("categories", {})
        if category in categories:
            return categories[category]
        lower = category.lower()
        for name, style in categories.items():
            if name.lower() == lower:
                return style
        return None

    def resolve_style(self, bucket: str, category: str) -> Dict[str, Any]:
        """Return a style dict given bucket and category, using fallbacks."""
        style = self._lookup_bucket(bucket, case_insensitive=False)
        if style is None:
            style = self._lookup_bucket(bucket, case_insensitive=True)
        if style is None:
            style = self._lookup_category(category)
        if style is None:
            key = f"{bucket}:{category}"
            if key not in self._reported_missing:
                print(f"Warning: No style defined for bucket '{bucket}' or category '{category}', using default.")
                self._reported_missing.add(key)
            style = DEFAULT_STYLE
        return style

    def pack_style_from_bucket(self, bucket_style: Dict[str, Any]) -> Dict[str, Any]:
        """Return the style for a pack by reusing bucket colour and icon."""
        return {
            "Color": bucket_style.get("Color", DEFAULT_STYLE["Color"]),
            "IconIndex": bucket_style.get("IconIndex", DEFAULT_STYLE["IconIndex"]),
            "SortGroup": bucket_style.get("SortGroup", DEFAULT_STYLE["SortGroup"]),
        }

    def _nfo_contents(self, style: Dict[str, Any]) -> str:
        """Return the textual contents of an `.nfo` file for the given style."""
        return (
            f"Color={style.get('Color', DEFAULT_STYLE['Color'])}\n"
            f"IconIndex={style.get('IconIndex', DEFAULT_STYLE['IconIndex'])}\n"
            f"HeightOfs=7\n"
            f"SortGroup={style.get('SortGroup', DEFAULT_STYLE['SortGroup'])}\n"
            "Tip=*Styled by Producer OS"
        )

    def write_nfo(self, folder_path: Path, name: str, style_dict: Dict[str, Any]) -> None:
        """Write .nfo file only if content differs (idempotent).

        FL Studio expects a plain-text .nfo in the format produced by `_nfo_contents()`.
        """
        nfo_path = Path(folder_path) / f"{name}.nfo"

        new_content = self._nfo_contents(style_dict)

        if nfo_path.exists():
            try:
                old_content = nfo_path.read_text(encoding="utf-8")
                if old_content.strip() == new_content.strip():
                    return  # no change; preserve mtime
            except Exception:
                # If reading fails, fall through and rewrite
                pass

        nfo_path.parent.mkdir(parents=True, exist_ok=True)
        nfo_path.write_text(new_content, encoding="utf-8")

    def compute_hash(self, style: Dict[str, Any]) -> str:
        """Compute a hash of style values for caching or comparison."""
        return hashlib.sha1(json.dumps(style, sort_keys=True).encode("utf-8")).hexdigest()
