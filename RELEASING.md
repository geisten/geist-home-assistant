# Release policy and checklist

The canonical compatibility source is [`compatibility.json`](compatibility.json).
`make test` (via `tests/test_compatibility.py`) fails if `hacs.json`, the
manifest, the protocol fixture, `README.md`, the disposable-HA test, or the CI
matrix disagree with it. Update that file first; the tests then tell you every
derived surface that must follow.

## Versioning (pre-1.0)

- **Patch / beta suffix** (`0.1.0-beta.N` → `0.1.0-beta.N+1`): bug fixes and
  reviewed non-breaking changes. This is the default for the current phase.
- **Minor** (`0.MINOR.0`): additive, non-breaking feature sets.
- **Major** (`MAJOR.0.0`): reserved for the 1.0 stability commitment.
- A new runtime protocol id (not `dynamic-tools-v1`) is always a breaking
  change and requires a new fixture in `protocol/` and a matching engine
  release before either side ships.

## Breaking changes and rollback (pre-1.0)

- Config-entry data format may change between betas. The integration supports
  upgrading from the immediately previous release (N−1); older jumps are not
  guaranteed.
- No migration of legacy or REST-era configuration is provided or promised
  before 1.0. Incompatible pre-1.0 data may be rejected with a clear message.
- Rollback N → N−1 is supported only when no config-entry data format change
  occurred in N; otherwise the release notes state the expected limit.
- Every integration tag maps to exactly one runtime protocol id (see
  `compatibility.json` `integration.protocol`).

## Integration release checklist (`v*` tag)

Executable without conversation context.

1. Decide the version bump per the rules above; note breaking/non-breaking.
2. If HA support changed, edit `compatibility.json` (`homeassistant.minimum`
   and/or `homeassistant.tested`) first.
3. Set `custom_components/geist_conversation/manifest.json` `version` to the
   new value (without the leading `v`).
4. Update `tests/test_hacs_package.py` and any pinned version assertions.
5. Add a `CHANGELOG.md` entry summarizing reviewed changes.
6. Run `make test` and `tests/test_hacs_ha_container.sh`; both must pass.
7. Open the PR; require green `contract`, `hacs`, `hassfest`, and every
   `disposable-ha (<version>)` matrix leg.
8. Merge, then push the `v<version>` tag. The release workflow builds
   `geist_conversation.zip`, verifies the tag matches the manifest, and marks
   `-*` tags as prereleases.
9. Record the published ZIP SHA-256 (`gh release view <tag>`), and for a beta
   follow-up capture redacted HACS-UI upgrade evidence under `docs/benchmarks/`.
10. Confirm no diagnostics/logs added in the change expose utterances,
    entities, states, paths, or the socket address (redaction contract).

## App release checklist (`app-v*` tag)

Covered by the supply-chain contract:
[SUPPLY_CHAIN.md](docs/SUPPLY_CHAIN.md) (runtime lock, signed images,
SBOM/provenance, pull-by-digest smoke). App images publish with
`--latest=false` so HACS does not offer an app tag as the integration update.

## Matrix maintenance

At each release, either extend `homeassistant.tested` with the newly verified
stable HA version or leave the row unchanged. Never widen a supported claim
without a corresponding green `disposable-ha` leg — an untested combination
must not appear in `compatibility.json` or `README.md`.
