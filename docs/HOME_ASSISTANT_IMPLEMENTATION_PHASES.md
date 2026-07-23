# Home Assistant implementation phases

This is the executable implementation index for the Geist Home Assistant
product. It contains only adapter, Home Assistant UX, distribution, and product
evidence work. Inference-engine work and the normative wire protocol belong to
[`geisten/geistlib`](https://github.com/geisten/geistlib).

## Product boundary

- Home Assistant derives request-scoped tools from Assist exposure.
- The integration revalidates every proposed call immediately before executing it.
- Geist receives no HA token and cannot call HA directly.
- Core/Container uses a permission-gated Unix socket.
- HA OS uses only a private app transport; there is no public REST/API endpoint.
- The sole runtime protocol is `dynamic-tools-v1`, pinned by `protocol/` fixtures.

## Agent handoff rules

Start with the first unfinished slice whose dependencies are complete. Keep one
PR to one numbered slice. Update status, verification commands, and evidence in
the same PR. Do not add migration adapters or compatibility transports. A slice
is complete only when its exit gate works from a clean checkout.

## HA Phase 0 — boundary and developer preview ✅

Delivered: custom Conversation integration, HA-owned exposure/policy/execution,
resident Unix-socket connection, guided Linux installation, rollback, health
handshake, and model-free contract tests.

Exit gate: a clean Core/Container installation can configure the integration
without YAML or HA credentials in the runtime and execute only exposed tools.

## HA Phase 1 — integration operability ✅

Delivered:

1. UI Config Flow, validated health handshake, reconfigure, DE/EN UI strings.
2. Polling health entity, Repairs recovery, redacted diagnostics.
3. Fresh-socket reconnect, zero-queue busy behavior, correlated cancellation.
4. HA-language metadata and bounded HA-owned conversation history.

Exit gate: configure, break, diagnose, repair, reconfigure, and unload through
the HA UI without inspecting daemon logs.

Phases 2 and 3 established the native beta and the host-neutral dynamic-tools
contract before the repository split. Their normative engine artifacts now live
in `geisten/geistlib`; this plan continues with HA-owned product work.

## Phase 4 — HACS integration distribution 🚧

Canonical tracking: [Phase 4 epic #11](https://github.com/geisten/geist-home-assistant/issues/11).

Delivered: root `hacs.json`, required manifest metadata, deterministic release
ZIP contract, HACS/Hassfest workflows, tag/version guard, and release workflow.

Delivered additionally: local HA 2026.3+ brand assets, validation without a
brands ignore, and package-equivalent clean install/replacement-upgrade checks
against a disposable HA Core container.

Published: `v0.1.0-beta.1` with a validated `geist_conversation.zip` asset.

Remaining executable slices:

1. [P4.1 real HACS UI clean install #10](https://github.com/geisten/geist-home-assistant/issues/10)
2. [P4.2 second beta and real N-1 to N upgrade #12](https://github.com/geisten/geist-home-assistant/issues/12)
3. [P4.3 compatibility matrix and release policy #13](https://github.com/geisten/geist-home-assistant/issues/13)

P4.3 can proceed in parallel. P4.2 starts only after P4.1 and must contain a
real reviewed integration change rather than an empty release. A
separate `home-assistant/brands` PR is no longer required for this custom
integration because HA 2026.3+ supports local `brand/` assets; move them to the
Brands repository only if the integration later targets HA Core.

Exit gate: clean-install and upgrade the custom integration through HACS from
published tags, retain the Config Entry, remove obsolete package files, and
publish redacted evidence for the tested compatibility matrix.

## Phase 5 — protected Home Assistant app 🚧 **NEXT**

Canonical tracking: [Phase 5 epic #2](https://github.com/geisten/geist-home-assistant/issues/2).

1. ✅ [P5.1 Runtime-Lock and verification #3](https://github.com/geisten/geist-home-assistant/issues/3)
   — delivered: committed lock on geistlib `v0.4.0`, fail-closed verify
   script, model-free negative fixtures, verified materialization in CI.
2. ✅ [P5.2 Signed multi-arch images #4](https://github.com/geisten/geist-home-assistant/issues/4)
   — delivered: `release-app.yml` published
   [app-v0.1.0](https://github.com/geisten/geist-home-assistant/releases/tag/app-v0.1.0)
   with signed per-arch digests, SBOM/provenance attestations, generic
   manifest, and pull-by-digest smokes on both architectures.
3. [P5.3 Private app transport and Config Flow #5](https://github.com/geisten/geist-home-assistant/issues/5)
   — implemented: fail-closed address parsing (Unix path or internal
   `host:port`), socat bridge on container port 8099 without a host port,
   healthcheck through the bridge, golden unix+tcp contract tests; HA-OS
   end-to-end evidence lands with P5.7.
4. [P5.4 Resource preflight and resident runtime lifecycle #6](https://github.com/geisten/geist-home-assistant/issues/6)
   — implemented: arch/RAM/disk preflight with structured fail-closed
   status lines and tunable thresholds, single resident runtime start,
   model-free negative fixtures; residency evidence under load lands
   with P5.7.
5. [P5.5 Watchdog, health, Repairs and recovery #7](https://github.com/geisten/geist-home-assistant/issues/7)
6. [P5.6 Upgrade, rollback and backup boundary #8](https://github.com/geisten/geist-home-assistant/issues/8)
7. [P5.7 HA OS E2E and 24-hour Pi 5 soak #9](https://github.com/geisten/geist-home-assistant/issues/9)

The protected `aarch64`/`amd64` scaffold, restrictive AppArmor, private runtime
boundary, healthcheck, and verified-input CI are already complete.

P5.1 requires a Geist release implementing `dynamic-tools-v1` for Linux
`aarch64` and `amd64`. This is satisfied by Geist `v0.4.0`
([geisten/geistlib#87](https://github.com/geisten/geistlib/issues/87),
release verification
[geisten/geistlib#117](https://github.com/geisten/geistlib/issues/117));
older releases predate the protocol and remain invalid inputs. See
[SUPPLY_CHAIN.md](SUPPLY_CHAIN.md).

Exit gate: add repository, install app, start it, add the integration, and run
the first correct request without SSH.

## Phase 6 — product evidence 🚧 pending

Publish at least 150 cases covering state/action, brightness/temperature,
areas, ambiguity, multiple calls, follow-ups, language variants, unexposed and
hallucinated entities, injection in names/state, high-impact actions, tool
failures, cancellation, and recovery.

Report tool/argument/final-action accuracy, denied-action rate, clarification
rate, latency, RSS, and reproducible energy where available by model, language,
and hardware. Require zero exposure-boundary violations and a 24-hour Pi 5 soak.

Exit gate: corpus, runner, raw results, security cases, and resource bounds are
published and reproducible.

## Phase 7 — public beta 🚧 pending

Prepare the HACS/App repository listing, compatibility and support policy,
privacy/security documentation, issue templates, release notes, and beta tester
path. Home Assistant Core inclusion is considered only after external beta
evidence and quality-scale requirements are stable.

Exit gate: a new user can discover, install, diagnose, update, and remove the
product using documented UI paths.
