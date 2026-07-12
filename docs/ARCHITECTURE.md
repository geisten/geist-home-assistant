# Architecture

## Ownership boundary

`geisten/geisten` owns inference, model loading, the resident dynamic-tools
service, and the normative wire protocol. This repository owns all Home
Assistant behavior and distribution.

```text
Home Assistant Assist
  -> geist_conversation integration
       -> exposure snapshot + request-scoped tools
       -> Geist dynamic-tools-v1 runtime
       <- proposed tool calls / response
       -> policy revalidation
       -> Home Assistant service execution
```

The runtime receives no Home Assistant credential and cannot call Home
Assistant directly. The integration is the sole policy and execution boundary.
It rejects entities that are no longer exposed and never offers arbitrary
service-call tools.

## Repository coupling

The repositories are coupled through:

1. the `dynamic-tools-v1` protocol identifier and JSON framing;
2. golden request/response fixtures under `protocol/`;
3. immutable, checksum-verified Geist release artifacts used by the HA app.

They are not coupled by Git submodules, copied engine source, REST endpoints,
or a shared release cadence. A protocol change must first be additive or use a
new protocol identifier, update fixtures in both repositories, and pass the
contract suites before either consumer is released.

## Transport profiles

- HA Core/Container on Linux: a resident `geist-home` process and a mode-0600
  Unix socket in the HA config directory.
- HA OS/Supervised: a protected HA app with an internal-only transport. No host
  ports, HA credentials, Docker socket, host namespaces, or `/config` mount.
