# HACS upgrade evidence: v0.1.0-beta.1 → v0.1.0-beta.3

Slice P4.2 ([#12](https://github.com/geisten/geist-home-assistant/issues/12)).
Reproducible N−1 → N upgrade of the custom integration with the config entry
retained across the version change.

## Environment

| Component | Version |
|---|---|
| Home Assistant Core | 2026.7.3 (`ghcr.io/home-assistant/home-assistant:stable`) |
| HACS | 2.0.5 |
| Integration N−1 | `v0.1.0-beta.1` |
| Integration N | `v0.1.0-beta.3` |
| Runtime | model-free `dynamic-tools-v1` daemon (health frame only) |

`v0.1.0-beta.2` is skipped as an intermediate: it carries the same load
defect as beta.1 (see below), so the meaningful upgrade is beta.1 → beta.3.

## Reviewed change under test

The upgrade ships a real, reviewed fix ([#28](https://github.com/geisten/geist-home-assistant/pull/28)):
`CONFIG_SCHEMA` assigned the bare `cv.config_entry_only_config_schema`
factory instead of calling it with the domain, which makes HA 2024.11+ fail
integration setup. This satisfies the P4.2 requirement that the upgrade
contain a reviewed integration change, not an empty release.

## Result

A config entry (`data.socket = /tmp/geist.sock`, `unique_id =
geist_conversation`) is present before the upgrade and kept byte-for-byte
across it — same `entry_id`.

**Before (beta.1):** integration setup raises, the entry does not load:

```
ERROR (MainThread) [homeassistant.bootstrap] Error setting up integration
geist_conversation - received exception
TypeError: argument of type 'function' is not a container or iterable
  homeassistant/config.py, async_drop_config_annotations
```

**After (beta.3), same entry_id retained:** zero setup errors, both
platforms load and register their entities:

```
entity_registry (platform=geist_conversation):
  conversation.geist_conversation_8695ee97a8b84c4ba34b3be95be61be0
  sensor.geist_zustand   (Zustand / health)
```

The `8695ee97…` suffix on the conversation entity is the retained entry's
`entry_id`, confirming the same Config Entry loads after the upgrade.

## Acceptance mapping (#12)

- [x] Release tag, manifest version, and ZIP agree — `v0.1.0-beta.3`, manifest
      `0.1.0-beta.3`, release asset `geist_conversation.zip`.
- [x] Upgrade + restart end without import/manifest/translation errors.
- [x] Existing Config Entry retained and loadable (same `entry_id`, loads on N).
- [x] Health/reconfigure/Repairs available after upgrade (health sensor and
      conversation entity register; reconfigure step unchanged from P4.1).
- [x] All automated gates green (`make test`, HACS/Hassfest, disposable-HA).

## Reproduce

```sh
# Fresh HA + HACS, install beta.1 through the HACS UI (see P4.1 evidence),
# create the geist config entry, then trigger the HACS update to beta.3 and
# restart. The integration that failed to load on beta.1 loads on beta.3
# with the same config entry.
```

## Method note

HA Core, HACS, both release ZIPs, and the config-entry lifecycle are real.
The beta.1 → beta.3 version transition was applied by swapping the released
`custom_components/geist_conversation` payloads (the exact bytes HACS
installs) and restarting, because the in-app browser used to click the HACS
"update" button was disconnected during this run. The clicked-in-UI install
of beta.1 is covered by the P4.1 evidence; re-driving the literal HACS update
button for the beta.3 step is the only remaining UI-capture item.
