# Geist for Home Assistant

Private, local conversation agent for Home Assistant backed by the
[Geist inference engine](https://github.com/geisten/geistlib).

This repository owns the Home Assistant product surface: the custom
integration, exposure and execution policy, diagnostics, installation tooling,
the protected Home Assistant app, tests, and release packaging. The inference
engine remains Home-Assistant-neutral.

## Status

This is pre-1.0 software. The dynamic-tools integration and Linux Unix-socket
developer path work; the protected HA app publishes signed multi-arch images
and connects over a private internal transport.
See [the implementation phases](docs/HOME_ASSISTANT_IMPLEMENTATION_PHASES.md)
for the executable roadmap.
The complete documentation map is in [docs/README.md](docs/README.md).

## Compatibility

`compatibility.json` is the canonical source; `README`, `hacs.json`, the
manifest, the protocol fixture, and CI are tested against it, so nothing here
can silently drift and no untested combination is claimed as supported.

| Item | Supported |
|---|---|
| Home Assistant (minimum) | 2026.6.0 |
| Home Assistant (tested in CI) | 2026.6.1, 2026.7.3 |
| Distribution | HACS custom repository, ZIP release |
| Runtime protocol | `dynamic-tools-v1` (required) |
| Integration `0.1.0-beta.3` | protocol `dynamic-tools-v1` |

Pre-1.0 policy: config-entry data may change between betas; the integration
supports the immediately previous release (N−1) for upgrades and does not
guarantee migration of legacy or REST-era configuration. Release rules and the
per-release checklist are in [RELEASING.md](RELEASING.md).

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

## Install through HACS

Until the repository is listed by default, add
`https://github.com/geisten/geist-home-assistant` as a custom HACS integration
repository. Install **Geist Conversation**, restart Home Assistant, then add it
under Settings → Devices & services. Tagged releases contain the validated
`geist_conversation.zip`; the default branch is intentionally not offered as
an installable version.

| Integration | Minimum Home Assistant | Runtime protocol | Status |
| :-- | :-- | :-- | :-- |
| [`v0.1.0-beta.1`](https://github.com/geisten/geist-home-assistant/releases/tag/v0.1.0-beta.1) | 2026.6.0 | `dynamic-tools-v1` | first HACS beta |

The automated clean-install and replacement-upgrade check runs against a
disposable Home Assistant 2026.6.1 container. The authenticated HACS UI smoke
and remaining Phase-4 gates are tracked in
[epic #11](https://github.com/geisten/geist-home-assistant/issues/11).

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
