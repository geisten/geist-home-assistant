# Geist for Home Assistant

Private, local conversation agent for Home Assistant backed by the
[Geist inference engine](https://github.com/geisten/geisten).

This repository owns the Home Assistant product surface: the custom
integration, exposure and execution policy, diagnostics, installation tooling,
the protected Home Assistant app, tests, and release packaging. The inference
engine remains Home-Assistant-neutral.

## Status

This is pre-1.0 software. The dynamic-tools integration and Linux Unix-socket
developer path work; the protected HA app is currently a build-only scaffold.
See [the implementation phases](docs/HOME_ASSISTANT_IMPLEMENTATION_PHASES.md)
for the executable roadmap.
The complete documentation map is in [docs/README.md](docs/README.md).

## Repository layout

- `custom_components/geist_conversation`: Home Assistant integration
- `apps/geist`: protected Home Assistant app
- `scripts`: Linux install, setup, diagnostics, and soak tooling
- `tests`: model-free policy, protocol, packaging, and lifecycle contracts
- `protocol`: versioned compatibility fixtures for Geist's dynamic-tools API

Release images additionally follow the immutable-input rules in
[the supply-chain contract](docs/SUPPLY_CHAIN.md).

## Development

```sh
make test
```

For Home Assistant Core or Container on Linux, build or download `geist`
from Geist and follow [the beta guide](docs/HOME_ASSISTANT_BETA.md). The runtime
keeps the model resident and communicates through a permission-gated Unix
socket; no REST compatibility layer exists.

## Architecture boundary

Home Assistant decides which entities are exposed, validates every proposed
action again, executes services, and owns conversation history. Geist performs
local inference against request-scoped tools. The repositories depend only on
the versioned protocol contract and release artifacts—there is no submodule or
source-level dependency. See [ARCHITECTURE.md](docs/ARCHITECTURE.md).
