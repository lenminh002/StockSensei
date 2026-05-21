---
status: code-map
path: stocksensei/extensions/discovery.py
language: python
updated: 2026-05-21
---

## Purpose
Discovers extension sources from global, project, configured path, and Python package entry-point locations.

## Functions / Sections
- `ExtensionScope` - allowed extension source scopes.
- `ExtensionSource` - dataclass describing an extension source.
- `ExtensionSource.display` - human-readable source identifier.
- `PROJECT_EXTENSIONS_DIR` - project-local extension directory.
- `GLOBAL_EXTENSIONS_DIR` - global extension directory.
- `ENTRY_POINT_GROUP` - Python entry point group name.
- `_iter_python_entries(directory)` - finds valid Python extension files or packages in a directory.
- `discover_sources(config)` - returns all configured extension sources.
- `load_source(source)` - imports or loads the selected extension source.

## Imports / Links
- [[config]] - supplies the global StockSensei config directory.
- external: importlib - loads Python files and entry points.
- external: os - expands configured extension paths.
- external: dataclasses - defines source metadata.
- external: pathlib - handles filesystem paths.
- external: typing - defines extension scope literals.
