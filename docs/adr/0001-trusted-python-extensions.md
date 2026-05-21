# Trusted Python extensions

StockSensei extensions are trusted Python code loaded from global, project-local, configured, or package-discovered locations and run with the same permissions as the application. We chose this over manifest-based permissions or sandboxed subprocesses because Python sandboxing is unreliable and subprocess isolation would slow early extension API iteration; future isolation can be added once the extension surface stabilizes.

Extensions are discovered Pi-style from project-local, global, configured, and package-discovered locations. User configuration should migrate from `~/.stocksensei_config.json` to `~/.config/stocksensei/config.json` with backward-compatible reads from the legacy path.
