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

## Runtime lock

`apps/geist/runtime.lock.json` pins the embedded-model runtime
(`geist-bitnet`) of Geist `v0.4.0`
([geisten/geistlib#87](https://github.com/geisten/geistlib/issues/87),
release verification
[geisten/geistlib#117](https://github.com/geisten/geistlib/issues/117)) for
both architectures. `scripts/verify-runtime-lock.sh ARCH` downloads the
locked asset, checks the SHA-256 before extraction, rejects traversal and
unexpected archive entries, and materializes `apps/geist/build/ARCH/geist`
for the image build, which performs no further network access for the
runtime. `--exec` compares `geist --version` against the lock; `--handshake`
requires the exact `dynamic-tools-v1` health frame. Releases `v0.3.3` and
older predate the protocol and remain rejected. Negative fixtures run in
`make test` (`tests/test_runtime_lock.py`) without any model download.

## App publishing

Pushing a tag `app-vX.Y.Z` runs `.github/workflows/release-app.yml`: a guard
job requires the tag to equal the `apps/geist/config.yaml` version and the
image to be `ghcr.io/geisten/geist-home-assistant-{arch}`. Each architecture
then re-runs the negative lock fixtures, materializes and verifies the locked
runtime (`--exec --handshake`), builds and pushes its image with BuildKit
provenance (`mode=max`) and SBOM attestations, smokes the image pulled by
digest until the container healthcheck passes, and cosign-signs the digest
keyless via GitHub OIDC. The generic multi-arch manifest and the GitHub
release (digest table plus verification commands) are published only after
both architecture smokes and signatures succeed. Verify any published digest
with:

```sh
cosign verify ghcr.io/geisten/geist-home-assistant@<digest> \
  --certificate-oidc-issuer https://token.actions.githubusercontent.com \
  --certificate-identity-regexp '^https://github.com/geisten/geist-home-assistant/'
```

## Lock update process

One PR per engine release, touching `apps/geist/runtime.lock.json` only:

1. Set `release` to the exact new tag and update both asset URLs to it.
2. Copy the digests from the release `SHA256SUMS`, then verify them
   independently: download both assets and compare `sha256`.
3. Set `version_output` to the exact `geist --version` line.
4. Run `make test` and `scripts/verify-runtime-lock.sh` for both
   architectures locally or let the app workflow do it.

Review checklist: tag is exact (`vX.Y.Z`, never `latest`); both URLs point
at that tag on `geisten/geistlib`; digests match the independently computed
values; `version_output` matches the binary; the app workflow (negative
fixtures, verify with `--exec --handshake`, image build) is green for both
architectures.
