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

The container healthcheck sends the model-free health frame through the TCP
bridge, so a dead bridge or a dead runtime both mark the app unhealthy.
