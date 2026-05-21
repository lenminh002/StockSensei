# Core extension architecture

StockSensei will move toward a packaged core where Terminal UI and Web UI share a `StockSensei Core` service, typed event stream, core session model, provider service, command registry, tool registry, and Visual Block schema registry. Extensions use a Pi-like activation API with declared ids and API versions, register through core registries, and can add tools and custom Visual Blocks first; broader lifecycle, prompt, command, UI, and renderer extension points remain reserved for later Web UI maturity.

Project-local, global, configured, and package-discovered extensions load by default, with project-local extensions requiring a first-use trust prompt. Built-in tools and built-in Visual Blocks register through the same core registries as extensions, while UI-specific native renderers stay owned by each interface.
