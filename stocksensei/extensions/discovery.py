from __future__ import annotations

import importlib.util
import os
from dataclasses import dataclass
from importlib import metadata
from pathlib import Path
from typing import Literal

from stocksensei.core.config import CONFIG_DIR

ExtensionScope = Literal["project", "global", "configured", "entry_point"]


@dataclass(frozen=True)
class ExtensionSource:
    scope: ExtensionScope
    path: str | None = None
    entry_point: str | None = None
    module_name: str | None = None

    @property
    def display(self) -> str:
        return self.path or self.entry_point or self.module_name or self.scope


PROJECT_EXTENSIONS_DIR = Path.cwd() / ".stocksensei" / "extensions"
GLOBAL_EXTENSIONS_DIR = Path(CONFIG_DIR) / "extensions"
ENTRY_POINT_GROUP = "stocksensei.extensions"


def _iter_python_entries(directory: Path) -> list[Path]:
    if not directory.exists():
        return []
    entries: list[Path] = []
    for child in sorted(directory.iterdir()):
        if child.is_file() and child.suffix == ".py" and not child.name.startswith("_"):
            entries.append(child)
        elif child.is_dir() and (child / "__init__.py").exists():
            entries.append(child / "__init__.py")
        elif child.is_dir() and (child / "extension.py").exists():
            entries.append(child / "extension.py")
    return entries


def discover_sources(config: dict | None = None) -> list[ExtensionSource]:
    sources: list[ExtensionSource] = []
    for path in _iter_python_entries(GLOBAL_EXTENSIONS_DIR):
        sources.append(ExtensionSource(scope="global", path=str(path)))
    for path in _iter_python_entries(PROJECT_EXTENSIONS_DIR):
        sources.append(ExtensionSource(scope="project", path=str(path)))
    for raw in (config or {}).get("extension_paths", []):
        path = Path(os.path.expanduser(raw))
        if path.is_dir():
            for entry in _iter_python_entries(path):
                sources.append(ExtensionSource(scope="configured", path=str(entry)))
        elif path.exists():
            sources.append(ExtensionSource(scope="configured", path=str(path)))
    try:
        eps = metadata.entry_points(group=ENTRY_POINT_GROUP)
    except TypeError:
        eps = metadata.entry_points().get(ENTRY_POINT_GROUP, [])
    for ep in eps:
        sources.append(ExtensionSource(scope="entry_point", entry_point=ep.name))
    return sources


def load_source(source: ExtensionSource):
    if source.entry_point:
        for ep in metadata.entry_points(group=ENTRY_POINT_GROUP):
            if ep.name == source.entry_point:
                return ep.load()
        raise ImportError(f"Entry point not found: {source.entry_point}")
    if source.path:
        module_name = f"stocksensei_ext_{abs(hash(source.path))}"
        spec = importlib.util.spec_from_file_location(module_name, source.path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot load extension from {source.path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    if source.module_name:
        return __import__(source.module_name, fromlist=["*"])
    raise ImportError(f"Cannot load extension source: {source}")
