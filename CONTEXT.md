# StockSensei

StockSensei is a stock research assistant with a terminal CLI today and a planned browser interface over the same assistant capability.

## Language

**StockSensei Core**:
Shared assistant capability that coordinates model access, market-data tools, conversation state, and structured responses independent of any user interface.
_Avoid_: Backend, engine, agent when referring to the whole shared capability

**Terminal UI**:
The command-line interface that presents StockSensei through terminal prompts, commands, status feedback, and rich-rendered blocks.
_Avoid_: CLI when the distinction from command invocation matters

**Web UI**:
A browser interface for StockSensei that presents the same core assistant capability as the Terminal UI.
_Avoid_: Dashboard, replacement CLI

**Extension**:
A trusted, separately registered capability package that can add behavior to StockSensei Core and may later provide interface-specific affordances.
_Avoid_: Plugin when naming the canonical domain concept

**Extension Surface**:
The set of StockSensei capabilities that Extensions are allowed to add or alter.
_Avoid_: Hook list, plugin API when discussing product boundaries

**Visual Block**:
A structured response item that represents user-visible content independently of any interface renderer.
_Avoid_: Component, widget, rich output

**Fallback Rendering**:
Readable substitute presentation used when an interface cannot render a Visual Block natively.
_Avoid_: Error state, raw dump

## Relationships

- **Terminal UI** and **Web UI** both use **StockSensei Core**
- **Web UI** does not replace **Terminal UI**
- An **Extension** primarily extends **StockSensei Core**
- An **Extension** may later add interface-specific affordances for **Terminal UI** or **Web UI**
- **Fallback Rendering** presents a **Visual Block** when native rendering is unavailable
- **Extension Surface** initially covers tools and Visual Blocks, with broader lifecycle and interface extension capability planned for later
- **StockSensei Core** owns sessions, provider configuration, command semantics, tool registration, Visual Block schemas, and typed run events
- **Terminal UI** and **Web UI** own native rendering for Visual Blocks

## Example dialogue

> **Dev:** "Should the Web UI get separate stock logic from the Terminal UI?"
> **Domain expert:** "No — both interfaces should use StockSensei Core so answers and visual outputs stay consistent."

## Flagged ambiguities

- "webui" was ambiguous between replacing the terminal app, mirroring it, or adding a second frontend — resolved: **Web UI** is a second frontend over **StockSensei Core**.
