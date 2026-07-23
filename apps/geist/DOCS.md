# Geist Home Assistant app

This app runs the resident Geist runtime with its embedded model. It supports
`aarch64` and `amd64`, exposes no host port, requests no Supervisor, Home
Assistant, Docker, device, audio, video or host-namespace access, and mounts no
Home Assistant directory. `/data` is the only persistent location and holds
nothing but the ephemeral runtime socket.

The runtime binary is materialized at image-build time from the committed
`runtime.lock.json` — exact release tag, immutable asset URLs, SHA-256 checked
before extraction (see `docs/SUPPLY_CHAIN.md`). Published images are
cosign-signed with SBOM and provenance attestations.

## Requirements

Supported architectures are `aarch64` and `amd64`; the start preflight
refuses a mismatched host before the runtime loads. It also requires about
1.5 GiB of available RAM for the embedded model and a little free space on
`/data`, and stops with a single structured error (`status=insufficient_ram`
/ `status=insufficient_disk` / `status=arch_mismatch`) instead of
crash-looping. The thresholds can be tuned via the `GEIST_MIN_RAM_MB` and
`GEIST_MIN_DISK_MB` environment variables. The runtime is started exactly
once per container lifetime and keeps the model resident; requests never
trigger a reload.

## Transport

The runtime serves `dynamic-tools-v1` on `/data/geist.sock`. A socat bridge
forwards the container-internal TCP port `8099` to that socket. No host port
is mapped (`ports: {}`), so only containers on the private app network — Home
Assistant Core — can reach it. The app contains no HTTP/REST server, and it
must not mount `/config` to share the internal Unix socket.

## Connect the integration

In the `geist_conversation` config flow, enter the app's internal address
`<hostname>:8099`, where `<hostname>` is shown on the app's info page
(Settings → Add-ons → Geist). On Core/Container installations without the
app, keep using the absolute Unix-socket path of a host-resident daemon.

## Health, watchdog and recovery

Readiness and liveness are separate signals:

- **Readiness** is the model-free `dynamic-tools-v1` health frame. The
  container healthcheck sends it through the TCP bridge every 30 s (5 s
  timeout, 3 retries), so a dead bridge or a dead runtime both mark the app
  unhealthy; the integration polls the same frame every 30 s and raises one
  deduplicated Repair per instance, removed automatically on recovery.
- **Liveness** is the Supervisor watchdog (`tcp://[HOST]:8099`): if the
  bridge stops accepting, the Supervisor restarts the app. Its built-in
  restart throttling bounds the retry rate, so a permanently broken host
  cannot loop forever, and preflight failures stop deterministically with a
  single structured status line before the model loads.

Requests are never silently retried across a restart: an interrupted request
surfaces one correlated error in Home Assistant, mutating tool calls are not
replayed, and the zero-queue busy semantics resume unchanged with the fresh
process.

## Backup, upgrade and rollback

The app keeps **no persistent data pre-1.0**: `/data` holds only the
ephemeral runtime socket and is fully excluded from Home Assistant backups
(`backup_exclude: ["*"]`). Restoring a backup on a clean instance restores
the integration's Config Entry through Home Assistant itself; reinstalling
the app is all that is needed on the app side. Upgrades and rollbacks are
plain image swaps with no data migrations: the only state a previous
version can leave behind is a stale socket, which every start removes, and
a runtime that does not answer the exact `dynamic-tools-v1` ready frame
never becomes healthy.

## Compatibility

| App | Integration | Protocol | Engine release |
|---|---|---|---|
| 0.1.0 | ≥ 0.1.0-beta.1 | `dynamic-tools-v1` | geistlib `v0.4.0` (locked) |

The release policy and the full matrix are formalized in P4.3
([#13](https://github.com/geisten/geist-home-assistant/issues/13)).
