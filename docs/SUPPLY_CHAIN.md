# Supply-chain contract

P2.3.2 publishes an HA app only from immutable inputs. A release lock must be
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

The newest published Geist release is `v0.3.3`. It predates the resident
`dynamic-tools-v1` implementation and is therefore intentionally rejected as
an HA app input. P2.3.2 remains open until the engine repository publishes a
release from the dynamic-tools branch for both Linux architectures. No mutable
or incompatible fallback is permitted.
