# Home Assistant implementation phases

This is the executable implementation index for the Geist Home Assistant
product. It contains only adapter, Home Assistant UX, distribution, and product
evidence work. Inference-engine work and the normative wire protocol belong to
[`geisten/geisten`](https://github.com/geisten/geisten).

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

## HA Phase 2 — distribution 🚧 **NEXT**

### P2.1 — HACS-ready integration package

Delivered: root `hacs.json`, required manifest metadata, deterministic release
ZIP contract, HACS/Hassfest workflows, tag/version guard, and release workflow.

Pending: publish the first tag, verify HACS install/upgrade against a disposable
HA instance, add the integration to `home-assistant/brands`, then remove the
temporary `brands` validation ignore before requesting default HACS inclusion.

Exit gate: install and upgrade the custom integration through HACS from a tag.

### P2.2 — protected HA app

1. ✅ Protected-compatible `aarch64`/`amd64` scaffold, restrictive AppArmor,
   private runtime boundary, healthcheck, build-only CI.
2. **NEXT, gated:** immutable runtime inputs, published per-architecture images
   and generic manifest, checksums, Cosign signatures, provenance, SBOM, and
   pull-by-digest health smoke tests.
3. Pending: persistent model/cache lifecycle, watchdog, RAM/architecture checks,
   backup/restore, upgrade, and rollback tests.

P2.2 item 2 requires a Geist release implementing `dynamic-tools-v1` for Linux
`aarch64` and `amd64`. Geist `v0.3.3` predates the protocol and is not a valid
fallback. See [SUPPLY_CHAIN.md](SUPPLY_CHAIN.md) and GitHub issue #1.

Exit gate: add repository, install app, start it, add the integration, and run
the first correct request without SSH.

## HA Phase 3 — product evidence 🚧 pending

Publish at least 150 cases covering state/action, brightness/temperature,
areas, ambiguity, multiple calls, follow-ups, language variants, unexposed and
hallucinated entities, injection in names/state, high-impact actions, tool
failures, cancellation, and recovery.

Report tool/argument/final-action accuracy, denied-action rate, clarification
rate, latency, RSS, and reproducible energy where available by model, language,
and hardware. Require zero exposure-boundary violations and a 24-hour Pi 5 soak.

Exit gate: corpus, runner, raw results, security cases, and resource bounds are
published and reproducible.

## HA Phase 4 — public beta 🚧 pending

Prepare the HACS/App repository listing, compatibility and support policy,
privacy/security documentation, issue templates, release notes, and beta tester
path. Home Assistant Core inclusion is considered only after external beta
evidence and quality-scale requirements are stable.

Exit gate: a new user can discover, install, diagnose, update, and remove the
product using documented UI paths.
