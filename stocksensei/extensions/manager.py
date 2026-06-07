from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from stocksensei.core.config import save_config
from stocksensei.extensions.api import ExtensionAPI, assert_api_compatible
from stocksensei.extensions.discovery import ExtensionSource, discover_sources, load_source
from utils import ask_text


@dataclass
class ExtensionRecord:
    id: str
    source: str
    scope: str
    version: str | None = None
    status: str = "loaded"
    error: str | None = None
    hooks: dict[str, list] = field(default_factory=dict)


class ExtensionManager:
    def __init__(self, *, config: dict, tool_registry: Any, block_registry: Any) -> None:
        self.config = config
        self.tool_registry = tool_registry
        self.block_registry = block_registry
        self.loaded: dict[str, ExtensionRecord] = {}
        self.failed: list[ExtensionRecord] = []
        self.disabled: dict[str, ExtensionRecord] = {}
        self._hooks: dict[str, list[tuple[str, Any]]] = {
            "on_startup": [],
            "before_agent_run": [],
            "after_agent_run": [],
            "on_shutdown": [],
        }

    def _project_trusted(self, source: ExtensionSource) -> bool:
        if source.scope != "project":
            return True
        root = str((Path.cwd() / ".stocksensei" / "extensions").resolve())
        trusted = self.config.setdefault("trusted_extension_projects", {})
        if trusted.get(root):
            return True
        answer = ask_text(
            f"Trust and load project-local StockSensei extensions from {root}? (y/N)",
            default="n",
        ).strip().lower()
        ok = answer in {"y", "yes"}
        trusted[root] = ok
        save_config(self.config)
        return bool(ok)

    def load_all(self) -> None:
        by_id: dict[str, tuple[ExtensionSource, Any, str, str | None]] = {}
        for source in discover_sources(self.config):
            if not self._project_trusted(source):
                self.disabled[source.display] = ExtensionRecord(source.display, source.display, source.scope, status="disabled", error="Project not trusted")
                continue
            try:
                module_or_factory = load_source(source)
                ext_id = getattr(module_or_factory, "EXTENSION_ID", None)
                api_version = getattr(module_or_factory, "API_VERSION", "0.1")
                version = getattr(module_or_factory, "VERSION", None)
                activate = getattr(module_or_factory, "activate", None)
                if activate is None and callable(module_or_factory):
                    activate = module_or_factory
                    ext_id = ext_id or getattr(module_or_factory, "id", None)
                if not ext_id:
                    raise ValueError("Extension must declare EXTENSION_ID")
                assert_api_compatible(api_version)
                if ext_id in by_id:
                    previous = by_id[ext_id][0]
                    if source.scope == "project" and previous.scope != "project":
                        by_id[ext_id] = (source, activate, api_version, version)
                    elif source.scope == previous.scope:
                        raise ValueError(f"Duplicate extension id in same scope: {ext_id}")
                    continue
                by_id[ext_id] = (source, activate, api_version, version)
            except Exception as exc:
                self.failed.append(ExtensionRecord(source.display, source.display, source.scope, status="failed", error=str(exc)))

        extension_config = self.config.setdefault("extensions", {})
        for ext_id, (source, activate, api_version, version) in by_id.items():
            if extension_config.get(ext_id, {}).get("enabled", True) is False:
                self.disabled[ext_id] = ExtensionRecord(ext_id, source.display, source.scope, version, status="disabled")
                continue
            try:
                api = ExtensionAPI(ext_id, api_version, self.tool_registry, self.block_registry)
                result = activate(api)
                if asyncio.iscoroutine(result):
                    asyncio.run(result)
                record = ExtensionRecord(ext_id, source.display, source.scope, version, hooks=api.hooks)
                self.loaded[ext_id] = record
                for hook_name, handlers in api.hooks.items():
                    for handler in handlers:
                        self._hooks[hook_name].append((ext_id, handler))
            except Exception as exc:
                self.failed.append(ExtensionRecord(ext_id, source.display, source.scope, version, status="failed", error=str(exc)))

    def run_hook_sync(self, hook_name: str, *args, **kwargs) -> list[Any]:
        return asyncio.run(self.run_hook(hook_name, *args, **kwargs))

    async def run_hook(self, hook_name: str, *args, **kwargs) -> list[Any]:
        results: list[Any] = []
        for ext_id, handler in list(self._hooks.get(hook_name, [])):
            if ext_id in self.disabled:
                continue
            try:
                result = handler(*args, **kwargs)
                if asyncio.iscoroutine(result):
                    result = await result
                results.append(result)
            except Exception as exc:
                record = self.loaded.pop(ext_id, ExtensionRecord(ext_id, ext_id, "unknown"))
                record.status = "failed"
                record.error = str(exc)
                self.failed.append(record)
                self.disabled[ext_id] = ExtensionRecord(ext_id, record.source, record.scope, record.version, status="disabled", error="Disabled after hook failure")
        return results

    def diagnostics(self) -> dict[str, list[dict[str, Any]]]:
        def dump(record: ExtensionRecord) -> dict[str, Any]:
            return {
                "id": record.id,
                "source": record.source,
                "scope": record.scope,
                "version": record.version,
                "status": record.status,
                "error": record.error,
            }
        return {
            "loaded": [dump(r) for r in self.loaded.values()],
            "disabled": [dump(r) for r in self.disabled.values()],
            "failed": [dump(r) for r in self.failed],
        }
