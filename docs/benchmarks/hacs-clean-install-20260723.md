# P4.1 evidence — real HACS UI clean install of v0.1.0-beta.1

Redacted, reproducible clean-install evidence for
[#10](https://github.com/geisten/geist-home-assistant/issues/10). All steps
were performed through the real Home Assistant / HACS web UI in a fresh,
disposable HA container; no credentials, tokens, private addresses,
utterances, or entity data appear below.

## Environment

| Component | Version |
|---|---|
| Home Assistant | 2026.7.3 (Container, `ghcr.io/home-assistant/home-assistant:stable`) |
| HACS | 2.0.5 |
| Geist Conversation | `v0.1.0-beta.1` (pre-release) |
| Host | macOS arm64, Docker 29.4.1 |
| Browser | Chromium-based embedded browser |
| Date | 2026-07-23 (UTC) |

## Procedure and results

1. **Fresh instance:** new HA container with empty `/config`, onboarding
   completed in the UI (local throwaway account, analytics off). HACS 2.0.5
   placed in `custom_components` before first start; GitHub device flow
   authorized by the operator. ~10 min including onboarding; two device-flow
   attempts failed earlier with a 20 s token timeout while the host slept —
   retry after wake succeeded.
2. **Custom repository:** HACS → Benutzerdefinierte Repositories →
   `https://github.com/geisten/geist-home-assistant`, Typ „Integration".
   Accepted and listed as „Geist Conversation" within seconds.
3. **Version listing:** HACS lists both published releases. ⚠️ Finding: the
   download dialog **defaults to `app-v0.1.0`** (the Phase-5 app-image
   release) because it is the newest non-prerelease; `v0.1.0-beta.1` (marked
   pre-release) must be selected explicitly under „Benötigst du eine andere
   Version?" → Release. Recorded as a release-policy input for
   [#13](https://github.com/geisten/geist-home-assistant/issues/13).
4. **Install:** `v0.1.0-beta.1` downloaded to
   `/config/custom_components/geist_conversation/`; on-disk manifest version
   `0.1.0-beta.1` verified. < 30 s.
5. **Restart:** HA restarted. Log shows only the generic
   „custom integration … not been tested" notice for `geist_conversation` —
   **no manifest, import, or translation errors**. Ready again in ~90 s.
6. **Devices & Services:** „geist Conversation" is discoverable via
   Integration hinzufügen; the config flow renders localized (DE):
   „Mit Geist verbinden", field „Unix-Socket-Pfad*", default
   `/config/geist.sock`.
7. **Health error path:** submitting without a running runtime yields the
   stable localized error **„Der Geist-Dienst ist nicht erreichbar."**
   (`cannot_connect`); no config entry is created, the form stays open for
   correction. No paths, tokens, or state beyond the user-entered default are
   displayed.

## Durations (active steps, excluding operator wait)

| Step | Duration |
|---|---|
| Onboarding + HACS setup (excl. failed sleep attempts) | ~10 min |
| Custom repo add + version select + install | ~2 min |
| Restart + log check | ~2 min |
| Config flow + error-path check | ~1 min |

## Conclusion

All P4.1 acceptance criteria are met through the real UI. The instance and
its Config-Entry-less state are kept as the N−1 baseline for the P4.2
upgrade test ([#12](https://github.com/geisten/geist-home-assistant/issues/12)).
