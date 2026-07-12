# Documentation index

This repository owns all Home Assistant product documentation:

- `ARCHITECTURE.md`: repository and security boundary
- `HOME_ASSISTANT_IMPLEMENTATION_PHASES.md`: canonical executable roadmap
- `proposals/home-assistant-phase-2.md`: detailed beta architecture and gates
- `HOME_ASSISTANT_BETA.md`: external tester path
- `SUPPLY_CHAIN.md`: immutable app-image inputs and publishing requirements
- `benchmarks/`: HA-specific Pi 5 and live-pipeline evidence

HACS packaging is defined by root `hacs.json`,
`.github/workflows/release-integration.yml`, the package contract, and the
disposable-HA install/upgrade test.

The Geist engine repository owns inference internals, build architecture,
generic deployment, performance benchmarks, and the normative
`dynamic-tools-v1` protocol. This repository keeps only compatibility fixtures
under `../protocol/`; it does not duplicate or redefine the engine contract.

Agents start with the first unfinished slice in
`HOME_ASSISTANT_IMPLEMENTATION_PHASES.md`, use the detailed proposal when the
slice points to it, and update status plus evidence in the same change.
Phase 4 is tracked by GitHub epic #11 and implementation issues #10, #12, #13.
Phase 5 is tracked by GitHub epic #2 and implementation issues #3 through #9.
