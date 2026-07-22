# Supply-chain contract

Phase 5 publishes an HA app only from immutable inputs. A release lock must be
committed before the publish workflow is enabled and must contain, per
architecture:

- an exact Geist release tag (never `latest`);
- the exact release-asset URL;
- the SHA-256 digest reported by GitHub and independently verified after download;
- the expected `geist --version` output;
- protocol `dynamic-tools-v1` verified by a model-free health handshake.

The app version, image tag, lock version, and generic multi-architecture
manifest tag must match. CI builds `aarch64` and `amd64`, attaches an SBOM and
provenance, signs images with GitHub OIDC/Cosign, then pulls each published
digest and runs the healthcheck through emulation or native runners.

## Current gate

The newest published Geist release is `v0.4.0`. It implements
`dynamic-tools-v1` for Linux `aarch64` and `x86_64` with published SHA-256
digests ([geisten/geistlib#87](https://github.com/geisten/geistlib/issues/87),
release verification
[geisten/geistlib#117](https://github.com/geisten/geistlib/issues/117)).
Releases `v0.3.3` and older predate the protocol and remain rejected as HA
app inputs. No mutable or incompatible fallback is permitted. P5.1 pins this
release in the runtime lock; HA work is tracked in
[Phase 5 epic #2](https://github.com/geisten/geist-home-assistant/issues/2).
